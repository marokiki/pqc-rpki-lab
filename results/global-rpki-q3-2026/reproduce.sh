#!/bin/sh
# Run on a host with the existing OpenSSL/Composite backend (e.g. ssh pqc).
# Raw source data stays outside tracked results. No I-D or old evidence is edited.
set -eu
: "${PQC_GLOBAL_WORK:?Set a NEW scratch directory with at least 8 GB free}"
: "${PQC_GLOBAL_OPENSSL:?Set the existing OpenSSL 3.6 executable}"
: "${PQC_COMPOSITE_PROVIDER_MODULE:?Set the existing Composite provider module}"
: "${OPENSSL_CONF:?Use experiments/openssl-composite.cnf}"
# Set LD_LIBRARY_PATH for the existing OpenSSL build if required.
TASK=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$TASK/../.." && pwd)
OUT="$PQC_GLOBAL_WORK/output"
mkdir -p "$OUT" "$PQC_GLOBAL_WORK/inputs"
for name in Global_RPKI_Report_2026_Q3.pdf Global_RPKI_Report_2026_Q3-zenodo.pdf; do
    if [ -f "$TASK/sources/$name" ] && [ ! -e "$PQC_GLOBAL_WORK/inputs/$name" ]; then
        cp "$TASK/sources/$name" "$PQC_GLOBAL_WORK/inputs/$name"
    fi
done
python3 "$TASK/fetch_sources.py" --network --snapshot --directory "$PQC_GLOBAL_WORK/inputs"
mkdir -p "$OUT/sources"
cp "$PQC_GLOBAL_WORK/inputs/Global_RPKI_Report_2026_Q3.pdf" "$PQC_GLOBAL_WORK/inputs/Global_RPKI_Report_2026_Q3-zenodo.pdf" "$OUT/sources/"
python3 "$TASK/extract_report.py" "$PQC_GLOBAL_WORK/inputs/Global_RPKI_Report_2026_Q3.pdf" --out "$OUT/sources"
PYTHONPATH="$REPO/src" python3 "$TASK/collect_measurements.py" --openssl "$PQC_GLOBAL_OPENSSL" --work "$PQC_GLOBAL_WORK/measurements" --out "$OUT"
python3 "$TASK/validate_measurements.py" --openssl "$PQC_GLOBAL_OPENSSL" --fixtures "$OUT/measurements" --out "$OUT/measurement-verification.json"
python3 "$TASK/calibrate_archive.py" "$PQC_GLOBAL_WORK/inputs/rpki-20260930T234958Z.tgz" --out "$OUT/archive-header-calibration.json"
python3 "$TASK/evaluate.py" snapshot "$PQC_GLOBAL_WORK/inputs/rpki-20260930T234958Z.tgz" --out "$OUT"
python3 "$TASK/diagnose_inventory.py" "$OUT/snapshot-inventory.jsonl.gz" --out "$OUT/snapshot-diagnostics.json"
rsync -a --timeout=60 rsync://rrdp.rpkiviews.org/data/2026/09/20260930.log "$PQC_GLOBAL_WORK/inputs/20260930.log"
python3 "$TASK/fetch_rrdp_day.py" --log "$PQC_GLOBAL_WORK/inputs/20260930.log" --out "$PQC_GLOBAL_WORK/trace" --expected-log-sha256 b72da97901cb3fca9bd47dfa6e987b805795a35cb27c5088e9bb4cc5631c0957
python3 "$TASK/evaluate.py" rrdp "$PQC_GLOBAL_WORK/trace/xml" --out "$OUT/rrdp-summary.json"
cp "$PQC_GLOBAL_WORK/trace/trace-selection.json" "$OUT/trace-selection.json"
# Use the retained original snapshot cache when pinned origin URLs have expired.
# A fresh live capture is a distinct dated cohort, not an exact reproduction.
SNAP_CACHE="${PQC_GLOBAL_SNAPSHOT_CACHE:-$PQC_GLOBAL_WORK/live-snapshots}"
python3 "$TASK/fetch_rrdp_snapshots.py" --network --replay-manifest "$TASK/rrdp-snapshot-selection.json" --out "$SNAP_CACHE"
python3 "$TASK/verify_snapshot_replay.py" --directory "$SNAP_CACHE/xml" --expected "$TASK/rrdp-snapshot-summary.json" --out "$OUT/rrdp-snapshot-replay-verification.json"
cp "$TASK/rrdp-snapshot-summary.json" "$OUT/rrdp-snapshot-summary.json"
cp "$TASK/rrdp-snapshot-selection.json" "$OUT/rrdp-snapshot-selection.json"
cp -R "$TASK/sources/rrdp-snapshot-notifications" "$OUT/sources/"
cp "$TASK/sources/historical-snapshot-probe.json" "$TASK/sources/ripe-20260930-end-notification.xml" "$OUT/sources/"
python3 "$TASK/build_report.py" --directory "$OUT"
python3 "$TASK/validate_results.py" --directory "$OUT"
printf '%s\n' "Results: $OUT"
