import sys
import os
from pathlib import Path
from datetime import datetime

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.yfinance_service import YFinanceService
import logging
from app.models.stock import Stock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def populate_stocks():
    # List of popular stocks to add
    stocks = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corporation"},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
        {"symbol": "AMZN", "name": "Amazon.com Inc."},
        {"symbol": "META", "name": "Meta Platforms Inc."},
        {"symbol": "TSLA", "name": "Tesla Inc."},
        {"symbol": "NVDA", "name": "NVIDIA Corporation"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co."},
        {"symbol": "V", "name": "Visa Inc."},
        {"symbol": "WMT", "name": "Walmart Inc."},
        {"symbol": "JNJ", "name": "Johnson & Johnson"},
        {"symbol": "PG", "name": "Procter & Gamble Co."},
        {"symbol": "MA", "name": "Mastercard Inc."},
        {"symbol": "HD", "name": "Home Depot Inc."},
        {"symbol": "BAC", "name": "Bank of America Corp."},
        {"symbol": "XOM", "name": "Exxon Mobil Corporation"},
        {"symbol": "KO", "name": "Coca-Cola Co."},
        {"symbol": "PFE", "name": "Pfizer Inc."},
        {"symbol": "BA", "name": "Boeing Co."},
        {"symbol": "CAT", "name": "Caterpillar Inc."},
        {"symbol": "DIS", "name": "Walt Disney Co."}
    ]

    db = SessionLocal()
    yfinance_service = YFinanceService()

    try:
        for stock_data in stocks:
            try:
                logger.info(f"Fetching data for {stock_data['symbol']}...")
                
                # Create stock record
                stock = Stock(
                    symbol=stock_data['symbol'],
                    name=stock_data['name']
                )
                db.add(stock)
                db.commit()
                db.refresh(stock)

                # Fetch and update historical data
                historical_data = yfinance_service.get_historical_data(stock_data['symbol'])
                
                # Convert date strings to Python date objects
                for data_point in historical_data:
                    data_point['date'] = datetime.strptime(data_point['date'], '%Y-%m-%d').date()
                    data_point['stock_id'] = stock.id

                # Update stock data
                yfinance_service.update_stock_data(stock.id, historical_data)
                
                logger.info(f"Successfully added {stock_data['symbol']}")

            except Exception as e:
                logger.error(f"Error processing {stock_data['symbol']}: {str(e)}")
                db.rollback()
                continue

    except Exception as e:
        logger.error(f"Error in populate_stocks: {str(e)}")
        db.rollback()
    finally:
        db.close()

    logger.info("Stock data population completed!")

if __name__ == "__main__":
    populate_stocks() 