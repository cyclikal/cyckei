.PHONY: help update clean run build count

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3

help:
	@echo "help"
	@echo "	Show this help dialog"
	@echo "setup"
	@echo "	Setup virtual environment with requirements"
	@echo "clean"
	@echo "	Remove virtual environment, builds, cache, and compiled files"
	@echo "run"
	@echo "	Run current Cyckei version"
	@echo "build"
	@echo "	Freeze current Cyckei version"
	@echo "count"
	@echo "	Count lines of python code"

setup: $(VENV_NAME)/bin/activate
$(VENV_NAME)/bin/activate: requirements.txt
	python3 -m pip install virtualenv
	test -d $(VENV_NAME) || virtualenv $(VENV_NAME)
	$(VENV_NAME)/bin/pip install -Ur requirements.txt

clean:
	rm -rf $(VENV_NAME)
	rm -rf build
	rm -rf dist
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

run:
	${PYTHON} cyckei.py

build:
	${PYTHON} -m PyInstaller --onefile --windowed --noconfirm --clean cyckei.spec

count:
	find . -name '*.py' | xargs wc -l
