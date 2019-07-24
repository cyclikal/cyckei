.PHONY: help update clean clean-all run build count docs view lint

VENV=venv
PYTHON=${VENV}/bin/python3
DOCS=docs

help:
	@echo "help"
	@echo "	Show this help dialog."
	@echo "setup"
	@echo "	Setup virtual environment with requirements."

	@echo "run"
	@echo "	Run current Cyckei version."
	@echo "build"
	@echo "	Freeze current Cyckei version into executable."

	@echo "clean"
	@echo "	Remove builds, cache, and compiled files."
	@echo "clean-all"
	@echo "	Remove virtual environment, and everything that make clean does."

	@echo "count"
	@echo "	Count lines of python code."

	@echo "docs"
	@echo "	Generate documenation with Sphinx."
	@echo "read"
	@echo "	View latest generated documentation."

setup: ${VENV}/bin/activate
${VENV}/bin/activate: requirements.txt
	python3 -m pip install virtualenv
	test -d ${VENV} || virtualenv ${VENV}
	${VENV}/bin/pip install -Ur requirements.txt

clean:
	rm -rf build
	rm -rf docs/_build/*
	find . | grep -E "(__pycache__|\.pyc|\.pyo|\.DS_Store$$)" | xargs rm -rf

clean-all:
	rm -rf ${VENV}
	make clean

run:
	${PYTHON} cyckei.py

build:
	${VENV}/bin/pip install pycrypto PyInstaller
	${PYTHON} -m PyInstaller --onefile --windowed --noconfirm --clean cyckei.spec

count:
	find . -name '*.py' -o -path ./${VENV} -prune | xargs wc -l

docs:
	${VENV}/bin/pip install Sphinx
	${VENV}/bin/sphinx-build -b html ${DOCS} ${DOCS}/_build

read:
	test -f ${DOCS}/_build/index.html || make docs
	open ${DOCS}/_build/index.html
