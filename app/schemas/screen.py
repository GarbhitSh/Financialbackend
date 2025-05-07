from pydantic import BaseModel, Field
from typing import Optional, List, Union, Any
from datetime import datetime

class ScreenCriteriaBase(BaseModel):
    field: str
    operator: str
    value: Union[float, int, str, List[Union[float, int, str]]]

class ScreenCriteriaCreate(ScreenCriteriaBase):
    pass

class ScreenCriteriaResponse(ScreenCriteriaBase):
    id: int
    screen_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ScreenBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    is_public: bool = False

class ScreenCreate(ScreenBase):
    criteria: List[ScreenCriteriaCreate]

class ScreenUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    criteria: Optional[List[ScreenCriteriaCreate]] = None

class ScreenResponse(ScreenBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    criteria: List[ScreenCriteriaResponse]
    
    class Config:
        from_attributes = True

class ScreenList(BaseModel):
    screens: List[ScreenResponse]
    total: int

class ScreenResult(BaseModel):
    screen_id: int
    screen_name: str
    results: List[Any]
    count: int
    execution_time: float
