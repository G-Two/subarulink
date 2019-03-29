# SPDX-License-Identifier: WTFPL
# Based on code from https://github.com/bachya/simplisafe-python/blob/dev/Makefile
coverage:
	#Not implemented yet
	#pipenv run py.test -s --verbose --cov-report term-missing --cov-report xml --cov=teslajsonpy tests
clean:
	rm -rf dist/ build/ .egg teslajsonpy.egg-info/
init:
	pip3 install --upgrade pip pipenv
	pipenv lock
	pipenv install --three --dev
lint: flake8 docstyle pylint
flake8:
	pipenv run flake8 teslajsonpy
docstyle:
	pipenv run pydocstyle teslajsonpy
pylint:
	pipenv run pylint teslajsonpy
publish:
	pipenv run python setup.py sdist bdist_wheel
	pipenv run twine upload dist/*
	rm -rf dist/ build/ .egg teslajsonpy.egg-info/
test:
	#Not implemented yet
	#pipenv run py.test
typing:
	pipenv run mypy --ignore-missing-imports teslajsonpy
