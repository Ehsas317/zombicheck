.PHONY: test source demo

test:
	python3 -m pytest tests -v

source:
	python3 zombicheck.py source --out rows.csv --limit 600

demo:
	python3 zombicheck.py check examples/rows-full.csv -o examples/zombie-report.csv --limit 600
