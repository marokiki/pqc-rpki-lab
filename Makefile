.PHONY: all test install-optional-pqc clean

all:
	./tools/run_all.sh

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

install-optional-pqc:
	./tools/install_optional_pqc.sh --allow-network

clean:
	rm -f results/*.csv results/*.json results/*.md results/tool-versions.txt
	rm -rf results/tables
	find results/figures -mindepth 1 ! -name README.md -delete 2>/dev/null || true
