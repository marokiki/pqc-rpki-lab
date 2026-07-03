#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from pqc_rpki_lab.result_io import markdown_table, write_json
from pqc_rpki_lab.routinator_krill import PROJECTS, extension_map, scan_project

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "routinator-krill"


def main() -> None:
    scans = [scan_project(spec) for spec in PROJECTS]
    ext_map = extension_map()
    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": "read-only scanner; no upstream source is copied into this repository",
        "scan_results": scans,
        "extension_map": ext_map,
    }
    write_json(RESULTS / "extension-map.json", ext_map)
    write_json(RESULTS / "source-scan.json", document)
    rows = [
        {
            "project": row["project"],
            "role": row["role"],
            "status": row["status"],
            "source_env": row["source_env"],
            "source_path": row["source_path"],
            "cargo_package": row.get("cargo_package", ""),
            "git_head": row.get("git_head", ""),
            "likely_file_count": len(row.get("likely_files", [])),
            "reason": row["reason"],
        }
        for row in scans
    ]
    (RESULTS / "source-scan.md").write_text(
        "# Routinator/Krill Source Scan\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "The scanner is read-only. Configure source paths with "
        "`PQC_RPKI_ROUTINATOR_SRC` and `PQC_RPKI_KRILL_SRC`; suggested local "
        "checkouts live under ignored `local/upstream/`.\n\n"
        + markdown_table(rows, [(key, key.replace("_", " ").title()) for key in rows[0]]) + "\n"
    )
    patch_rows = [
        {
            "project": project["project"],
            "area": point["area"],
            "patch_unit": point["need"],
            "upstream_source": "external checkout; not vendored",
            "status": "planned",
        }
        for project in ext_map["projects"]
        for point in project["extension_points"]
    ]
    (RESULTS / "patch-plan.md").write_text(
        "# Routinator/Krill Patch Plan\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "No patch files are stored in this public repository. When patches are "
        "created, they should live in the relevant upstream worktree or PR branch.\n\n"
        + markdown_table(patch_rows, [
            ("project", "Project"), ("area", "Area"), ("patch_unit", "Patch Unit"),
            ("upstream_source", "Upstream Source"), ("status", "Status"),
        ]) + "\n"
    )


if __name__ == "__main__":
    main()
