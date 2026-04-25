.PHONY: setup synthetic public dune demo clean-data

PYTHON ?= python3
VENV := .venv
VPY := $(VENV)/bin/python

setup:
	$(PYTHON) -m venv $(VENV)
	$(VPY) -m pip install --upgrade pip
	$(VPY) -m pip install -e ".[dash,dev]"

synthetic: setup
	$(VPY) -m src.pipeline

public: setup
	$(VPY) -m src.pipeline_public --refresh

dune: setup
	$(VPY) -m src.pipeline_dune

demo: synthetic
	$(VPY) -m streamlit run src/viz/dashboard.py

clean-data:
	rm -f data/processed/*.parquet data/synthetic/*.parquet
