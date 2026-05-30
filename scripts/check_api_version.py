#  SPDX-License-Identifier: Apache-2.0
"""Detect Subaru API version drift between the MySubaru Android app and this repo.

The MySubaru app is a React Native app whose JavaScript is shipped as a Hermes bytecode
bundle (``assets/index.android.bundle``). The Connected Services API version is embedded
in that bundle as part of the backend base URLs, e.g. ``mobileapi.prod.subarucs.com/g2v32``.

This script extracts the API version from a decoded app bundle and compares it against the
``API_VERSION`` constant in ``subarulink/_subaru_api/const.py``. It exits non-zero when they
differ so a CI job can notify maintainers that Subaru has bumped the API version (which
breaks the package until ``API_VERSION`` is updated).

Usage:
    python scripts/check_api_version.py --bundle path/to/index.android.bundle
"""


import argparse
import importlib.util
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CONST_PATH = REPO_ROOT / "subarulink" / "_subaru_api" / "const.py"


def get_repo_api_version(const_path: pathlib.Path) -> str:
    """Return the API_VERSION value (e.g. "/g2v32") declared in const.py.

    The module is loaded in isolation rather than via ``import subarulink`` so that the
    real Python value is used (robust to quoting/formatting), without executing the package
    __init__ and pulling in runtime dependencies such as aiohttp. This works because
    _subaru_api/const.py contains only constants and has no imports of its own.
    """
    spec = importlib.util.spec_from_file_location("subarulink_api_const", const_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load module from {const_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.API_VERSION
    except AttributeError:
        raise SystemExit(f"Could not find API_VERSION in {const_path}") from None


def find_apk_api_versions(bundle: bytes, generation_prefix: str) -> set[int]:
    """Return the set of API version numbers found in the app bundle for a given generation.

    The Hermes string table packs strings without delimiters, so a version token can bleed
    into an adjacent string (e.g. ".../g2v" followed by a "150,000 miles" string yields a
    spurious "g2v150"). Anchoring on the ``subarucs.com/`` host and capping the version to two
    digits filters out that noise while still catching every real backend URL.
    """
    # e.g. rb"subarucs\.com/g2v(\d{1,2})(?!\d)"
    pattern = rb"subarucs\.com/" + re.escape(generation_prefix.encode()) + rb"(\d{1,2})(?!\d)"
    return {int(m) for m in re.findall(pattern, bundle)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--bundle",
        required=True,
        type=pathlib.Path,
        help="Path to the decoded app bundle (assets/index.android.bundle)",
    )
    parser.add_argument(
        "--const",
        default=DEFAULT_CONST_PATH,
        type=pathlib.Path,
        help="Path to subarulink/_subaru_api/const.py (default: repo copy)",
    )
    args = parser.parse_args()

    repo_version = get_repo_api_version(args.const)
    # Split "/g2v32" into generation prefix "g2v" and number 32.
    repo_match = re.match(r"/(g\dv)(\d+)", repo_version)
    if not repo_match:
        raise SystemExit(f"Unexpected API_VERSION format: {repo_version!r}")
    generation_prefix, repo_number = repo_match.group(1), int(repo_match.group(2))

    if not args.bundle.is_file():
        raise SystemExit(f"App bundle not found: {args.bundle}")
    bundle = args.bundle.read_bytes()

    found = find_apk_api_versions(bundle, generation_prefix)
    if not found:
        print(
            f"ERROR: Found no '{generation_prefix}<n>' API version tokens in {args.bundle}.\n"
            "The bundle format or URL scheme may have changed -- this check needs to be revisited.",
            file=sys.stderr,
        )
        return 2

    apk_number = max(found)
    found_str = ", ".join(f"{generation_prefix}{n}" for n in sorted(found))
    print(f"Repo API_VERSION:        {repo_version}")
    print(f"APK API versions found:  {found_str}")
    print(f"APK latest API version:  {generation_prefix}{apk_number}")

    if apk_number != repo_number:
        print(
            f"\nMISMATCH: repo uses {repo_version} but the APK's latest is "
            f"/{generation_prefix}{apk_number}.\n"
            f"Subaru likely changed the API version. Update API_VERSION in "
            f"{args.const.relative_to(REPO_ROOT) if args.const.is_relative_to(REPO_ROOT) else args.const}.",
            file=sys.stderr,
        )
        return 1

    print("\nOK: repo API_VERSION matches the latest version in the APK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
