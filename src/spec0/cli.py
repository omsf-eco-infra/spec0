import argparse
import logging

from functools import partial

from spec0.releasesource import PyPIReleaseSource, CondaReleaseSource
from spec0.releasefilters import SPEC0StrictDate, SPEC0Quarter
from spec0.output import terminal_output, json_output, specifier_output
from spec0.main import main


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument("--log-level", default="WARNING")

    source = parser.add_argument_group("Source")
    source.add_argument("--pypi", action="store_true")
    source.add_argument("--conda-channel")
    source.add_argument("--conda-arch", nargs="+", default=["noarch", "linux-64"])
    # source.add_argument('--github', action='store_true')

    # filter options
    filterg = parser.add_argument_group("Filter")
    filterg.add_argument(
        "--filter", choices=["spec0", "spec0quarterly"], default="spec0"
    )
    filterg.add_argument("--n-months", type=int, default=24)

    # output options
    output = parser.add_argument_group("Output")
    output.add_argument(
        "--output-columns", nargs="+", default=["package", "release-date", "drop-date"]
    )
    output.add_argument("--output-json", action="store_true")
    output.add_argument("--output-specifier", action="store_true")

    return parser


def select_source(opts):
    selected_pypi = opts.pypi
    selected_conda = opts.conda_channel is not None
    # selected_github = opts.github
    n_selected = sum([selected_pypi, selected_conda])
    if n_selected == 0:
        source = None
    elif n_selected > 1:
        raise ValueError("Only one source can be selected")
    else:
        if selected_pypi:
            source = [PyPIReleaseSource()]
        elif selected_conda:
            platforms = [f"{opts.conda_channel}/{arch}" for arch in opts.conda_arch]
            source = [CondaReleaseSource(platforms)]
        # elif selected_github:
        #    source = GitHubReleaseSource()
    return source


def select_filter(opts):
    if opts.filter == "spec0":
        filter_ = SPEC0StrictDate(opts.n_months)
    elif opts.filter == "spec0quarterly":
        filter_ = SPEC0Quarter(opts.n_months)
    return filter_


def select_output(opts):
    n_selected = sum([opts.output_json, opts.output_specifier])
    if n_selected == 0:
        release_date = "Release Date" in opts.output_columns
        drop_date = "Drop Date" in opts.output_columns
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
        else:
            raise RuntimeError("This should never happen")
    return output


if __name__ == "__main__":
    parser = make_parser()
    opts = parser.parse_args()
    logging.basicConfig(level=opts.log_level)  # eww

    sources = select_source(opts)
    filter_ = select_filter(opts)
    output = select_output(opts)

    results = main(opts.package, sources, filter_)
    output(results)
