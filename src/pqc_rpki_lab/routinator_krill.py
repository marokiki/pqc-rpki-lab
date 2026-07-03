from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROUTINATOR_ENV = "PQC_RPKI_ROUTINATOR_SRC"
KRILL_ENV = "PQC_RPKI_KRILL_SRC"
ROUTINATOR_BIN_ENV = "PQC_RPKI_ROUTINATOR_BIN"
KRILL_BIN_ENV = "PQC_RPKI_KRILL_BIN"


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    role: str
    source_env: str
    binary_env: str
    default_binary: str
    extension_points: tuple[dict[str, str], ...]


ROUTINATOR_SPEC = ProjectSpec(
    name="Routinator",
    role="validator",
    source_env=ROUTINATOR_ENV,
    binary_env=ROUTINATOR_BIN_ENV,
    default_binary="routinator",
    extension_points=(
        {"area": "algorithm-registry", "need": "Register ML-DSA and candidate composite AlgorithmIdentifiers."},
        {"area": "x509-verification", "need": "Verify certificate SPKI and signature algorithms across CA boundaries."},
        {"area": "cms-verification", "need": "Verify RFC 6488 SignedData with PQC signature algorithms."},
        {"area": "manifest-consistency", "need": "Reject products outside the Manifest signer issuing context."},
        {"area": "mixed-tree", "need": "Allow algorithm transition at CA boundaries without per-object mixing."},
        {"area": "vrp-ccr-export", "need": "Export VRPs or CCR-compatible ROAPayloadState for semantic comparison."},
    ),
)

KRILL_SPEC = ProjectSpec(
    name="Krill",
    role="ca-publication",
    source_env=KRILL_ENV,
    binary_env=KRILL_BIN_ENV,
    default_binary="krill",
    extension_points=(
        {"area": "ca-key-algorithm", "need": "Abstract CA key algorithms beyond RSA."},
        {"area": "child-ca-issuance", "need": "Issue child certificates whose SPKI algorithm differs from issuer signature algorithm."},
        {"area": "ee-certificate", "need": "Generate RFC 6488 EE certificates for PQC object signers."},
        {"area": "cms-signing", "need": "Sign Manifest and ROA CMS objects with selected algorithm suite."},
        {"area": "publication", "need": "Publish RSA baseline, PQC branch, and mixed-tree repositories reproducibly."},
        {"area": "transport-size", "need": "Measure RRDP snapshot, RRDP delta, and rsync output growth."},
    ),
)

PROJECTS = (ROUTINATOR_SPEC, KRILL_SPEC)


def cargo_package_name(cargo_toml: Path) -> str:
    if not cargo_toml.exists():
        return ""
    in_package = False
    for line in cargo_toml.read_text(errors="replace").splitlines():
        stripped = line.strip()
        if stripped == "[package]":
            in_package = True
            continue
        if stripped.startswith("[") and stripped != "[package]":
            in_package = False
        if in_package and stripped.startswith("name"):
            _, value = stripped.split("=", 1)
            return value.strip().strip('"')
    return ""


def git_head(path: Path) -> str:
    git_dir = path / ".git"
    if not git_dir.exists():
        return ""
    try:
        process = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""
    return process.stdout.strip()


def likely_files(path: Path, patterns: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    if not path.exists():
        return matches
    for file in path.rglob("*"):
        if len(matches) >= 40:
            break
        if not file.is_file():
            continue
        relative = file.relative_to(path).as_posix()
        lowered = relative.lower()
        if any(pattern in lowered for pattern in patterns):
            matches.append(relative)
    return matches


def scan_project(spec: ProjectSpec, environment: dict[str, str] | None = None) -> dict[str, object]:
    environment = environment or os.environ
    source_value = environment.get(spec.source_env, "")
    if not source_value:
        return {
            "project": spec.name,
            "role": spec.role,
            "status": "skipped",
            "source_env": spec.source_env,
            "source_path": "",
            "reason": f"{spec.source_env} is not set",
            "extension_points": list(spec.extension_points),
            "likely_files": [],
        }
    path = Path(source_value)
    if not path.exists():
        return {
            "project": spec.name,
            "role": spec.role,
            "status": "blocked",
            "source_env": spec.source_env,
            "source_path": str(path),
            "reason": "configured source path does not exist",
            "extension_points": list(spec.extension_points),
            "likely_files": [],
        }
    cargo = path / "Cargo.toml"
    patterns = (
        "crypto", "cert", "certificate", "cms", "manifest", "roa", "validation",
        "repository", "publication", "rrdp", "rsync", "payload", "signed",
    )
    return {
        "project": spec.name,
        "role": spec.role,
        "status": "confirmed" if cargo.exists() else "blocked",
        "source_env": spec.source_env,
        "source_path": str(path),
        "reason": "" if cargo.exists() else "Cargo.toml not found",
        "cargo_package": cargo_package_name(cargo),
        "git_head": git_head(path),
        "extension_points": list(spec.extension_points),
        "likely_files": likely_files(path, patterns),
    }


def extension_map() -> dict[str, object]:
    return {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": "public extension map; no upstream source vendored",
        "projects": [
            {
                "project": spec.name,
                "role": spec.role,
                "source_env": spec.source_env,
                "binary_env": spec.binary_env,
                "suggested_local_path": f"local/upstream/{spec.name.lower()}/",
                "extension_points": list(spec.extension_points),
            }
            for spec in PROJECTS
        ],
    }


def binary_probe(spec: ProjectSpec, environment: dict[str, str] | None = None) -> dict[str, object]:
    environment = environment or os.environ
    binary = environment.get(spec.binary_env, "")
    if not binary:
        return {
            "project": spec.name,
            "role": spec.role,
            "binary_env": spec.binary_env,
            "binary": "",
            "status": "skipped",
            "reason": f"{spec.binary_env} is not set",
            "version": "",
        }
    try:
        process = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "project": spec.name,
            "role": spec.role,
            "binary_env": spec.binary_env,
            "binary": binary,
            "status": "blocked",
            "reason": str(error),
            "version": "",
        }
    text = (process.stdout or process.stderr).strip()
    return {
        "project": spec.name,
        "role": spec.role,
        "binary_env": spec.binary_env,
        "binary": binary,
        "status": "confirmed" if process.returncode == 0 else "blocked",
        "reason": "" if process.returncode == 0 else text,
        "version": text.splitlines()[0] if text else "",
    }


def default_interop_layers(status: str, reason: str) -> dict[str, str]:
    return {
        "parser": status,
        "signature": status,
        "certificate_path": status,
        "crl": status,
        "manifest": status,
        "roa": status,
        "vrp_output": status,
        "reason": reason,
    }
