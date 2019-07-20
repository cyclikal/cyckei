.PHONY: help update clean run build count

VENV?=venv
PYTHON=${VENV}/bin/python3

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

setup: $(VENV)/bin/activate
$(VENV)/bin/activate: requirements.txt
	python3 -m pip install virtualenv
	test -d $(VENV) || virtualenv $(VENV)
	$(VENV)/bin/pip install -Ur requirements.txt

clean:
	rm -rf $(VENV)
	rm -rf build
	rm -rf dist
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

run:
	${PYTHON} cyckei.py

build:
	${PYTHON} -m PyInstaller --onefile --windowed --noconfirm --clean cyckei.spec

count:
	find . -name '*.py' -o -path ./$(VENV) -prune | xargs wc -l
