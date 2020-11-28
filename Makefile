# SPDX-License-Identifier: WTFPL
# Based on code from https://github.com/bachya/simplisafe-python/blob/dev/Makefile
build:
	pipenv run python setup.py sdist bdist_wheel
black:
	pipenv run black subarulink
clean:
	rm -rf dist/ build/ .egg subarulink.egg-info/
init:
	pip3 install --upgrade pip pipenv
	pipenv lock
	pipenv install --three --dev
	pre-commit install
lint: flake8 docstyle pylint
flake8:
	pipenv run flake8 subarulink
docstyle:
	pipenv run pydocstyle subarulink
pylint:
	pipenv run pylint subarulink
publish: build
	pipenv run twine upload dist/*
test:
	pipenv run pytest

