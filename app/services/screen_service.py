from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from typing import List, Dict, Any
from app.models.screen import Screen, ScreenCriteria
from app.models.stock import Stock

class ScreenService:
    def __init__(self, db: Session):
        self.db = db

    def _build_criteria_condition(self, criterion: ScreenCriteria) -> Any:
        """Build SQL condition for a single criterion"""
        field = getattr(Stock, criterion.field, None)
        if not field:
            raise ValueError(f"Invalid field: {criterion.field}")

        if criterion.operator == ">":
            return field > criterion.value
        elif criterion.operator == "<":
            return field < criterion.value
        elif criterion.operator == "=":
            return field == criterion.value
        elif criterion.operator == ">=":
            return field >= criterion.value
        elif criterion.operator == "<=":
            return field <= criterion.value
        elif criterion.operator == "between":
            if not isinstance(criterion.value, list) or len(criterion.value) != 2:
                raise ValueError("Between operator requires a list of two values")
            return and_(field >= criterion.value[0], field <= criterion.value[1])
        else:
            raise ValueError(f"Invalid operator: {criterion.operator}")

    def run_screen(self, screen_id: int) -> Dict[str, Any]:
        """Execute a screen and return matching stocks"""
        # Get screen and its criteria
        screen = self.db.query(Screen).filter(Screen.id == screen_id).first()
        if not screen:
            raise ValueError(f"Screen with ID {screen_id} not found")

        # Build query conditions
        conditions = []
        for criterion in screen.criteria:
            try:
                condition = self._build_criteria_condition(criterion)
                conditions.append(condition)
            except ValueError as e:
                raise ValueError(f"Error in criterion {criterion.id}: {str(e)}")

        # Apply all conditions
        query = self.db.query(Stock)
        if conditions:
            query = query.filter(and_(*conditions))

        # Execute query
        matching_stocks = query.all()

        # Format results
        results = []
        for stock in matching_stocks:
            stock_dict = {
                "id": stock.id,
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "sector": stock.sector,
                "industry": stock.industry,
                "market_cap": stock.market_cap,
                "pe_ratio": stock.pe_ratio,
                "price": stock.price,
                "price_to_book": stock.price_to_book,
                "dividend_yield": stock.dividend_yield,
                "eps": stock.eps,
                "beta": stock.beta,
                "fifty_two_week_high": stock.fifty_two_week_high,
                "fifty_two_week_low": stock.fifty_two_week_low,
                "avg_volume": stock.avg_volume
            }
            results.append(stock_dict)

        return {
            "screen_id": screen.id,
            "screen_name": screen.name,
            "results": results,
            "count": len(results)
        } 