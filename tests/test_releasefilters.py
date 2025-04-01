import datetime
import pytest
from packaging.version import Version
from unittest.mock import patch

from spec0.releasefilters import *

read_datetime = datetime.datetime


@pytest.fixture
def releases():
    # a set of releases where, by strict date, 0 and 3 should be dropped,
    # and by quarter, 0 should be dropped.
    rA = Release(
        version=Version("1.0.0"),
        release_date=datetime.datetime(2021, 12, 15, tzinfo=datetime.timezone.utc),
    )
    rB = Release(
        version=Version("1.1.0"),
        release_date=datetime.datetime(2022, 6, 1, tzinfo=datetime.timezone.utc),
    )
    rC = Release(
        version=Version("0.9.0"),
        release_date=datetime.datetime(2022, 3, 1, tzinfo=datetime.timezone.utc),
    )
    rD = Release(
        version=Version("1.2.0"),
        release_date=datetime.datetime(2022, 1, 1, tzinfo=datetime.timezone.utc),
    )
    releases = [rA, rB, rC, rD]
    return releases


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


def test_get_oldest_minor_release():
    r1 = Release(
        version=Version("1.0.0"),
        release_date=datetime.datetime(2023, 1, 15, tzinfo=datetime.timezone.utc),
    )
    r2 = Release(
        version=Version("1.0.0"),
        release_date=datetime.datetime(2023, 1, 10, tzinfo=datetime.timezone.utc),
    )
    r3 = Release(
        version=Version("1.1.0"),
        release_date=datetime.datetime(2023, 2, 1, tzinfo=datetime.timezone.utc),
    )
    # pre-release: not included
    r4 = Release(
        version=Version("1.1.0a1"),
        release_date=datetime.datetime(2023, 1, 5, tzinfo=datetime.timezone.utc),
    )
    releases = [r1, r2, r3, r4]
    oldest = get_oldest_minor_release(releases)
    # For (0,1,0), the oldest is r2; for (0,1,1), it is r3.
    assert oldest[(0, 1, 0)] == r2
    assert oldest[(0, 1, 1)] == r3


@pytest.mark.parametrize("include_upper_bound", [True, False])
def test_make_specifier(include_upper_bound):
    r1 = Release(
        version=Version("1.0.0"),
        release_date=datetime.datetime(2023, 1, 15, tzinfo=datetime.timezone.utc),
    )
    r2 = Release(
        version=Version("1.1.0"),
        release_date=datetime.datetime(2023, 2, 15, tzinfo=datetime.timezone.utc),
    )
    supported = {(0, 1, 0): r1, (0, 1, 1): r2}
    spec = make_specifier(supported, include_upper_bound=include_upper_bound)
    assert Version("1.0.0") in spec
    assert Version("1.5.0") in spec
    assert (Version("2.0.0") in spec) is not include_upper_bound


@pytest.mark.parametrize("package", ["python", "other"])
@pytest.mark.parametrize("python_override", [True, False])
def test_get_n_months(package, python_override):
    if package == "python" and python_override:
        expected = 36
    else:
        expected = 24
    spec = SPEC0StrictDate(n_months=24, python_override=python_override)
    assert spec._get_n_months(package) == expected


class TestSPEC0StrictDate:
    def test_filter(self, releases):
        fixed_now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        with patch(
            "spec0.releasefilters.datetime.datetime", wraps=datetime.datetime
        ) as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_now

            spec_strict = SPEC0StrictDate(n_months=24, python_override=False)
            supported = spec_strict.filter("foo", releases)
            expected = releases[1:-1]
            for release in expected:
                key = (
                    release.version.epoch,
                    release.version.major,
                    release.version.minor,
                )
                assert key in supported

    @pytest.mark.parametrize("python_override", [True, False])
    @pytest.mark.parametrize("package", ["foo", "python"])
    def test_drop_date(self, python_override, package):
        r = Release(
            version=Version("1.0.0"),
            release_date=datetime.datetime(2023, 1, 15, tzinfo=datetime.timezone.utc),
        )
        if python_override and package == "python":
            expected = datetime.datetime(2026, 1, 15, tzinfo=datetime.timezone.utc)
        else:
            expected = datetime.datetime(2025, 1, 15, tzinfo=datetime.timezone.utc)
        spec_strict = SPEC0StrictDate(n_months=24, python_override=python_override)
        drop = spec_strict.drop_date(package, r)
        assert drop == expected


class TestSPEC0Quarter:
    def test_filter(self, releases):
        fixed_now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        with patch(
            "spec0.releasefilters.datetime.datetime", wraps=datetime.datetime
        ) as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_now

            spec_quarter = SPEC0Quarter(n_months=24, python_override=False)
            supported = spec_quarter.filter("foo", releases)

            expected = releases[1:]

            for release in expected:
                key = (
                    release.version.epoch,
                    release.version.major,
                    release.version.minor,
                )
                assert key in supported

    @pytest.mark.parametrize("python_override", [True, False])
    @pytest.mark.parametrize("package", ["foo", "python"])
    def test_drop_date(self, python_override, package):
        r = Release(
            version=Version("1.0.0"),
            release_date=datetime.datetime(2023, 1, 15, tzinfo=datetime.timezone.utc),
        )
        if python_override and package == "python":
            expected = datetime.datetime(2026, 4, 1, tzinfo=datetime.timezone.utc)
        else:
            expected = datetime.datetime(2025, 4, 1, tzinfo=datetime.timezone.utc)
        spec0 = SPEC0Quarter(n_months=24, python_override=python_override)
        drop = spec0.drop_date(package, r)
        assert drop == expected
