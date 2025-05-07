import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.stock import Stock
from app.models.screen import Screen, ScreenCriteria
from app.utils.security import get_password_hash

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create a test user and get token
def get_test_token(client):
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
    )
    
    # Login
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )
    
    return response.json()["access_token"]

@pytest.fixture
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Use TestClient
    with TestClient(app) as c:
        yield c
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db):
    # Create test user
    hashed_password = get_password_hash("password123")
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_stocks(db):
    # Create test stocks
    stocks = [
        Stock(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=2500000000000,
            pe_ratio=28.5,
            price=175.50,
            price_to_book=45.2,
            dividend_yield=0.5,
            eps=6.15,
            beta=1.2
        ),
        Stock(
            symbol="MSFT",
            company_name="Microsoft Corporation",
            sector="Technology",
            industry="Software",
            market_cap=2300000000000,
            pe_ratio=32.1,
            price=330.75,
            price_to_book=15.8,
            dividend_yield=0.8,
            eps=10.3,
            beta=0.9
        ),
        Stock(
            symbol="GOOGL",
            company_name="Alphabet Inc.",
            sector="Technology",
            industry="Internet Content & Information",
            market_cap=1800000000000,
            pe_ratio=25.4,
            price=140.20,
            price_to_book=6.2,
            dividend_yield=0,
            eps=5.5,
            beta=1.1
        )
    ]
    
    for stock in stocks:
        db.add(stock)
    
    db.commit()
    return stocks

def test_create_screen(client):
    token = get_test_token(client)
    
    # Create screen
    response = client.post(
        "/api/screens/",
        json={
            "name": "Test Screen",
            "description": "A test screening criteria",
            "is_public": True,
            "criteria": [
                {
                    "field": "pe_ratio",
                    "operator": "<",
                    "value": 30
                },
                {
                    "field": "market_cap",
                    "operator": ">",
                    "value": 1000000000000
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Screen"
    assert data["description"] == "A test screening criteria"
    assert data["is_public"] == True
    assert len(data["criteria"]) == 2

def test_get_screens(client, test_user, db):
    token = get_test_token(client)
    
    # Create screens
    screen1 = Screen(
        name="Screen 1",
        description="First test screen",
        user_id=test_user.id,
        is_public=True
    )
    
    screen2 = Screen(
        name="Screen 2",
        description="Second test screen",
        user_id=test_user.id,
        is_public=False
    )
    
    db.add(screen1)
    db.add(screen2)
    db.commit()
    
    # Get screens
    response = client.get(
        "/api/screens/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["screens"]) == 2
    assert data["screens"][0]["name"] == "Screen 1"
    assert data["screens"][1]["name"] == "Screen 2"

def test_run_screen(client, test_user, test_stocks, db):
    token = get_test_token(client)
    
    # Create screen
    screen = Screen(
        name="Value Tech Stocks",
        description="Technology stocks with reasonable PE ratios",
        user_id=test_user.id,
        is_public=True
    )
    
    db.add(screen)
    db.commit()
    db.refresh(screen)
    
    # Add criteria
    criterion1 = ScreenCriteria(
        screen_id=screen.id,
        field="sector",
        operator="=",
        value="Technology"
    )
    
    criterion2 = ScreenCriteria(
        screen_id=screen.id,
        field="pe_ratio",
        operator="<",
        value=30
    )
    
    db.add(criterion1)
    db.add(criterion2)
    db.commit()
    
    # Run screen
    response = client.post(
        f"/api/screens/{screen.id}/run",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["screen_id"] == screen.id
    assert data["screen_name"] == "Value Tech Stocks"
    assert data["count"] == 1  # Only AAPL should match
    assert data["results"][0]["symbol"] == "AAPL"
