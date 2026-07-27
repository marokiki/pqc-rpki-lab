.PHONY: all certificate-sizes ccr-comparison cms-api-probe composite-100k composite-bootstrap composite-bootstrap-check composite-e2e composite-e2e-rp-matrix composite-e2e-negative composite-e2e-benchmark composite-keygen-benchmark draft-composite-100k exact-100k key-roll krill-experimental-bootstrap krill-experimental-bootstrap-check krill-experimental-build krill-experimental-e2e krill-scaled-e2e krill-scaled-summary local-validation message-sweep mixed-tree object-benchmarks pre-publication public-cache-profile regenerate-reports review-evidence routinator-experimental-bootstrap routinator-experimental-bootstrap-check routinator-experimental-build routinator-experimental-matrix routinator-experimental-negative routinator-krill-interop routinator-krill-scan rpki-objects test validator-container-probe verify-artifacts install-optional-pqc clean

COMPOSITE_OPENSSL ?= $(CURDIR)/local/build/openssl-3.6.2-install/bin/openssl
COMPOSITE_OPENSSL_LIBDIR ?= $(CURDIR)/local/build/openssl-3.6.2-install/lib64
COMPOSITE_PROVIDER_MODULE ?= $(CURDIR)/local/build/composite-provider/composite.so
COMPOSITE_OPENSSL_CONF ?= $(CURDIR)/experiments/openssl-composite.cnf
COMPOSITE_ENV = LD_LIBRARY_PATH="$(COMPOSITE_OPENSSL_LIBDIR):$${LD_LIBRARY_PATH}" OPENSSL_CONF="$(COMPOSITE_OPENSSL_CONF)" PQC_COMPOSITE_PROVIDER_MODULE="$(COMPOSITE_PROVIDER_MODULE)"
RUSTUP_HOME ?= $(CURDIR)/local/build/rustup-home
CARGO_HOME ?= $(CURDIR)/local/build/cargo-home
ROUTINATOR_SOURCE ?= $(CURDIR)/local/upstream/routinator
ROUTINATOR_BIN ?= $(ROUTINATOR_SOURCE)/target/debug/routinator
KRILL_SOURCE ?= $(CURDIR)/local/upstream/krill
KRILL_SCALED_ROOT ?= $(CURDIR)/local/krill-scaled/verified-1000
PQC_RPKI_CACHE ?=
PUBLIC_CACHE_LABEL ?= operator-supplied Routinator cache snapshot
RUST_ENV = RUSTUP_HOME="$(RUSTUP_HOME)" CARGO_HOME="$(CARGO_HOME)" OPENSSL_DIR="$(CURDIR)/local/build/openssl-3.6.2-install" LD_LIBRARY_PATH="$(COMPOSITE_OPENSSL_LIBDIR):$${LD_LIBRARY_PATH}"

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
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/generate_rpki_objects.py \
		--algorithm ml-dsa-65 \
		--output-root local/e2e/rp-matrix-pure \
		--openssl "$(COMPOSITE_OPENSSL)"
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/generate_rpki_objects.py \
		--algorithm composite-mldsa65-p256 \
		--output-root local/e2e/rp-matrix-composite \
		--openssl "$(COMPOSITE_OPENSSL)"
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/generate_rpki_objects.py \
		--algorithm rsa \
		--output-root local/e2e/rp-matrix-rsa \
		--openssl "$(COMPOSITE_OPENSSL)"
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/composite_rp_matrix.py \
		--pure-fixture local/e2e/rp-matrix-pure/testdata/validator/ml-dsa-65 \
		--composite-fixture local/e2e/rp-matrix-composite/testdata/validator/composite-mldsa65-p256 \
		--rsa-fixture local/e2e/rp-matrix-rsa/testdata/validator/rsa \
		--unmodified local/build/rpki-client-baseline/src/rpki-client \
		--patched local/build/rpki-client-composite/src/rpki-client

composite-e2e-negative: composite-e2e
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/generate_rpki_objects.py \
		--algorithm ml-dsa-65 \
		--output-root local/e2e/negative-pure \
		--private-output local/e2e/rp-matrix-private \
		--openssl "$(COMPOSITE_OPENSSL)"
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/composite_negative_tests.py \
		--pure-fixture local/e2e/negative-pure/testdata/validator/ml-dsa-65 \
		--pure-private local/e2e/rp-matrix-private/ml-dsa-65 \
		--openssl "$(COMPOSITE_OPENSSL)" \
		--rpki-client local/build/rpki-client-composite/src/rpki-client

composite-e2e-benchmark: composite-e2e
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/composite_e2e_benchmark.py \
		--generation-repetitions 100 \
		--validation-repetitions 1000 \
		--openssl "$(COMPOSITE_OPENSSL)" \
		--baseline-rpki-client local/build/rpki-client-baseline/src/rpki-client \
		--patched-rpki-client local/build/rpki-client-composite/src/rpki-client

composite-keygen-benchmark:
	$(COMPOSITE_ENV) PYTHONPATH=src python3 tools/keygen_benchmark.py \
		--repetitions 1000 \
		--openssl "$(COMPOSITE_OPENSSL)"

composite-bootstrap:
	./tools/bootstrap_composite_e2e.sh --allow-network

composite-bootstrap-check:
	./tools/bootstrap_composite_e2e.sh --check-only

routinator-experimental-build:
	cd "$(ROUTINATOR_SOURCE)" && $(RUST_ENV) \
		"$(CARGO_HOME)/bin/cargo" build --no-default-features

routinator-experimental-bootstrap:
	./tools/bootstrap_routinator_experimental.sh --allow-network

routinator-experimental-bootstrap-check:
	./tools/bootstrap_routinator_experimental.sh --check-only

routinator-experimental-matrix: composite-e2e-rp-matrix routinator-experimental-build
	$(COMPOSITE_ENV) PYTHONPATH=src python3 \
		tools/routinator_experimental_matrix.py \
		--binary "$(ROUTINATOR_BIN)" \
		--rsa-fixture local/e2e/rp-matrix-rsa/testdata/validator/rsa \
		--pure-fixture local/e2e/rp-matrix-pure/testdata/validator/ml-dsa-65 \
		--composite-fixture local/e2e/rp-matrix-composite/testdata/validator/composite-mldsa65-p256 \
		--mixed-fixture local/e2e/current

routinator-experimental-negative: composite-e2e-negative routinator-experimental-build
	$(COMPOSITE_ENV) PYTHONPATH=src:tools python3 \
		tools/routinator_negative_tests.py --binary "$(ROUTINATOR_BIN)"

krill-experimental-build:
	cd "$(KRILL_SOURCE)" && $(RUST_ENV) \
		"$(CARGO_HOME)/bin/cargo" +1.88.0 build --no-default-features

krill-experimental-bootstrap:
	./tools/bootstrap_krill_experimental.sh --allow-network

krill-experimental-bootstrap-check:
	./tools/bootstrap_krill_experimental.sh --check-only

krill-experimental-e2e: krill-experimental-build
	./tools/run_krill_experimental.sh

krill-scaled-e2e: krill-experimental-build
	./tools/run_krill_scaled_experimental.sh

public-cache-profile:
	test -n "$(PQC_RPKI_CACHE)"
	PYTHONPATH=src python3 tools/profile_public_cache.py \
		--cache "$(PQC_RPKI_CACHE)" \
		--source-label "$(PUBLIC_CACHE_LABEL)"

krill-scaled-summary:
	PYTHONPATH=src python3 tools/summarize_scaled_krill.py \
		--scaled-root "$(KRILL_SCALED_ROOT)" \
		--reliability local/krill-reliability/results.tsv \
		--roa-count 1000

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
	PYTHONPATH=src python3 tools/check_composite_evidence.py
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
