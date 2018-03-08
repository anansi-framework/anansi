"""Test datetime based fields."""
import datetime


def test_date_field():
    """Test date field definition."""
    from anansi.fields import Date

    date = Date()
    assert date.data_type is datetime.date


def test_datetime_field():
    """Test datetime field definition."""
    from anansi.fields import Datetime

    dtime = Datetime()
    assert dtime.data_type is datetime.datetime
    assert dtime.as_utc is False
    assert dtime.with_timezone is False

    utc_dtime = Datetime(as_utc=True, with_timezone=True)
    assert utc_dtime.data_type is datetime.datetime
    assert utc_dtime.as_utc is True
    assert utc_dtime.with_timezone is True


def test_time_field():
    """Test time field definition."""
    from anansi.fields import Time

    time = Time()
    assert time.data_type is datetime.time
