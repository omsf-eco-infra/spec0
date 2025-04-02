import pytest

from spec0.output import *
from packaging.version import Version
import datetime


@pytest.mark.parametrize("release_date", [True, False])
@pytest.mark.parametrize("drop_date", [True, False])
def test_terminal_output_combined(capsys, release_date, drop_date):
    pkg_info = {
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
