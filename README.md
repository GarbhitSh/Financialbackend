# Financial Stock Screener

A powerful financial stock screening application that allows users to create custom screens based on various financial metrics and criteria. The application integrates with Yahoo Finance to provide real-time stock data and historical price information.

## Features

- 🔐 **User Authentication**: Secure user registration and login system
- 📊 **Stock Data**: Real-time stock information from Yahoo Finance
- 🔍 **Custom Screens**: Create and save custom stock screening criteria
- 📈 **Historical Data**: Access historical price data for stocks
- 👥 **Public/Private Screens**: Share your screens with other users or keep them private
- 📱 **RESTful API**: Well-documented API for easy integration\



![alt]("https://github.com/GarbhitSh/Financialbackend/blob/main/dia.png).


## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Authentication**: JWT
- **Stock Data**: Yahoo Finance API
- **Documentation**: OpenAPI/Swagger

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone https://github.com/garbhitsh/Financialbackend.git
cd financial-screener
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` file with your configuration.

5. Initialize the database:
```bash
python app/scripts/init_db.py
```

6. Populate initial stock data:
```bash
python app/scripts/populate_stocks.py
```

## Running the Application

1. Start the development server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Documentation

The API documentation is available in two formats:
- [API Documentation](API_DOCUMENTATION.md): Detailed API endpoint documentation
- [Architecture Documentation](ARCHITECTURE_DIAGRAM.md): System architecture and design

## Project Structure

```
financial-screener/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   └── base.py
│   ├── models/
│   │   ├── stock.py
│   │   ├── screen.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── stock.py
│   │   ├── screen.py
│   │   └── user.py
│   ├── services/
│   │   ├── stock_service.py
│   │   ├── screen_service.py
│   │   └── yfinance_service.py
│   └── scripts/
│       ├── init_db.py
│       └── populate_stocks.py
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Available Screen Criteria

The application supports screening based on the following metrics:

- Market Capitalization
- P/E Ratio
- Price
- Price to Book Ratio
- Dividend Yield
- EPS (Earnings per Share)
- Beta
- 52-Week High/Low
- Average Volume

## Example Usage

1. Register a new user:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword", "full_name": "John Doe"}'
```

2. Create a screen:
```bash
curl -X POST http://localhost:8000/api/v1/screens \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Value Stocks",
    "description": "Stocks with low P/E ratio and high dividend yield",
    "is_public": false,
    "criteria": [
      {
        "field": "pe_ratio",
        "operator": "<",
        "value": 15
      },
      {
        "field": "dividend_yield",
        "operator": ">",
        "value": 3.0
      }
    ]
  }'
```

3. Run a screen:
```bash
curl -X POST http://localhost:8000/api/v1/screens/1/run \
  -H "Authorization: Bearer <your_token>"
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## Testing

Run the test suite:
```bash
pytest
```

## Security

- All passwords are hashed using bcrypt
- JWT tokens are used for authentication
- Rate limiting is implemented to prevent abuse
- Input validation is performed on all endpoints
- SQL injection prevention through SQLAlchemy

## Performance

- Database queries are optimized with proper indexing
- Response caching for frequently accessed data
- Pagination for large datasets
- Efficient data serialization

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- Yahoo Finance for providing stock data
- FastAPI for the excellent web framework
- SQLAlchemy for the ORM
- All contributors who have helped with the project
