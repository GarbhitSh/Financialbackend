from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func
import logging

from app.database import get_db
from app.models.stock import Stock, StockPrice
from app.schemas.stock import (
    StockCreate, StockResponse, StockList,
    StockPriceCreate, StockPriceResponse
)
from app.utils.security import get_current_user
from app.models.user import User
from app.services.yfinance_service import YFinanceService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(
    stock: StockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new stock and fetch data from Yahoo Finance
    """
    try:
        # Initialize YFinance service
        yf_service = YFinanceService(db)
        
        # Update stock data from Yahoo Finance
        db_stock = yf_service.update_stock_data(stock.symbol)
        
        return db_stock
    except ValueError as e:
        logger.error(f"Validation error creating stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating stock. Please try again later."
        )

@router.get("/", response_model=StockList)
def get_stocks(
    skip: int = 0,
    limit: int = 100,
    symbol: Optional[str] = None,
    sector: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of stocks with optional filtering
    """
    try:
        query = db.query(Stock)
        
        # Apply filters if provided
        if symbol:
            query = query.filter(Stock.symbol.ilike(f"%{symbol}%"))
        
        if sector:
            query = query.filter(Stock.sector == sector)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        stocks = query.offset(skip).limit(limit).all()
        
        return {"stocks": stocks, "total": total}
    except Exception as e:
        logger.error(f"Error getting stocks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving stocks. Please try again later."
        )

@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(
    stock_id: int,
    db: Session = Depends(get_db)
):
    """
    Get stock by ID and update data from Yahoo Finance
    """
    try:
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with ID {stock_id} not found"
            )
        
        # Update stock data from Yahoo Finance
        yf_service = YFinanceService(db)
        updated_stock = yf_service.update_stock_data(stock.symbol)
        
        return updated_stock
    except ValueError as e:
        logger.error(f"Validation error getting stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving stock data. Please try again later."
        )

@router.post("/prices", response_model=StockPriceResponse, status_code=status.HTTP_201_CREATED)
def create_stock_price(
    price: StockPriceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add historical price data for a stock (admin only)
    """
    # Check if stock exists
    stock = db.query(Stock).filter(Stock.id == price.stock_id).first()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with ID {price.stock_id} not found"
        )
    
    # Check if price data for this date already exists
    existing_price = db.query(StockPrice).filter(
        StockPrice.stock_id == price.stock_id,
        StockPrice.date == price.date
    ).first()
    
    if existing_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Price data for stock ID {price.stock_id} on {price.date} already exists"
        )
    
    # Create new price entry
    new_price = StockPrice(**price.model_dump())
    db.add(new_price)
    db.commit()
    db.refresh(new_price)
    
    return new_price

@router.get("/prices/{stock_id}", response_model=List[StockPriceResponse])
def get_stock_prices(
    stock_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get historical price data for a stock
    """
    try:
        # Check if stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with ID {stock_id} not found"
            )
        
        # Initialize YFinance service
        yf_service = YFinanceService(db)
        
        # Fetch historical data
        historical_data = yf_service.fetch_historical_data(
            stock.symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        # Update database with new data
        for data in historical_data:
            price = StockPrice(
                stock_id=stock_id,
                **data
            )
            db.add(price)
        
        db.commit()
        
        # Query updated price data
        query = db.query(StockPrice).filter(StockPrice.stock_id == stock_id)
        
        if start_date:
            query = query.filter(StockPrice.date >= start_date)
        
        if end_date:
            query = query.filter(StockPrice.date <= end_date)
        
        prices = query.order_by(StockPrice.date).all()
        
        return prices
    except ValueError as e:
        logger.error(f"Validation error getting stock prices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock prices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving stock prices. Please try again later."
        )

@router.get("/sectors", response_model=List[str])
def get_sectors(db: Session = Depends(get_db)):
    """
    Get list of all sectors
    """
    try:
        sectors = db.query(Stock.sector).distinct().filter(Stock.sector != None).all()
        return [sector[0] for sector in sectors if sector[0]]
    except Exception as e:
        logger.error(f"Error getting sectors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sectors. Please try again later."
        )

@router.get("/industries", response_model=List[str])
def get_industries(
    sector: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all industries, optionally filtered by sector
    """
    try:
        query = db.query(Stock.industry).distinct().filter(Stock.industry != None)
        
        if sector:
            query = query.filter(Stock.sector == sector)
        
        industries = query.all()
        return [industry[0] for industry in industries if industry[0]]
    except Exception as e:
        logger.error(f"Error getting industries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving industries. Please try again later."
        )

@router.post("/update/{symbol}", response_model=StockResponse)
def update_stock_data(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually update stock data from Yahoo Finance
    """
    try:
        yf_service = YFinanceService(db)
        updated_stock = yf_service.update_stock_data(symbol)
        return updated_stock
    except ValueError as e:
        logger.error(f"Validation error updating stock data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating stock data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating stock data. Please try again later."
        )

@router.get("/test/{symbol}", response_model=dict)
def test_stock_data(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to verify stock data structure
    """
    try:
        yf_service = YFinanceService(db)
        stock_info = yf_service.fetch_stock_info(symbol)
        historical_data = yf_service.fetch_historical_data(symbol, period="1mo")
        
        return {
            "stock_info": stock_info,
            "historical_data": historical_data[:5],  # Return first 5 days of data
            "message": "Data structure is valid and ready for frontend consumption"
        }
    except ValueError as e:
        logger.error(f"Validation error testing stock data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error testing stock data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing stock data. Please try again later."
        )
