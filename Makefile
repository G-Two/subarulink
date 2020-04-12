# SPDX-License-Identifier: WTFPL
# Based on code from https://github.com/bachya/simplisafe-python/blob/dev/Makefile
black:
	pipenv run black subarulink
coverage:
	#Not implemented yet
	#pipenv run py.test -s --verbose --cov-report term-missing --cov-report xml --cov=subarulink tests
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
publish:
	pipenv run python setup.py sdist bdist_wheel
	pipenv run twine upload dist/*
	rm -rf dist/ build/ .egg subarulink.egg-info/
test:
	#Not implemented yet
	#pipenv run py.test
typing:
	pipenv run mypy --ignore-missing-imports subarulink
