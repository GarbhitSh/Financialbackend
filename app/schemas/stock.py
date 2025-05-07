from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class StockBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    price: Optional[float] = None
    price_to_book: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    beta: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    avg_volume: Optional[int] = None

class StockCreate(StockBase):
    pass

class StockResponse(StockBase):
    id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True

class StockPriceBase(BaseModel):
    stock_id: int
    date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None

class StockPriceCreate(StockPriceBase):
    pass

class StockPriceResponse(StockPriceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StockList(BaseModel):
    stocks: List[StockResponse]
    total: int
