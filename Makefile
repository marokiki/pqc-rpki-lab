.PHONY: all composite-100k exact-100k review-evidence test install-optional-pqc clean

all:
	./tools/run_all.sh

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

review-evidence:
	PQC_RPKI_RESULTS_DIR=results/review-2026-06 PYTHONPATH=src python3 benchmarks/primitive_bench.py
	PYTHONPATH=src python3 benchmarks/bulk_signing.py
	PQC_RPKI_RESULTS_DIR=results/review-2026-06 PYTHONPATH=src python3 benchmarks/repository_impact.py

exact-100k:
	PYTHONPATH=src python3 benchmarks/exact_100k.py --iterations 100000

composite-100k:
	PYTHONPATH=src .venv/bin/python benchmarks/composite_100k.py --iterations 100000

install-optional-pqc:
	./tools/install_optional_pqc.sh --allow-network

clean:
	rm -f results/*.csv results/*.json results/*.md results/tool-versions.txt
	rm -rf results/tables
	find results/figures -mindepth 1 ! -name README.md -delete 2>/dev/null || true
