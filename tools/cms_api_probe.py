#!/usr/bin/env python3
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_suffix(".c")
RESULTS = ROOT / "results" / "cms-probe"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    openssl = shutil.which("openssl")
    compiler = shutil.which("cc")
    pkg_config = shutil.which("pkg-config")
    report: dict[str, object] = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "openssl": subprocess.run([openssl, "version", "-a"], capture_output=True, text=True).stdout if openssl else None,
        "source": str(SOURCE.relative_to(ROOT)),
        "results": [],
    }
    if not all((openssl, compiler, pkg_config)):
        report["status"] = "skipped"
        report["reason"] = "openssl, cc, and pkg-config are required"
    else:
        with tempfile.TemporaryDirectory(prefix="pqc-rpki-cms-api-probe-") as name:
            directory = Path(name)
            executable = directory / "cms-api-probe"
            flags = subprocess.run([pkg_config, "--cflags", "--libs", "openssl"], check=True, capture_output=True, text=True).stdout.split()
            compile_command = [compiler, "-O2", "-Wall", "-Wextra", "-Werror", str(SOURCE), "-o", str(executable), *flags]
            subprocess.run(compile_command, check=True, capture_output=True, text=True)
            key = directory / "key.pem"
            cert = directory / "cert.pem"
            content = directory / "content.der"
            content.write_bytes(b"ML-DSA CMS API probe")
            subprocess.run([openssl, "genpkey", "-algorithm", "ML-DSA-65", "-out", str(key)], check=True, capture_output=True)
            subprocess.run([openssl, "req", "-new", "-x509", "-key", str(key), "-subj", "/CN=CMS API probe", "-days", "1", "-out", str(cert)], check=True, capture_output=True)
            rows = []
            for mode in ("default", "sha512"):
                output = directory / f"{mode}.der"
                command = [str(executable), mode, str(key), str(cert), str(content), "1.2.840.113549.1.9.16.1.24", str(output)]
                process = subprocess.run(command, capture_output=True, text=True)
                log = (process.stdout + process.stderr).strip()
                (RESULTS / f"{mode}.log").write_text(log + ("\n" if log else ""))
                rows.append({
                    "mode": mode,
                    "status": "confirmed" if process.returncode == 0 else "blocked",
                    "returncode": process.returncode,
                    "output_bytes": output.stat().st_size if output.exists() else None,
                    "command": ["$TMPDIR/cms-api-probe", mode, "$TMPDIR/key.pem", "$TMPDIR/cert.pem", "$TMPDIR/content.der", "1.2.840.113549.1.9.16.1.24", "$TMPDIR/output.der"],
                    "error": log,
                })
            report["status"] = "confirmed"
            report["compile_command"] = ["cc", "-O2", "-Wall", "-Wextra", "-Werror", "tools/cms_api_probe.c", "-o", "$TMPDIR/cms-api-probe", "$(pkg-config --cflags --libs openssl)"]
            report["results"] = rows
    (RESULTS / "cms-api-probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = ["# OpenSSL ML-DSA CMS API Probe", "", "> EXPERIMENTAL / NOT FOR PRODUCTION", ""]
    for row in report.get("results", []):
        lines.append(f"- `{row['mode']}`: **{row['status']}** (return code {row['returncode']})")
    (RESULTS / "cms-api-probe.md").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
