.PHONY: all test install-optional-pqc clean

all:
	./tools/run_all.sh

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

install-optional-pqc:
	./tools/install_optional_pqc.sh --allow-network

clean:
	rm -rf results/*.csv results/*.json results/*.md results/tool-versions.txt results/tables results/figures
