.PHONY: all certificate-sizes ccr-comparison cms-api-probe composite-100k composite-e2e composite-e2e-rp-matrix composite-e2e-negative composite-e2e-benchmark draft-composite-100k exact-100k key-roll local-validation message-sweep mixed-tree object-benchmarks pre-publication regenerate-reports review-evidence routinator-krill-interop routinator-krill-scan rpki-objects test validator-container-probe verify-artifacts install-optional-pqc clean

COMPOSITE_OPENSSL ?= $(CURDIR)/local/build/openssl-3.6.2-install/bin/openssl
COMPOSITE_OPENSSL_LIBDIR ?= $(CURDIR)/local/build/openssl-3.6.2-install/lib64
COMPOSITE_PROVIDER_MODULE ?= $(CURDIR)/local/build/composite-provider/composite.so
COMPOSITE_OPENSSL_CONF ?= $(CURDIR)/experiments/openssl-composite.cnf
COMPOSITE_ENV = LD_LIBRARY_PATH="$(COMPOSITE_OPENSSL_LIBDIR):$${LD_LIBRARY_PATH}" OPENSSL_CONF="$(COMPOSITE_OPENSSL_CONF)" PQC_COMPOSITE_PROVIDER_MODULE="$(COMPOSITE_PROVIDER_MODULE)"

all:
	./tools/run_all.sh

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

object-benchmarks:
	PYTHONPATH=src python3 tools/object_benchmarks.py

certificate-sizes:
	PYTHONPATH=src python3 tools/object_generation_feasibility.py

mixed-tree:
	PYTHONPATH=src python3 tools/mixed_tree_fixture.py

ccr-comparison:
	PYTHONPATH=src python3 tools/ccr_comparison.py

routinator-krill-scan:
	PYTHONPATH=src python3 tools/routinator_krill_scan.py

routinator-krill-interop:
	PYTHONPATH=src python3 tools/routinator_krill_interop.py

rpki-objects:
	PYTHONPATH=src python3 tools/generate_rpki_objects.py

composite-e2e:
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/composite_e2e.py \
		--openssl "$(COMPOSITE_OPENSSL)"

composite-e2e-rp-matrix: composite-e2e
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/composite_rp_matrix.py \
		--unmodified local/build/rpki-client-baseline/src/rpki-client \
		--patched local/build/rpki-client-composite/src/rpki-client

composite-e2e-negative: composite-e2e
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/composite_negative_tests.py \
		--openssl "$(COMPOSITE_OPENSSL)" \
		--rpki-client local/build/rpki-client-composite/src/rpki-client

composite-e2e-benchmark: composite-e2e
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/composite_e2e_benchmark.py \
		--generation-repetitions 100 \
		--validation-repetitions 1000 \
		--openssl "$(COMPOSITE_OPENSSL)" \
		--baseline-rpki-client local/build/rpki-client-baseline/src/rpki-client \
		--patched-rpki-client local/build/rpki-client-composite/src/rpki-client

cms-api-probe:
	PYTHONPATH=src python3 tools/cms_api_probe.py

key-roll: rpki-objects
	PYTHONPATH=src python3 tools/key_roll_benchmark.py

local-validation: rpki-objects
	PYTHONPATH=src python3 tools/local_object_validation.py

regenerate-reports: object-benchmarks mixed-tree ccr-comparison routinator-krill-scan routinator-krill-interop cms-api-probe rpki-objects key-roll local-validation
	PYTHONPATH=src python3 tools/generate_report.py

pre-publication:
	PYTHONPATH=src python3 tools/check_required_artifacts.py
	PYTHONPATH=src python3 tools/pre_publication_check.py

verify-artifacts:
	PYTHONPATH=src python3 tools/check_required_artifacts.py

review-evidence:
	PQC_RPKI_RESULTS_DIR=results/review-2026-06 PYTHONPATH=src python3 benchmarks/primitive_bench.py
	PYTHONPATH=src python3 benchmarks/bulk_signing.py
	PQC_RPKI_RESULTS_DIR=results/review-2026-06 PYTHONPATH=src python3 benchmarks/repository_impact.py

exact-100k:
	PYTHONPATH=src python3 benchmarks/exact_100k.py --iterations 100000

message-sweep:
	PYTHONPATH=src python3 benchmarks/message_sweep.py --iterations 100000 --repetitions 10

validator-container-probe: rpki-objects
	PYTHONPATH=src python3 tools/validator_container_probe.py

composite-100k:
	PYTHONPATH=src .venv/bin/python benchmarks/composite_100k.py --iterations 100000

draft-composite-100k:
	PYTHONPATH=src python3 benchmarks/draft_composite_100k.py --iterations 100000

install-optional-pqc:
	./tools/install_optional_pqc.sh --allow-network

clean:
	rm -f results/*.csv results/*.json results/*.md results/tool-versions.txt
	rm -rf results/tables
	rm -rf results/object-benchmarks results/mixed-tree results/ccr-comparison results/routinator-krill results/validator-interoperability results/rpki-objects results/key-roll results/local-validation
	rm -rf results/cms-probe results/cms-generation results/validator-probe results/message-sweep
	find results/figures -mindepth 1 ! -name README.md -delete 2>/dev/null || true
