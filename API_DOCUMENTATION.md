# Financial Screener API Documentation

## Overview
The Financial Screener API provides endpoints for managing stock data, creating and running stock screens, and user authentication. This documentation covers all available endpoints, request/response formats, and usage examples.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints except login and registration require authentication using a Bearer token.

### Headers
```
Authorization: Bearer <your_token>
```

## Endpoints

### Authentication

#### Register User
```http
POST /auth/register
```

Request body:
```json
{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
}
```

Response (201 Created):
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
}
```

#### Login
```http
POST /auth/login
```

Request body:
```json
{
    "email": "user@example.com",
    "password": "securepassword"
}
```

Response (200 OK):
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}
```

### Stocks

#### Get All Stocks
```http
GET /stocks
```

Query Parameters:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)
- `symbol` (optional): Filter by stock symbol

Response (200 OK):
```json
{
    "stocks": [
        {
            "id": 1,
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 2000000000000,
            "pe_ratio": 25.5,
            "price": 150.25,
            "price_to_book": 15.2,
            "dividend_yield": 0.5,
            "eps": 6.0,
            "beta": 1.2,
            "fifty_two_week_high": 180.0,
            "fifty_two_week_low": 120.0,
            "avg_volume": 1000000
        }
    ],
    "total": 1
}
```

#### Get Stock by ID
```http
GET /stocks/{stock_id}
```

Response (200 OK):
```json
{
    "id": 1,
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "market_cap": 2000000000000,
    "pe_ratio": 25.5,
    "price": 150.25,
    "price_to_book": 15.2,
    "dividend_yield": 0.5,
    "eps": 6.0,
    "beta": 1.2,
    "fifty_two_week_high": 180.0,
    "fifty_two_week_low": 120.0,
    "avg_volume": 1000000
}
```

### Screens

#### Create Screen
```http
POST /screens
```

Request body:
```json
{
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
}
```

Response (201 Created):
```json
{
    "id": 1,
    "name": "Value Stocks",
    "description": "Stocks with low P/E ratio and high dividend yield",
    "is_public": false,
    "user_id": 1,
    "criteria": [
        {
            "id": 1,
            "screen_id": 1,
            "field": "pe_ratio",
            "operator": "<",
            "value": 15
        },
        {
            "id": 2,
            "screen_id": 1,
            "field": "dividend_yield",
            "operator": ">",
            "value": 3.0
        }
    ]
}
```

#### Get All Screens
```http
GET /screens
```

Query Parameters:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)
- `name` (optional): Filter by screen name

Response (200 OK):
```json
{
    "screens": [
        {
            "id": 1,
            "name": "Value Stocks",
            "description": "Stocks with low P/E ratio and high dividend yield",
            "is_public": false,
            "user_id": 1,
            "criteria": [...]
        }
    ],
    "total": 1
}
```

#### Get Screen by ID
```http
GET /screens/{screen_id}
```

Response (200 OK):
```json
{
    "id": 1,
    "name": "Value Stocks",
    "description": "Stocks with low P/E ratio and high dividend yield",
    "is_public": false,
    "user_id": 1,
    "criteria": [...]
}
```

#### Update Screen
```http
PUT /screens/{screen_id}
```

Request body:
```json
{
    "name": "Updated Value Stocks",
    "description": "Updated description",
    "is_public": true,
    "criteria": [
        {
            "field": "pe_ratio",
            "operator": "<",
            "value": 12
        }
    ]
}
```

Response (200 OK):
```json
{
    "id": 1,
    "name": "Updated Value Stocks",
    "description": "Updated description",
    "is_public": true,
    "user_id": 1,
    "criteria": [...]
}
```

#### Delete Screen
```http
DELETE /screens/{screen_id}
```

Response (204 No Content)

#### Run Screen
```http
POST /screens/{screen_id}/run
```

Response (200 OK):
```json
{
    "screen_id": 1,
    "screen_name": "Value Stocks",
    "results": [
        {
            "id": 1,
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 2000000000000,
            "pe_ratio": 14.5,
            "price": 150.25,
            "price_to_book": 15.2,
            "dividend_yield": 3.5,
            "eps": 6.0,
            "beta": 1.2,
            "fifty_two_week_high": 180.0,
            "fifty_two_week_low": 120.0,
            "avg_volume": 1000000
        }
    ],
    "count": 1,
    "execution_time": 0.123
}
```

## Data Models

### Stock
```typescript
interface Stock {
    id: number;
    symbol: string;
    company_name: string;
    sector?: string;
    industry?: string;
    market_cap?: number;
    pe_ratio?: number;
    price?: number;
    price_to_book?: number;
    dividend_yield?: number;
    eps?: number;
    beta?: number;
    fifty_two_week_high?: number;
    fifty_two_week_low?: number;
    avg_volume?: number;
    last_updated: string;
}
```

### Screen
```typescript
interface Screen {
    id: number;
    name: string;
    description?: string;
    user_id: number;
    is_public: boolean;
    created_at: string;
    updated_at?: string;
    criteria: ScreenCriteria[];
}
```

### ScreenCriteria
```typescript
interface ScreenCriteria {
    id: number;
    screen_id: number;
    field: string;
    operator: string;
    value: number | string | number[];
    created_at: string;
    updated_at?: string;
}
```

## Available Screen Criteria Fields
- `market_cap`: Market capitalization
- `pe_ratio`: Price to Earnings ratio
- `price`: Current stock price
- `price_to_book`: Price to Book ratio
- `dividend_yield`: Dividend yield percentage
- `eps`: Earnings per Share
- `beta`: Beta coefficient
- `fifty_two_week_high`: 52-week high price
- `fifty_two_week_low`: 52-week low price
- `avg_volume`: Average trading volume

## Available Operators
- `>`: Greater than
- `<`: Less than
- `=`: Equal to
- `>=`: Greater than or equal to
- `<=`: Less than or equal to
- `between`: Between two values (requires array of two numbers)

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Error message describing the issue"
}
```

### 401 Unauthorized
```json
{
    "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
    "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
    "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error message"
}
```

## Rate Limiting
The API implements rate limiting to prevent abuse. The current limits are:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

## Best Practices
1. Always handle API errors gracefully
2. Implement proper error handling for network issues
3. Cache responses when appropriate
4. Use pagination for large data sets
5. Validate input data before sending requests
6. Keep authentication tokens secure
7. Implement proper error handling for rate limiting 