#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -n "${PQC_RPKI_PYTHON:-}" ]]; then
  PYTHON="$PQC_RPKI_PYTHON"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="python3"
fi
export PQC_RPKI_PYTHON="$PYTHON"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
if [[ -d "$ROOT/.local/oqs" ]]; then
  export OQS_INSTALL_PATH="$ROOT/.local/oqs"
  export DYLD_LIBRARY_PATH="$ROOT/.local/oqs/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
  export LD_LIBRARY_PATH="$ROOT/.local/oqs/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

mkdir -p "$ROOT/results/tables" "$ROOT/results/figures"
"$ROOT/tools/check_versions.sh" > "$ROOT/results/tool-versions.txt"
"$PYTHON" "$ROOT/benchmarks/primitive_bench.py"
"$PYTHON" "$ROOT/tools/object_generation_feasibility.py"
"$PYTHON" "$ROOT/benchmarks/repository_impact.py"
if [[ -n "${PQC_RPKI_CACHE:-}" ]]; then
  "$PYTHON" "$ROOT/tools/cache_stats.py" --cache "$PQC_RPKI_CACHE"
else
  "$PYTHON" "$ROOT/tools/cache_stats.py"
fi
"$PYTHON" "$ROOT/tools/validator_probe.py"
"$PYTHON" "$ROOT/tools/vrp_equivalence.py"
"$PYTHON" "$ROOT/tools/migration_scenarios.py"
"$PYTHON" "$ROOT/tools/literature_comparison.py"
"$PYTHON" "$ROOT/tools/generate_report.py"
"$PYTHON" "$ROOT/tools/generate_support_docs.py"
"$PYTHON" -m unittest discover -s "$ROOT/tests" -v
echo "pqc-rpki-lab: completed without network access"
