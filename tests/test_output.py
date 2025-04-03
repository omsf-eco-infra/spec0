import pytest
import json

from spec0.output import *
from packaging.version import Version
import datetime


@pytest.fixture
def pkg_info():
    return {
        "package": "mypackage",
        "releases": [
            {
                "version": Version("1.0"),
                "release-date": datetime.datetime(2020, 1, 1),
                "drop-date": datetime.datetime(2021, 1, 1),
            },
            {
                "version": Version("1!2.3"),
                "release-date": datetime.datetime(2020, 2, 2),
                "drop-date": datetime.datetime(2021, 2, 2),
            },
        ],
    }


def test_json_output(capsys, pkg_info):
    json_output(pkg_info)
    captured = capsys.readouterr().out
    output_dict = json.loads(captured)
    expected = {
        "package": "mypackage",
        "releases": [
            {
                "version": "1.0",
                "release-date": "2020-01-01T00:00:00",
                "drop-date": "2021-01-01T00:00:00",
            },
            {
                "version": "1!2.3",
                "release-date": "2020-02-02T00:00:00",
                "drop-date": "2021-02-02T00:00:00",
            },
        ],
    }
    assert output_dict == expected


@pytest.mark.parametrize(
    "include_upper_bound, expected",
    [
        (True, "mypackage <1!3.0,>=1.0\n"),
        (False, "mypackage >=1.0\n"),
    ],
)
def test_specifier_output(capsys, pkg_info, include_upper_bound, expected):
    specifier_output(pkg_info, include_upper_bound=include_upper_bound)
    captured = capsys.readouterr().out
    assert captured == expected


@pytest.mark.parametrize("release_date", [True, False])
@pytest.mark.parametrize("drop_date", [True, False])
def test_terminal_output_combined(capsys, pkg_info, release_date, drop_date):
    terminal_output(pkg_info, release_date=release_date, drop_date=drop_date)
    captured = capsys.readouterr().out
    header_line, _, first_row, second_row = captured.splitlines()

    # Fixed assertions that are always expected.
    assert "Package" in header_line
    assert "mypackage 1.0" in first_row
    assert "mypackage 1!2.3" in second_row

    # Check header for release date and drop date based on flags.
    if release_date:
        assert "Release Date" in header_line
        assert "2020-01-01" in first_row
        assert "2020-02-02" in second_row
    else:
        assert "Release Date" not in header_line
        assert "2020-01-01" not in first_row
        assert "2020-02-02" not in second_row

    if drop_date:
        assert "Drop Date" in header_line
        assert "2021-01-01" in first_row
        assert "2021-02-02" in second_row
    else:
        assert "Drop Date" not in header_line
        assert "2021-01-01" not in first_row
        assert "2021-02-02" not in second_row
