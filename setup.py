#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  SPDX-License-Identifier: Apache-2.0

# Note: To use the "upload" functionality of this file, you must:
#   $ pip install twine
# sourced from https://github.com/kennethreitz/setup.py
"""
Python Package for controlling Tesla API.

For more details about this api, please refer to the documentation at
https://github.com/zabuldon/teslajsonpy
"""
import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = "teslajsonpy"
DESCRIPTION = "A library to work with Tesla API."
URL = "https://github.com/zabuldon/teslajsonpy"
EMAIL = "sergey.isachenkol@bool.by"
AUTHOR = "Sergey Isachenko"
REQUIRES_PYTHON = ">=3.0"
LICENSE = "Apache-2.0"
VERSION = None

# What packages are required for this module to be executed?
REQUIRED = [
    'teslajsonpy',
    'requests'
]

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
    with io.open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
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
        print("\033[1m{0}\033[0m".format(string))

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
        os.system("git tag v{0}".format(ABOUT["__version__"]))
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
    packages=find_packages(exclude=("tests",)),
    # If your package is a single module, use this instead of "packages":
    # py_modules=["mypackage"],

    # entry_points={
    #     "console_scripts": ["mycli=mymodule:cli"],
    # },
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
    ],
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
)
