.PHONY: help venv update clean run build

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3

help:
	@echo "help"
	@echo "	Show this help dialog"
	@echo "venv"
	@echo "	Setup virtual environment with requirements"
	@echo "clean"
	@echo "	Remove virtual environment and reinstall requirements"
	@echo "run"
	@echo "	Run current Cyckei version"
	@echo "build"
	@echo "	Freeze current Cyckei version"

venv:
	python3 -m pip install virtualenv
	test -d $(VENV_NAME) || virtualenv $(VENV_NAME)
	$(VENV_NAME)/bin/pip install -Ur requirements.txt

clean:
	rm -rf $(VENV_NAME)
	make venv

run:
	${PYTHON} cyckei.py

build:
	${PYTHON} -m PyInstaller --onefile --windowed --noconfirm --clean cyckei.spec
