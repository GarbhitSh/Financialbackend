from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from sqlalchemy import text, and_, or_
import time

from app.database import get_db
from app.models.screen import Screen, ScreenCriteria
from app.models.stock import Stock
from app.schemas.screen import (
    ScreenCreate, ScreenResponse, ScreenUpdate, 
    ScreenList, ScreenResult
)
from app.utils.security import get_current_user
from app.models.user import User
from app.services.screen_service import ScreenService

router = APIRouter()

@router.post("/", response_model=ScreenResponse, status_code=status.HTTP_201_CREATED)
def create_screen(
    screen: ScreenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new screening criteria
    """
    # Check if screen name already exists for this user
    existing_screen = db.query(Screen).filter(
        Screen.name == screen.name,
        Screen.user_id == current_user.id
    ).first()
    
    if existing_screen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Screen with name '{screen.name}' already exists for this user"
        )
    
    # Create new screen
    db_screen = Screen(
        name=screen.name,
        description=screen.description,
        is_public=screen.is_public,
        user_id=current_user.id
    )
    
    db.add(db_screen)
    db.commit()
    db.refresh(db_screen)
    
    # Add criteria
    for criterion in screen.criteria:
        db_criterion = ScreenCriteria(
            screen_id=db_screen.id,
            field=criterion.field,
            operator=criterion.operator,
            value=criterion.value
        )
        db.add(db_criterion)
    
    db.commit()
    db.refresh(db_screen)
    
    return db_screen

@router.get("/", response_model=ScreenList)
def get_screens(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of screens for current user
    """
    # Query screens owned by current user or public screens
    query = db.query(Screen).filter(
        or_(
            Screen.user_id == current_user.id,
            Screen.is_public == True
        )
    )
    
    # Apply name filter if provided
    if name:
        query = query.filter(Screen.name.ilike(f"%{name}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    screens = query.offset(skip).limit(limit).all()
    
    return {"screens": screens, "total": total}

@router.get("/{screen_id}", response_model=ScreenResponse)
def get_screen(
    screen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get screen by ID
    """
    screen = db.query(Screen).filter(Screen.id == screen_id).first()
    
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screen with ID {screen_id} not found"
        )
    
    # Check if user has access to this screen
    if screen.user_id != current_user.id and not screen.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this screen"
        )
    
    return screen

@router.put("/{screen_id}", response_model=ScreenResponse)
def update_screen(
    screen_id: int,
    screen_update: ScreenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update screen
    """
    # Get screen
    db_screen = db.query(Screen).filter(Screen.id == screen_id).first()
    
    if not db_screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screen with ID {screen_id} not found"
        )
    
    # Check if user owns this screen
    if db_screen.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this screen"
        )
    
    # Update screen fields
    if screen_update.name is not None:
        # Check if new name already exists for this user
        if screen_update.name != db_screen.name:
            existing_screen = db.query(Screen).filter(
                Screen.name == screen_update.name,
                Screen.user_id == current_user.id,
                Screen.id != screen_id
            ).first()
            
            if existing_screen:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Screen with name '{screen_update.name}' already exists for this user"
                )
        
        db_screen.name = screen_update.name
    
    if screen_update.description is not None:
        db_screen.description = screen_update.description
    
    if screen_update.is_public is not None:
        db_screen.is_public = screen_update.is_public
    
    # Update criteria if provided
    if screen_update.criteria is not None:
        # Delete existing criteria
        db.query(ScreenCriteria).filter(ScreenCriteria.screen_id == screen_id).delete()
        
        # Add new criteria
        for criterion in screen_update.criteria:
            db_criterion = ScreenCriteria(
                screen_id=screen_id,
                field=criterion.field,
                operator=criterion.operator,
                value=criterion.value
            )
            db.add(db_criterion)
    
    db.commit()
    db.refresh(db_screen)
    
    return db_screen

@router.delete("/{screen_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_screen(
    screen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete screen
    """
    # Get screen
    db_screen = db.query(Screen).filter(Screen.id == screen_id).first()
    
    if not db_screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screen with ID {screen_id} not found"
        )
    
    # Check if user owns this screen
    if db_screen.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this screen"
        )
    
    # Delete screen (cascade will delete criteria)
    db.delete(db_screen)
    db.commit()
    
    return None

@router.post("/{screen_id}/run", response_model=ScreenResult)
def run_screen(
    screen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a screen and return matching stocks
    """
    # Start timer for execution time
    start_time = time.time()
    
    # Get screen
    screen = db.query(Screen).filter(Screen.id == screen_id).first()
    
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screen with ID {screen_id} not found"
        )
    
    # Check if user has access to this screen
    if screen.user_id != current_user.id and not screen.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this screen"
        )
    
    try:
        # Create screen service and run the screen
        screen_service = ScreenService(db)
        result = screen_service.run_screen(screen_id)
        
        # Add execution time to result
        result["execution_time"] = time.time() - start_time
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running screen: {str(e)}"
        )
