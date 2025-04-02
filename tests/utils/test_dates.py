import datetime
import pytest

from spec0.utils.dates import *


@pytest.mark.parametrize(
    "datetime, expected",
    [
        (datetime.datetime(2023, 5, 15), (2023, 2)),
        (datetime.datetime(2023, 1, 1), (2023, 1)),
        (datetime.datetime(2023, 12, 31), (2023, 4)),
    ],
)
def test_get_quarter(datetime, expected):
    assert get_quarter(datetime) == expected


@pytest.mark.parametrize(
    "datetime, expected",
    [
        (datetime.datetime(2023, 5, 15), (2023, 3)),
        (datetime.datetime(2023, 11, 1), (2024, 1)),  # bump the year
    ],
)
def test_next_quarter(datetime, expected):
    assert next_quarter(datetime) == expected


def test_quarter_to_date():
    expected = datetime.datetime(2023, 4, 1, tzinfo=datetime.timezone.utc)
    assert quarter_to_date((2023, 2)) == expected


@pytest.mark.parametrize(
    "datetime, n_months, expected",
    [
        (datetime.datetime(2023, 1, 15), 3, datetime.datetime(2023, 4, 15)),
        (datetime.datetime(2023, 7, 15), 4, datetime.datetime(2023, 11, 15)),
    ],
)
def test_shift_date_by_months(datetime, n_months, expected):
    assert shift_date_by_months(datetime, n_months) == expected
