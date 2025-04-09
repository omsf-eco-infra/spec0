from spec0.releasefilters import SPEC0StrictDate

import logging

_logger = logging.getLogger(__name__)


def default_filter():
    """Default support filter if none is provided."""
    return SPEC0StrictDate()


def main(package, source, filter_=None):
    """Main function to get release info for a package.

    Parameters
    ----------
    package : str
        The name of the package to get release info for.
    source : ReleaseSource
        The source to use for getting release info.
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
    if filter_ is None:
        filter_ = default_filter()

    releases = source.get_releases(package)
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
