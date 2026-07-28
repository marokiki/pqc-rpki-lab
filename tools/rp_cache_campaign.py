#!/usr/bin/env python3
"""Measure fresh, unchanged-cache, and one-ROA-update RP validation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR))
from krill_experimental_validate import (
    expected_vrps,
    extract_routinator_vrps,
    prepare_fixture,
)
from krill_scale_campaign import (
    environment_summary,
    parse_time,
    time_summary,
)
from pqc_rpki_lab.workspace import reset_generated_directory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK = ROOT / "local" / "rp-cache-campaign"
DEFAULT_RESULT = (
    ROOT / "results" / "scaled-corpus"
    / "rp-cache-regimes.json"
)


def reset(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def run_process(
    command: list[str],
    env: dict[str, str],
    log: Path,
    *,
    timing: Path | None = None,
) -> dict[str, int | float] | None:
    log.parent.mkdir(parents=True, exist_ok=True)
    actual = command
    if timing is not None:
        actual = ["/usr/bin/time", "-v", "-o", str(timing), *command]
    with log.open("w") as output:
        process = subprocess.run(
            actual,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )
    if process.returncode:
        raise RuntimeError(
            f"command failed ({process.returncode}); see {log}"
        )
    return parse_time(timing) if timing is not None else None


def rpki_cache(fixture: Path, cache: Path) -> None:
    reset(cache)
    (cache / "localhost").mkdir()
    (cache / "ta" / "testbed").mkdir(parents=True)
    shutil.copytree(fixture / "ta", cache / "localhost" / "ta")
    shutil.copytree(fixture / "repo", cache / "localhost" / "repo")
    shutil.copyfile(
        fixture / "ta" / "ta.cer",
        cache / "ta" / "testbed" / "ta.cer",
    )


def rpki_overlay(fixture: Path, cache: Path) -> None:
    target = cache / "localhost" / "repo"
    shutil.rmtree(target)
    shutil.copytree(fixture / "repo", target)


def rpki_vrps(output: Path) -> list[dict[str, object]]:
    with (output / "csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return sorted(
        [
            {
                "asn": row["ASN"],
                "prefix": row["IP Prefix"],
                "max_length": int(row["Max Length"]),
            }
            for row in rows
        ],
        key=lambda item: (item["prefix"], item["asn"]),
    )


def run_rpki(
    binary: Path,
    fixture: Path,
    cache: Path,
    target: Path,
    expected: list[dict[str, object]],
    env: dict[str, str],
    *,
    timed: bool,
) -> dict[str, int | float] | None:
    output = target / "output"
    reset(output)
    timing = target / "time.txt" if timed else None
    measured = run_process(
        [
            str(binary),
            "-x",
            "-n",
            "-d",
            str(cache),
            "-t",
            str(fixture / "testbed.tal"),
            "-j",
            "-c",
            "-vv",
            str(output),
        ],
        env,
        target / "rpki-client.log",
        timing=timing,
    )
    if rpki_vrps(output) != expected:
        raise RuntimeError(f"rpki-client VRP mismatch in {target}")
    return measured


def wait_port(process: subprocess.Popen[str], port: int) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("rsync daemon exited")
        with socket.socket() as sock:
            sock.settimeout(0.1)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise RuntimeError("rsync daemon did not become ready")


def serve_fixture(fixture: Path, served: Path) -> None:
    reset(served)
    shutil.copytree(fixture / "ta", served / "ta")
    shutil.copytree(fixture / "repo", served / "repo")


def run_routinator(
    binary: Path,
    fixture: Path,
    cache: Path,
    target: Path,
    expected: list[dict[str, object]],
    env: dict[str, str],
    wrapper: Path,
    *,
    timed: bool,
) -> dict[str, int | float] | None:
    target.mkdir(parents=True, exist_ok=True)
    output = target / "vrps.json"
    if output.exists():
        output.unlink()
    tal_dir = target / "tals"
    reset(tal_dir)
    shutil.copyfile(fixture / "testbed.tal", tal_dir / "testbed.tal")
    config = target / "routinator.conf"
    config.write_text(
        f'repository-dir = "{cache}"\nno-rir-tals = true\n'
    )
    timing = target / "time.txt" if timed else None
    measured = run_process(
        [
            str(binary),
            "--config",
            str(config),
            "-vv",
            "--repository-dir",
            str(cache),
            "--no-rir-tals",
            "--extra-tals-dir",
            str(tal_dir),
            "--disable-rrdp",
            "--allow-dubious-hosts",
            "--log-repository-issues",
            "--rsync-command",
            str(wrapper),
            "vrps",
            "--complete",
            "--format",
            "json",
            "--output",
            str(output),
        ],
        env,
        target / "routinator.log",
        timing=timing,
    )
    parsed = json.loads(output.read_text()) if output.exists() else {}
    if extract_routinator_vrps(parsed) != expected:
        raise RuntimeError(f"Routinator VRP mismatch in {target}")
    return measured


def changed_objects(
    initial: Path, updated: Path
) -> dict[str, int]:
    left = {
        path.relative_to(initial): hashlib.sha256(path.read_bytes()).digest()
        for path in initial.rglob("*")
        if path.is_file()
    }
    right = {
        path.relative_to(updated): hashlib.sha256(path.read_bytes()).digest()
        for path in updated.rglob("*")
        if path.is_file()
    }
    names = set(left) | set(right)
    changed = [name for name in names if left.get(name) != right.get(name)]
    return {
        "changed_file_count": len(changed),
        "initial_changed_bytes": sum(
            (initial / name).stat().st_size
            for name in changed
            if (initial / name).is_file()
        ),
        "updated_changed_bytes": sum(
            (updated / name).stat().st_size
            for name in changed
            if (updated / name).is_file()
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--krill-output", type=Path, required=True)
    parser.add_argument("--rpki-client", type=Path, required=True)
    parser.add_argument("--routinator", type=Path, required=True)
    parser.add_argument("--roa-count", type=int, required=True)
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--port", type=int, default=27873)
    args = parser.parse_args()
    if args.roa_count < 1 or args.repetitions < 2:
        raise SystemExit("ROA count must be positive and repetitions at least 2")

    work = args.work.resolve()
    reset_generated_directory(work, allowed_root=ROOT / "local")
    fixtures = work / "fixtures"
    initial = fixtures / "initial"
    updated = fixtures / "updated"
    prepare_fixture(args.krill_output.resolve() / "composite", initial)
    prepare_fixture(
        args.krill_output.resolve() / "composite-updated", updated
    )
    initial_expected = expected_vrps(args.roa_count)
    updated_expected = expected_vrps(
        args.roa_count, first_prefix="192.0.2.0/25"
    )
    env = os.environ.copy()
    env["PQC_RPKI_EXPERIMENTAL"] = "1"

    rpki_rows: dict[str, list[dict[str, int | float]]] = {
        "fresh_validator_cache": [],
        "unchanged_repository_cache": [],
        "one_roa_update": [],
    }
    rpki_root = work / "rpki-client"
    for repetition in range(1, args.repetitions + 1):
        cache = rpki_root / "fresh" / f"{repetition:04d}" / "cache"
        rpki_cache(initial, cache)
        row = run_rpki(
            args.rpki_client.resolve(),
            initial,
            cache,
            rpki_root / "fresh" / f"{repetition:04d}",
            initial_expected,
            env,
            timed=True,
        )
        assert row is not None
        rpki_rows["fresh_validator_cache"].append(row)

    warm_cache = rpki_root / "warm" / "cache"
    rpki_cache(initial, warm_cache)
    run_rpki(
        args.rpki_client.resolve(),
        initial,
        warm_cache,
        rpki_root / "warm" / "prewarm",
        initial_expected,
        env,
        timed=False,
    )
    for repetition in range(1, args.repetitions + 1):
        row = run_rpki(
            args.rpki_client.resolve(),
            initial,
            warm_cache,
            rpki_root / "warm" / f"{repetition:04d}",
            initial_expected,
            env,
            timed=True,
        )
        assert row is not None
        rpki_rows["unchanged_repository_cache"].append(row)

    for repetition in range(1, args.repetitions + 1):
        target = rpki_root / "incremental" / f"{repetition:04d}"
        cache = target / "cache"
        rpki_cache(initial, cache)
        run_rpki(
            args.rpki_client.resolve(),
            initial,
            cache,
            target / "prevalidate",
            initial_expected,
            env,
            timed=False,
        )
        rpki_overlay(updated, cache)
        row = run_rpki(
            args.rpki_client.resolve(),
            updated,
            cache,
            target / "updated",
            updated_expected,
            env,
            timed=True,
        )
        assert row is not None
        rpki_rows["one_roa_update"].append(row)

    served = work / "routinator" / "served"
    serve_fixture(initial, served)
    daemon_config = work / "routinator" / "rsyncd.conf"
    daemon_config.write_text(
        "use chroot = false\nread only = true\n"
        f"[ta]\npath = {served / 'ta'}\n"
        f"[repo]\npath = {served / 'repo'}\n"
    )
    wrapper = work / "routinator" / "rsync-wrapper.py"
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f"port = {args.port}\n"
        "args = [arg.replace('rsync://localhost/', "
        "f'rsync://127.0.0.1:{port}/') for arg in sys.argv[1:]]\n"
        "os.execv('/usr/bin/rsync', ['rsync', *args])\n"
    )
    wrapper.chmod(0o700)
    daemon = subprocess.Popen(
        [
            "/usr/bin/rsync",
            "--daemon",
            "--no-detach",
            f"--port={args.port}",
            f"--config={daemon_config}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )
    routinator_rows: dict[str, list[dict[str, int | float]]] = {
        "fresh_validator_cache": [],
        "unchanged_repository_cache": [],
        "one_roa_update": [],
    }
    try:
        wait_port(daemon, args.port)
        routinator_root = work / "routinator"
        for repetition in range(1, args.repetitions + 1):
            serve_fixture(initial, served)
            target = routinator_root / "fresh" / f"{repetition:04d}"
            cache = target / "cache"
            cache.mkdir(parents=True)
            row = run_routinator(
                args.routinator.resolve(),
                initial,
                cache,
                target,
                initial_expected,
                env,
                wrapper,
                timed=True,
            )
            assert row is not None
            routinator_rows["fresh_validator_cache"].append(row)

        serve_fixture(initial, served)
        warm_target = routinator_root / "warm"
        warm_cache = warm_target / "cache"
        warm_cache.mkdir(parents=True)
        run_routinator(
            args.routinator.resolve(),
            initial,
            warm_cache,
            warm_target / "prewarm",
            initial_expected,
            env,
            wrapper,
            timed=False,
        )
        for repetition in range(1, args.repetitions + 1):
            target = warm_target / f"{repetition:04d}"
            row = run_routinator(
                args.routinator.resolve(),
                initial,
                warm_cache,
                target,
                initial_expected,
                env,
                wrapper,
                timed=True,
            )
            assert row is not None
            routinator_rows["unchanged_repository_cache"].append(row)

        for repetition in range(1, args.repetitions + 1):
            target = routinator_root / "incremental" / f"{repetition:04d}"
            cache = target / "cache"
            cache.mkdir(parents=True)
            serve_fixture(initial, served)
            run_routinator(
                args.routinator.resolve(),
                initial,
                cache,
                target / "prevalidate",
                initial_expected,
                env,
                wrapper,
                timed=False,
            )
            serve_fixture(updated, served)
            row = run_routinator(
                args.routinator.resolve(),
                updated,
                cache,
                target / "updated",
                updated_expected,
                env,
                wrapper,
                timed=True,
            )
            assert row is not None
            routinator_rows["one_roa_update"].append(row)
    finally:
        daemon.terminate()
        daemon.wait(timeout=5)

    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "single-parent, single-child local-rsync cache-regime "
            "measurement; OS page cache is uncontrolled and rpki-client "
            "does not retain a parsed validation cache between processes"
        ),
        "roa_count": args.roa_count,
        "repetitions_per_regime": args.repetitions,
        "regimes": {
            "fresh_validator_cache": (
                "new RP repository/cache directory for every validation"
            ),
            "unchanged_repository_cache": (
                "same repository/cache directory after one unmeasured run"
            ),
            "one_roa_update": (
                "initial Composite state validated once, then one ROA "
                "replaced and the updated state validated"
            ),
        },
        "environment": environment_summary(
            env,
            ROOT / "local" / "build",
            args.rpki_client.resolve(),
            args.routinator.resolve(),
        ),
        "update": changed_objects(initial / "repo", updated / "repo"),
        "rpki_client": {
            name: time_summary(rows) for name, rows in rpki_rows.items()
        },
        "routinator": {
            name: time_summary(rows)
            for name, rows in routinator_rows.items()
        },
        "all_expected_vrps_observed": True,
        "contains_private_keys": False,
        "contains_raw_objects": False,
        "contains_absolute_paths": False,
    }
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if re.search(r'/(?:home|Users)/', text):
        raise RuntimeError("sanitized summary contains an absolute user path")
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
