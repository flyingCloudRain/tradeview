from datetime import date as dt_date

import pytest
from pydantic import ValidationError

from app.schemas.trading_calendar import TradingCalendarUpdate


def test_update_accepts_valid_payload():
    payload = {
        "date": "2026-01-06",
        "stock_name": "合众思壮",
        "direction": "买入",
        "strategy": "排板",
        "source": "云聪",
    }

    schema = TradingCalendarUpdate(**payload)

    assert schema.date == dt_date(2026, 1, 6)
    assert schema.stock_name == "合众思壮"
    assert schema.direction == "买入"
    assert schema.strategy == "排板"
    assert schema.source == "云聪"
    assert schema.notes is None
    assert schema.images is None


def test_update_rejects_invalid_direction():
    with pytest.raises(ValidationError):
        TradingCalendarUpdate(direction="无效方向")

