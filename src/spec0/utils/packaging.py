from packaging.specifiers import SpecifierSet
from packaging.version import Version


def make_specifier(pkg_info, include_upper_bound=True):
    versions = [release["version"] for release in pkg_info["releases"]]
    min_version = min(versions)
    spec = SpecifierSet(f">={min_version}")
    if include_upper_bound:
        max_version = max(versions)
        upper = Version(f"{max_version.epoch}!{max_version.major + 1}.0")
        spec = spec & SpecifierSet(f"<{upper}")
    return spec


def major_minor_str(version):
    major_minor_str = f"{version.major}.{version.minor}"
    if version.epoch != 0:
        major_minor_str = f"{version.epoch}!{major_minor_str}"

    return major_minor_str
