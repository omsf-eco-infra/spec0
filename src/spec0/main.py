from spec0.releasesource import PyPIReleaseSource, CondaReleaseSource
from spec0.releasefilters import SPEC0StrictDate

import logging

_logger = logging.getLogger(__name__)


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
    result = {
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
    _logger.info(result)
    return result
