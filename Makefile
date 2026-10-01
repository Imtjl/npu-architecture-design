PYTHON ?= python3

.PHONY: all model report clean

all: report

model:
	$(PYTHON) tools/processor_timing_model.py

report: model
	$(PYTHON) tools/build_report.py

clean:
	rm -rf build tools/__pycache__
