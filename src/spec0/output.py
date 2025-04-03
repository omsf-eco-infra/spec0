import json
from packaging.version import Version
from datetime import datetime
from .utils.packaging import make_specifier, major_minor_str


def json_output(pkg_info):
    """Print package information in JSON format.

    Parameters
    ----------
    pkg_info : dict
        Dictionary containing package information. See the output of
        :func:`.main` for details.
    """

    def default(obj):
        if isinstance(obj, Version):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:  # pragma: no cover
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    print(json.dumps(pkg_info, indent=4, default=default))


def specifier_output(pkg_info, include_upper_bound=True):
    """Print package information as a specifier.

    This allows you to provide the SPEC0-style requirements as version
    specifier suitable for use in a requirements file, for example
    ``mypackage >=1.1,<2``.

    Parameters
    ----------
    pkg_info : dict
        Dictionary containing package information. See the output of
        :func:`.main` for details.
    include_upper_bound : bool
        If True, include an upper bound of the specifier, defined as not
        allowing the next major version.
    """
    spec = make_specifier(pkg_info, include_upper_bound)
    print(f"{pkg_info['package']} {spec}")


def terminal_output(pkg_info, release_date=True, drop_date=True):
    """Print package information in a terminal-friendly table format.

    Parameters
    ----------
    pkg_info : dict
        Dictionary containing package information. See the output of
        :func:`.main` for details.
    release_date : bool
        If True (default), include the release date of each version.
    drop_date : bool
        If True (default), include the drop date of each version.
    """
    package = pkg_info["package"]
    release_names = [
        f"{package} {major_minor_str(release['version'])}"
        for release in pkg_info["releases"]
    ]
    release_dates = [release["release-date"] for release in pkg_info["releases"]]
    drop_dates = [release["drop-date"] for release in pkg_info["releases"]]
    name_width = max(len("Package"), max(len(name) for name in release_names))
    date_format = "%Y-%m-%d"
    if release_date:
        release_date_width = len("Release Date")
    else:
        release_date_width = 0

    if drop_date:
        drop_date_width = 10  # YYYY-MM-DD ; longer than "Drop Date"
    else:
        drop_date_width = 0

    # print header
    line = f"{'Package':<{name_width}}"
    if release_date:
        line += f" | {'Release Date':<{release_date_width}}"
    if drop_date:
        line += f" | {'Drop Date':<{drop_date_width}}"

    print(line)
    print("-" * len(line))
    for name, date_release, date_drop in zip(release_names, release_dates, drop_dates):
        line = f"{name:<{name_width}}"
        if release_date:
            line += f" | {date_release.strftime(date_format):<{release_date_width}}"
        if drop_date:
            line += f" | {date_drop.strftime(date_format):<{drop_date_width}}"

        print(line)
