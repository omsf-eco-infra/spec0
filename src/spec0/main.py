from spec0.releasesource import PyPIReleaseSource, CondaReleaseSource
from spec0.releasefilters import SPEC0StrictDate

import logging

_logger = logging.getLogger(__name__)


def default_sources():
    """Default release sources if none are provided."""
    return [
        PyPIReleaseSource(),
        CondaReleaseSource(["conda-forge/noarch", "conda-forge/linux-64"]),
    ]


def default_filter():
    """Default support filter if none is provided."""
    return SPEC0StrictDate()


def main(package, sources=None, filter_=None):
    """Main function to get release info for a package.

    Parameters
    ----------
    package : str
        The name of the package to get release info for.
    sources : list, optional
        A list of release sources to use. If None, default sources are used.
    filter_ : ReleaseFilter, optional
        A release filter to use. If None, default filter is used.

    Returns
    -------
    pkg_info : dict
        A dictionary describing the support requirements. This is a dict key
        with keys "package" and "releases". The value of "package" is the
        name of the package. The value of "releases" is a list of dicts with
        keys "version", "release-date", and "drop-date", where "version" is
        the packaging.version.Version of the release, "release-date" is the
        (datetime) release date of the release, and "drop-date" is the
        (datetime) drop date of the release, according to the input filter.
    """
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
