import asyncio
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.stock_sync_service import StockSyncService

logger = logging.getLogger(__name__)

class StockSyncTask:
    def __init__(self):
        self.db = SessionLocal()
        self.sync_service = StockSyncService(self.db)
        self.is_running = False

    async def sync_stocks(self):
        """
        Sync all stocks data
        """
        try:
            logger.info("Starting stock sync task")
            self.sync_service.sync_all_stocks()
            logger.info("Stock sync completed successfully")
        except Exception as e:
            logger.error(f"Error in stock sync task: {str(e)}")

    async def sync_historical_data(self):
        """
        Sync historical data for all stocks
        """
        try:
            logger.info("Starting historical data sync task")
            # Get data for the last 30 days
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            results = self.sync_service.sync_all_historical_data(
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"Historical data sync completed. Success: {len(results['success'])}, Failed: {len(results['failed'])}")
        except Exception as e:
            logger.error(f"Error in historical data sync task: {str(e)}")

    async def run_sync_tasks(self):
        """
        Run sync tasks periodically
        """
        while self.is_running:
            try:
                # Sync stock data every hour
                await self.sync_stocks()
                await asyncio.sleep(3600)  # 1 hour
                
                # Sync historical data every 4 hours
                await self.sync_historical_data()
                await asyncio.sleep(14400)  # 4 hours
            except Exception as e:
                logger.error(f"Error in sync tasks: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    def start(self):
        """
        Start the sync tasks
        """
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self.run_sync_tasks())
            logger.info("Stock sync tasks started")

    def stop(self):
        """
        Stop the sync tasks
        """
        self.is_running = False
        logger.info("Stock sync tasks stopped")

# Create a singleton instance
stock_sync_task = StockSyncTask()

def start_stock_sync():
    """
    Start the stock sync tasks
    """
    stock_sync_task.start()

def stop_stock_sync():
    """
    Stop the stock sync tasks
    """
    stock_sync_task.stop() 