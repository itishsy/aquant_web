"""Database initialization helpers."""

from src.db.models import (
    Hot,
    RevHot,
    RevPan,
    RevZtb,
    Review,
    Signal,
    TradeDailyPlan,
    TradeDailyPlanItem,
    TradeMonthlySummary,
    TradeWeeklyReview,
    User,
    db,
)


def init_db():
    """Create required tables if they do not exist."""
    table_models = [
        User,
        Signal,
        Review,
        Hot,
        RevPan,
        RevHot,
        RevZtb,
        TradeDailyPlan,
        TradeDailyPlanItem,
        TradeWeeklyReview,
        TradeMonthlySummary,
    ]

    db.connect(reuse_if_open=True)
    try:
        db.create_tables(table_models, safe=True)
    finally:
        if not db.is_closed():
            db.close()


if __name__ == "__main__":
    init_db()
