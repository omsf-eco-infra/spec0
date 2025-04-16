import argparse
import logging
import os

from functools import partial

from spec0.releasesource import (
    PyPIReleaseSource,
    CondaReleaseSource,
    GitHubReleaseSource,
    DefaultReleaseSource,
)
from spec0.releasefilters import SPEC0StrictDate, SPEC0Quarter
from spec0.output import terminal_output, json_output, specifier_output
from spec0.main import main


def make_parser():
    """Make the command line parser for the spec0 CLI."""
    parser = argparse.ArgumentParser(
        prog="spec0",
        description=(
            "List versions of a given package that should be supported "
            "according to spec0-style rules. This can be customized in "
            "3 ways: the source of the release information, the filter "
            "that defines supported versions, and the output format. "
            "By default, we search first if this package is known as "
            "a GitHub release, then we check for it on PyPI, and finally "
            "on conda-forge (in noarch and linux-64). The default uses "
            "SPEC0 according to the exact date of the release, and outputs "
            "as a table with release dates and drop dates."
        ),
    )
    parser.add_argument("package", help="Python package to look up")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        help="Set the logging level (default: WARNING)",
    )

    source = parser.add_argument_group(
        "Source",
        description=(
            "Select the source of the release information. Only one source "
            "can be selected."
        ),
    )
    source.add_argument(
        "--pypi",
        action="store_true",
        help="Use PyPI (only) as the source for release information",
    )
    source.add_argument(
        "--conda-channel",
        type=str,
        help="Use a conda channel as the source for release information",
    )
    source.add_argument(
        "--conda-arch",
        nargs="+",
        default=["noarch", "linux-64"],
        help=("Conda architectures to check, only used if conda-channel is specified"),
    )
    source.add_argument("--github", action="store_true")

    # filter options
    filterg = parser.add_argument_group(
        "Filter",
        description=("Select the filter to select which releases are supported."),
    )
    filterg.add_argument(
        "--filter",
        choices=["spec0", "spec0quarterly"],
        default="spec0",
        help="Filter type to apply to release data",
    )
    filterg.add_argument(
        "--n-months",
        type=int,
        default=24,
        help="Number of months to support releases (default: 24)",
    )

    # output options
    output = parser.add_argument_group(
        "Output",
        description=(
            "Select the output format. Only one output can be selected. "
            "``output-columns`` selects the columns to be printed in the "
            "table, and is ignored if ``output-json`` or ``output-specifier`` "
            "is selected."
        ),
    )
    output.add_argument(
        "--output-columns",
        action="append",
        choices=["release-date", "drop-date"],
        help=(
            "Columns to include in the output table. Package (including "
            "version) is always included."
        ),
    )
    output.add_argument(
        "--output-json",
        action="store_true",
        help="Output the results as JSON",
    )
    output.add_argument(
        "--output-specifier",
        action="store_true",
        help="Output the results as a version specifier, e.g. '>=1.2'",
    )
    return parser


def select_source(opts):
    """Use CLI arguments to select the source of the release information.

    Parameters
    ----------
    opts : argparse.Namespace
        The command line arguments.
    """
    selected_pypi = opts.pypi
    selected_conda = opts.conda_channel is not None
    selected_github = opts.github
    n_selected = sum([selected_pypi, selected_conda, selected_github])
    token = os.getenv("GITHUB_TOKEN")
    if n_selected == 0:
        source = DefaultReleaseSource(token)
    elif n_selected > 1:
        raise ValueError("Only one source can be selected")
    else:
        if selected_pypi:
            source = PyPIReleaseSource()
        elif selected_conda:
            platforms = [f"{opts.conda_channel}/{arch}" for arch in opts.conda_arch]
            source = CondaReleaseSource(platforms)
        elif selected_github:
            source = GitHubReleaseSource(token)

    return source


def select_filter(opts):
    """Use CLI arguments to select the support filter.

    Parameters
    ----------
    opts : argparse.Namespace
        The command line arguments.
    """
    if opts.filter == "spec0":
        filter_ = SPEC0StrictDate(opts.n_months)
    elif opts.filter == "spec0quarterly":
        filter_ = SPEC0Quarter(opts.n_months)
    return filter_


def select_output(opts):
    """Use CLI arguments to select the output format.

    Parameters
    ----------
    opts : argparse.Namespace
        The command line arguments.
    """
    n_selected = sum([opts.output_json, opts.output_specifier])
    if n_selected == 0:
        if not opts.output_columns:
            # default
            opts.output_columns = ["package", "release-date", "drop-date"]
        release_date = "release-date" in opts.output_columns
        drop_date = "drop-date" in opts.output_columns
        output = partial(
            terminal_output, release_date=release_date, drop_date=drop_date
        )
    elif n_selected > 1:
        raise ValueError("Only one output can be selected")
    else:
        if opts.output_json:
            output = json_output
        elif opts.output_specifier:
            output = specifier_output
        else:  # pragma: no cover
            raise RuntimeError("This should never happen")
    return output


def cli_main():
    parser = make_parser()
    opts = parser.parse_args()
    # maybe in the future be a little more precise in setting logging to our
    # loggers, not the root logger
    logging.basicConfig(level=opts.log_level)

    sources = select_source(opts)
    filter_ = select_filter(opts)
    output = select_output(opts)

    results = main(opts.package, sources, filter_)
    output(results)


if __name__ == "__main__":
    cli_main()
