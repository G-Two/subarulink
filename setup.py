#!/usr/bin/env python
#  SPDX-License-Identifier: Apache-2.0

# Note: To use the "upload" functionality of this file, you must:
#   $ pip install twine
# sourced from https://github.com/kennethreitz/setup.py
"""
subarulink - A Python Package for interacting with Subaru Starlink Remote Services API.

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import os
from shutil import rmtree
import sys

from setuptools import Command, setup

# Package meta-data.
NAME = "subarulink"
DESCRIPTION = "A package for interacting with Subaru Starlink Remote Services API."
URL = "https://github.com/G-Two/subarulink"
EMAIL = ""
AUTHOR = "G-Two"
REQUIRES_PYTHON = ">=3.9"
LICENSE = "Apache-2.0"
VERSION = None

# What packages are required for this module to be executed?
REQUIRED = ["aiohttp", "stdiomask"]

# What packages are optional?
EXTRAS = {
    # "fancy feature": ["django"],
}

# The rest you shouldn"t have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for
# that!
HERE = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if "README.md" is present in your MANIFEST.in file!
try:
    with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
        LONG_DESCRIPTION = "\n" + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = DESCRIPTION

# Load the package"s __version__.py module as a dictionary.
ABOUT = {}
if not VERSION:
    PROJECT_SLUG = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(HERE, PROJECT_SLUG, "__version__.py")) as f:
        exec(f.read(), ABOUT)  # pylint: disable=exec-used
else:
    ABOUT["__version__"] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(string):
        """Print things in bold."""
        print(f"\033[1m{string}\033[0m")

    def initialize_options(self):
        """Initialize options."""

    def finalize_options(self):
        """Finalize options."""

    def run(self):
        """Run UploadCommand."""
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(HERE, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal".
                  format(sys.executable))

        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        os.system("git tag v{}".format(ABOUT["__version__"]))
        os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=ABOUT["__version__"],
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=['subarulink', 'subarulink.app', 'subarulink._subaru_api'],
    entry_points={"console_scripts": ["subarulink = subarulink.app.cli:main"]},
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license=LICENSE,
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet',
    ],
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
)
