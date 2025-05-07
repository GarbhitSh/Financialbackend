import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.stock import Stock, StockPrice
from app.services.yfinance_service import YFinanceService

logger = logging.getLogger(__name__)

class StockSyncService:
    def __init__(self, db: Session):
        self.db = db
        self.yf_service = YFinanceService(db)

    def sync_stock_data(self, symbol: str) -> Stock:
        """
        Sync stock data from Yahoo Finance
        """
        try:
            logger.info(f"Syncing data for stock: {symbol}")
            return self.yf_service.update_stock_data(symbol)
        except Exception as e:
            logger.error(f"Error syncing stock data for {symbol}: {str(e)}")
            raise

    def sync_multiple_stocks(self, symbols: List[str]) -> List[Stock]:
        """
        Sync multiple stocks data
        """
        synced_stocks = []
        for symbol in symbols:
            try:
                stock = self.sync_stock_data(symbol)
                synced_stocks.append(stock)
            except Exception as e:
                logger.error(f"Failed to sync {symbol}: {str(e)}")
                continue
        return synced_stocks

    def sync_all_stocks(self) -> List[Stock]:
        """
        Sync all stocks in the database
        """
        try:
            stocks = self.db.query(Stock).all()
            symbols = [stock.symbol for stock in stocks]
            return self.sync_multiple_stocks(symbols)
        except Exception as e:
            logger.error(f"Error syncing all stocks: {str(e)}")
            raise

    def sync_historical_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[StockPrice]:
        """
        Sync historical price data for a stock
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            # Get stock from database
            stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                raise ValueError(f"Stock {symbol} not found in database")

            # Fetch historical data
            historical_data = self.yf_service.fetch_historical_data(
                symbol,
                start_date=start_date,
                end_date=end_date
            )

            # Update database
            for data in historical_data:
                price = self.db.query(StockPrice).filter(
                    StockPrice.stock_id == stock.id,
                    StockPrice.date == data["date"]
                ).first()

                if not price:
                    price = StockPrice(
                        stock_id=stock.id,
                        **data
                    )
                    self.db.add(price)
                else:
                    for key, value in data.items():
                        setattr(price, key, value)

            self.db.commit()
            return historical_data

        except Exception as e:
            logger.error(f"Error syncing historical data for {symbol}: {str(e)}")
            self.db.rollback()
            raise

    def sync_all_historical_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        Sync historical data for all stocks
        """
        try:
            stocks = self.db.query(Stock).all()
            results = {
                "success": [],
                "failed": []
            }

            for stock in stocks:
                try:
                    self.sync_historical_data(
                        stock.symbol,
                        start_date=start_date,
                        end_date=end_date
                    )
                    results["success"].append(stock.symbol)
                except Exception as e:
                    logger.error(f"Failed to sync historical data for {stock.symbol}: {str(e)}")
                    results["failed"].append(stock.symbol)

            return results

        except Exception as e:
            logger.error(f"Error syncing all historical data: {str(e)}")
            raise

    def get_stock_status(self, symbol: str) -> dict:
        """
        Get sync status for a stock
        """
        try:
            stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return {
                    "exists": False,
                    "last_updated": None,
                    "has_historical_data": False
                }

            # Get latest price data
            latest_price = self.db.query(StockPrice)\
                .filter(StockPrice.stock_id == stock.id)\
                .order_by(StockPrice.date.desc())\
                .first()

            return {
                "exists": True,
                "last_updated": stock.updated_at,
                "has_historical_data": latest_price is not None,
                "latest_price_date": latest_price.date if latest_price else None
            }

        except Exception as e:
            logger.error(f"Error getting stock status for {symbol}: {str(e)}")
            raise 