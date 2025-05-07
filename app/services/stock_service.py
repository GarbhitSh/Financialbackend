from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.models.stock import Stock, StockPrice

class StockService:
    """
    Service for stock-related operations
    """
    
    @staticmethod
    def calculate_technical_indicators(
        stock_id: int,
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators for a stock
        """
        # Get stock
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            return {"error": f"Stock with ID {stock_id} not found"}
        
        # Get historical prices
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        prices = db.query(StockPrice).filter(
            StockPrice.stock_id == stock_id,
            StockPrice.date >= start_date,
            StockPrice.date <= end_date
        ).order_by(StockPrice.date).all()
        
        if not prices:
            return {"error": f"No price data found for stock ID {stock_id}"}
        
        # Convert to pandas DataFrame
        df = pd.DataFrame([{
            "date": p.date,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume
        } for p in prices])
        
        # Calculate indicators
        indicators = {}
        
        # Simple Moving Averages
        if len(df) >= 20:
            indicators["sma_20"] = df["close"].rolling(window=20).mean().iloc[-1]
        
        if len(df) >= 50:
            indicators["sma_50"] = df["close"].rolling(window=50).mean().iloc[-1]
        
        if len(df) >= 200:
            indicators["sma_200"] = df["close"].rolling(window=200).mean().iloc[-1]
        
        # Relative Strength Index (RSI)
        if len(df) >= 14:
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            indicators["rsi_14"] = 100 - (100 / (1 + rs.iloc[-1]))
        
        # MACD
        if len(df) >= 26:
            ema_12 = df["close"].ewm(span=12, adjust=False).mean()
            ema_26 = df["close"].ewm(span=26, adjust=False).mean()
            macd = ema_12 - ema_26
            signal = macd.ewm(span=9, adjust=False).mean()
            indicators["macd"] = macd.iloc[-1]
            indicators["macd_signal"] = signal.iloc[-1]
            indicators["macd_histogram"] = macd.iloc[-1] - signal.iloc[-1]
        
        # Bollinger Bands
        if len(df) >= 20:
            sma_20 = df["close"].rolling(window=20).mean()
            std_20 = df["close"].rolling(window=20).std()
            indicators["bollinger_upper"] = (sma_20 + (std_20 * 2)).iloc[-1]
            indicators["bollinger_middle"] = sma_20.iloc[-1]
            indicators["bollinger_lower"] = (sma_20 - (std_20 * 2)).iloc[-1]
        
        return {
            "stock_id": stock_id,
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "current_price": stock.price,
            "indicators": indicators
        }
    
    @staticmethod
    def get_stock_performance(
        stock_id: int,
        db: Session,
        period: str = "1y"
    ) -> Dict[str, Any]:
        """
        Calculate stock performance metrics
        """
        # Get stock
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            return {"error": f"Stock with ID {stock_id} not found"}
        
        # Determine date range based on period
        end_date = datetime.now().date()
        
        if period == "1m":
            start_date = end_date - timedelta(days=30)
        elif period == "3m":
            start_date = end_date - timedelta(days=90)
        elif period == "6m":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "3y":
            start_date = end_date - timedelta(days=3*365)
        elif period == "5y":
            start_date = end_date - timedelta(days=5*365)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        # Get historical prices
        prices = db.query(StockPrice).filter(
            StockPrice.stock_id == stock_id,
            StockPrice.date >= start_date,
            StockPrice.date <= end_date
        ).order_by(StockPrice.date).all()
        
        if not prices:
            return {"error": f"No price data found for stock ID {stock_id}"}
        
        # Calculate performance metrics
        start_price = prices[0].close
        end_price = prices[-1].close
        
        # Total return
        total_return = (end_price - start_price) / start_price * 100
        
        # Annualized return
        days = (prices[-1].date - prices[0].date).days
        if days > 0:
            annualized_return = ((1 + total_return/100) ** (365/days) - 1) * 100
        else:
            annualized_return = 0
        
        # Volatility (standard deviation of daily returns)
        df = pd.DataFrame([{"date": p.date, "close": p.close} for p in prices])
        df["daily_return"] = df["close"].pct_change()
        volatility = df["daily_return"].std() * (252 ** 0.5) * 100  # Annualized
        
        # Maximum drawdown
        df["cumulative_return"] = (1 + df["daily_return"]).cumprod()
        df["cumulative_max"] = df["cumulative_return"].cummax()
        df["drawdown"] = (df["cumulative_return"] / df["cumulative_max"] - 1) * 100
        max_drawdown = df["drawdown"].min()
        
        return {
            "stock_id": stock_id,
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "period": period,
            "start_date": prices[0].date,
            "end_date": prices[-1].date,
            "start_price": start_price,
            "end_price": end_price,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "max_drawdown": max_drawdown
        }
