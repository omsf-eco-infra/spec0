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
        (datetime.datetime(2022, 6, 15), 0, datetime.datetime(2022, 6, 15)),
        (datetime.datetime(2022, 6, 15), 3, datetime.datetime(2022, 9, 15)),
        (datetime.datetime(2022, 11, 15), 1, datetime.datetime(2022, 12, 15)),
        (datetime.datetime(2022, 3, 15), 12, datetime.datetime(2023, 3, 15)),
        (datetime.datetime(2022, 5, 15), 15, datetime.datetime(2023, 8, 15)),
        (datetime.datetime(2020, 2, 29), 1, datetime.datetime(2020, 3, 29)),
        (datetime.datetime(2022, 11, 15), 2, datetime.datetime(2023, 1, 15)),
        (datetime.datetime(2021, 12, 31), 1, datetime.datetime(2022, 1, 31)),
        (datetime.datetime(2022, 1, 31), 1, datetime.datetime(2022, 3, 1)),
        (datetime.datetime(2020, 2, 29), 12, datetime.datetime(2021, 3, 1)),
    ],
)
def test_shift_date_by_months(datetime, n_months, expected):
    assert shift_date_by_months(datetime, n_months) == expected
