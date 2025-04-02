from spec0.releasesource import PyPIReleaseSource, CondaReleaseSource
from spec0.releasefilters import SPEC0StrictDate


def default_sources():
    return [
        PyPIReleaseSource(),
        CondaReleaseSource(["conda-forge/noarch", "conda-forge/linux-64"]),
    ]


def default_filter():
    return SPEC0StrictDate()


def main(package, sources=None, filter_=None):
    if sources is None:
        sources = default_sources()

    if filter_ is None:
        filter_ = default_filter()

    # we take the releases from the first source that has them
    for source in sources:
        if releases := source.get_releases(package):
            break

    filtered = filter_.filter(package, releases)
    return {
        "package": package,
        "releases": [
            {
                "version": release.version,
                "release-date": release.release_date,
                "drop-date": filter_.drop_date(package, release),
            }
            for release in filtered.values()
        ],
    }


def _major_minor_str(version):
    major_minor_str = f"{version.major}.{version.minor}"
    if version.epoch != 0:
        major_minor_str = f"{version.epoch}!{major_minor_str}"

    return major_minor_str


def terminal_output(pkg_info, release_date=True, drop_date=True):
    package = pkg_info["package"]
    release_names = [
        f"{package} {_major_minor_str(release['version'])}"
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
