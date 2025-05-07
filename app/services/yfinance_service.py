import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from app.models.stock import Stock, StockPrice
from app.models.screen import Screen, ScreenCriteria

logger = logging.getLogger(__name__)

class YFinanceService:
    def __init__(self, db: Session):
        self.db = db

    def fetch_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch basic stock information from Yahoo Finance
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Get current price
            current_price = info.get("currentPrice", 0)
            if not current_price:
                current_price = info.get("regularMarketPrice", 0)
            
            return {
                "symbol": symbol,
                "company_name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "price": current_price,
                "price_to_book": info.get("priceToBook", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "eps": info.get("trailingEps", 0),
                "beta": info.get("beta", 0),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
                "avg_volume": info.get("averageVolume", 0)
            }
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            raise ValueError(f"Failed to fetch stock info for {symbol}: {str(e)}")

    def fetch_historical_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical price data from Yahoo Finance
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            stock = yf.Ticker(symbol)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No historical data found for {symbol}")
            
            return [
                {
                    "date": index.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                }
                for index, row in hist.iterrows()
            ]
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            raise ValueError(f"Failed to fetch historical data for {symbol}: {str(e)}")

    def update_stock_data(self, symbol: str) -> Stock:
        """
        Update stock information and historical data in the database
        """
        try:
            # Fetch stock info
            stock_info = self.fetch_stock_info(symbol)
            
            # Check if stock exists
            stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
            
            if not stock:
                # Create new stock
                stock = Stock(**stock_info)
                self.db.add(stock)
                self.db.commit()
                self.db.refresh(stock)
            else:
                # Update existing stock
                for key, value in stock_info.items():
                    setattr(stock, key, value)
                self.db.commit()
                self.db.refresh(stock)
            
            # Fetch and update historical data
            historical_data = self.fetch_historical_data(symbol)
            
            for data in historical_data:
                # Check if price data exists for this date
                price = self.db.query(StockPrice).filter(
                    StockPrice.stock_id == stock.id,
                    StockPrice.date == data["date"]
                ).first()
                
                if not price:
                    # Create new price entry
                    price = StockPrice(
                        stock_id=stock.id,
                        **data
                    )
                    self.db.add(price)
                else:
                    # Update existing price entry
                    for key, value in data.items():
                        setattr(price, key, value)
            
            self.db.commit()
            return stock
            
        except ValueError as e:
            logger.error(f"Validation error updating stock data for {symbol}: {str(e)}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error updating stock data for {symbol}: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Failed to update stock data for {symbol}: {str(e)}")

    def execute_screen(self, screen: Screen) -> List[Stock]:
        """
        Execute a screen using Yahoo Finance data
        """
        try:
            # Get all stocks
            stocks = self.db.query(Stock).all()
            matching_stocks = []
            
            for stock in stocks:
                # Fetch latest data
                stock_data = self.fetch_stock_info(stock.symbol)
                
                # Check each criterion
                matches = True
                for criterion in screen.criteria:
                    field = criterion.field
                    operator = criterion.operator
                    value = criterion.value
                    
                    if field not in stock_data:
                        matches = False
                        break
                    
                    stock_value = stock_data[field]
                    
                    if operator == "=":
                        if stock_value != value:
                            matches = False
                            break
                    elif operator == ">":
                        if stock_value <= value:
                            matches = False
                            break
                    elif operator == "<":
                        if stock_value >= value:
                            matches = False
                            break
                    elif operator == ">=":
                        if stock_value < value:
                            matches = False
                            break
                    elif operator == "<=":
                        if stock_value > value:
                            matches = False
                            break
                    elif operator == "!=":
                        if stock_value == value:
                            matches = False
                            break
                    elif operator == "between":
                        if not (value[0] <= stock_value <= value[1]):
                            matches = False
                            break
                    elif operator == "in":
                        if stock_value not in value:
                            matches = False
                            break
                
                if matches:
                    matching_stocks.append(stock)
            
            return matching_stocks
            
        except Exception as e:
            logger.error(f"Error executing screen {screen.id}: {str(e)}")
            raise ValueError(f"Failed to execute screen: {str(e)}") 