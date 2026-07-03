#!/usr/bin/env python3
"""Render the PQC RPKI markdown draft into submission helper artifacts.

This is intentionally small and dependency-free.  It produces RFCXML v3 that is
well-formed and suitable for xml2rfc/datatracker validation, plus a plain-text
review copy.  It is not a full mmark implementation.
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ietf" / "draft-yoshikawa-sidrops-pqc-rpki-01.md"
OUTDIR = ROOT / "ietf" / "submission"
BIBXML_DIR = ROOT / "ietf" / "bibxml"
DOCNAME = "draft-yoshikawa-sidrops-pqc-rpki-01"


@dataclass
class Section:
    level: int
    title: str
    blocks: list[object] = field(default_factory=list)


@dataclass
class Paragraph:
    text: str


@dataclass
class BulletList:
    items: list[str]


@dataclass
class NumberedList:
    items: list[str]


@dataclass
class Table:
    headers: list[str]
    rows: list[list[str]]


def split_source(text: str) -> tuple[dict[str, object], str, str, str]:
    header, rest = text.split("--- abstract", 1)
    abstract, rest = rest.split("--- middle", 1)
    middle, back = rest.split("--- back", 1)
    meta: dict[str, object] = {}
    author: dict[str, str] = {}
    keywords: list[str] = []
    in_keywords = False
    in_author = False
    for raw in header.strip().strip("-").splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("keyword:"):
            in_keywords = True
            in_author = False
            continue
        if line.startswith("author:"):
            in_author = True
            in_keywords = False
            continue
        if in_keywords and line.strip().startswith("- "):
            keywords.append(line.strip()[2:].strip())
            continue
        if in_author:
            stripped = line.strip()
            if stripped.startswith("- "):
                stripped = stripped[2:]
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                author[key.strip()] = value.strip().strip('"')
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    meta["keywords"] = keywords
    meta["author"] = author
    return meta, abstract.strip(), middle.strip(), back.strip()


def consume_blocks(lines: list[str]) -> list[object]:
    blocks: list[object] = []
    para: list[str] = []
    bullet: list[str] = []
    numbered: list[str] = []
    table: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            blocks.append(Paragraph(" ".join(part.strip() for part in para)))
            para = []

    def flush_bullet() -> None:
        nonlocal bullet
        if bullet:
            blocks.append(BulletList(bullet))
            bullet = []

    def flush_numbered() -> None:
        nonlocal numbered
        if numbered:
            blocks.append(NumberedList(numbered))
            numbered = []

    def flush_table() -> None:
        nonlocal table
        if table:
            parsed = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in table]
            if len(parsed) < 2 or not all(re.fullmatch(r":?-+:?", cell) for cell in parsed[1]):
                raise ValueError("invalid Markdown table")
            blocks.append(Table(parsed[0], parsed[2:]))
            table = []

    for raw in lines:
        line = raw.rstrip()
        if not line:
            flush_para()
            flush_bullet()
            flush_numbered()
            flush_table()
            continue
        if line.startswith("|") and line.endswith("|"):
            flush_para()
            flush_bullet()
            flush_numbered()
            table.append(line)
            continue
        flush_table()
        if line.startswith("* "):
            flush_para()
            flush_numbered()
            bullet.append(line[2:].strip())
            continue
        match = re.match(r"^\d+\.\s+(.*)$", line)
        if match:
            flush_para()
            flush_bullet()
            numbered.append(match.group(1).strip())
            continue
        if line.startswith("  ") and bullet:
            bullet[-1] += " " + line.strip()
            continue
        if line.startswith("  ") and numbered:
            numbered[-1] += " " + line.strip()
            continue
        flush_bullet()
        flush_numbered()
        para.append(line)
    flush_para()
    flush_bullet()
    flush_numbered()
    flush_table()
    return blocks


def parse_sections(text: str) -> list[Section]:
    sections: list[Section] = []
    current_title = ""
    current_level = 1
    current_lines: list[str] = []
    for raw in text.splitlines():
        if raw.startswith("#"):
            if current_title:
                sections.append(
                    Section(current_level, current_title, consume_blocks(current_lines))
                )
            current_level = len(raw) - len(raw.lstrip("#"))
            current_title = raw.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(raw)
    if current_title:
        sections.append(Section(current_level, current_title, consume_blocks(current_lines)))
    return sections


def add_t(parent: ET.Element, text: str) -> None:
    element = ET.SubElement(parent, "t")
    add_inline(element, text)


def add_inline(parent: ET.Element, text: str) -> None:
    pattern = re.compile(r"`([^`]+)`|\[([A-Za-z0-9_.-]+)\]")
    pos = 0
    last_child: ET.Element | None = None
    for match in pattern.finditer(text):
        literal = text[pos : match.start()]
        if last_child is None:
            parent.text = (parent.text or "") + literal
        else:
            last_child.tail = (last_child.tail or "") + literal
        if match.group(1) is not None:
            last_child = ET.SubElement(parent, "tt")
            last_child.text = match.group(1)
        else:
            last_child = ET.SubElement(parent, "xref", {"target": match.group(2)})
        pos = match.end()
    literal = text[pos:]
    if last_child is None:
        parent.text = (parent.text or "") + literal
    else:
        last_child.tail = (last_child.tail or "") + literal


def add_block(parent: ET.Element, block: object) -> None:
    if isinstance(block, Paragraph):
        add_t(parent, block.text)
    elif isinstance(block, BulletList):
        ul = ET.SubElement(parent, "ul")
        for item in block.items:
            li = ET.SubElement(ul, "li")
            add_t(li, item)
    elif isinstance(block, NumberedList):
        ol = ET.SubElement(parent, "ol")
        for item in block.items:
            li = ET.SubElement(ol, "li")
            add_t(li, item)
    elif isinstance(block, Table):
        table = ET.SubElement(parent, "table")
        thead = ET.SubElement(table, "thead")
        header_row = ET.SubElement(thead, "tr")
        for value in block.headers:
            add_inline(ET.SubElement(header_row, "th"), value)
        tbody = ET.SubElement(table, "tbody")
        for values in block.rows:
            row = ET.SubElement(tbody, "tr")
            for value in values:
                add_inline(ET.SubElement(row, "td"), value)


def add_sections(parent: ET.Element, sections: list[Section]) -> None:
    stack: list[tuple[int, ET.Element]] = [(0, parent)]
    for sec in sections:
        while stack and stack[-1][0] >= sec.level:
            stack.pop()
        container = stack[-1][1]
        attrs = {"anchor": anchor(sec.title)}
        if sec.title == "Acknowledgements":
            attrs["numbered"] = "false"
        element = ET.SubElement(container, "section", attrs)
        ET.SubElement(element, "name").text = sec.title
        for block in sec.blocks:
            add_block(element, block)
        stack.append((sec.level, element))


def anchor(title: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return value or "section"


def reference(
    parent: ET.Element,
    anchor_value: str,
    title: str,
    series_name: str | None = None,
    series_value: str | None = None,
    target: str | None = None,
    author_fullname: str | None = None,
    author_initials: str | None = None,
    author_surname: str | None = None,
    organization: str | None = None,
    month: str | None = None,
    year: str | None = None,
) -> None:
    attrs = {"anchor": anchor_value}
    if target:
        attrs["target"] = target
    ref = ET.SubElement(parent, "reference", attrs)
    front = ET.SubElement(ref, "front")
    ET.SubElement(front, "title").text = title
    author_attrs: dict[str, str] = {}
    if author_fullname:
        author_attrs["fullname"] = author_fullname
    if author_initials:
        author_attrs["initials"] = author_initials
    if author_surname:
        author_attrs["surname"] = author_surname
    author = ET.SubElement(front, "author", author_attrs)
    if organization:
        ET.SubElement(author, "organization").text = organization
    date_attrs: dict[str, str] = {}
    if month:
        date_attrs["month"] = month
    if year:
        date_attrs["year"] = year
    ET.SubElement(front, "date", date_attrs)
    if series_name and series_value:
        ET.SubElement(ref, "seriesInfo", {"name": series_name, "value": series_value})


def add_bibxml(parent: ET.Element, filename: str) -> None:
    path = BIBXML_DIR / filename
    parent.append(ET.parse(path).getroot())


def build_xml(meta: dict[str, object], abstract: str, middle: str, back: str) -> ET.Element:
    rfc = ET.Element(
        "rfc",
        {
            "version": "3",
            "category": str(meta.get("category", "std")),
            "ipr": str(meta.get("ipr", "trust200902")),
            "docName": DOCNAME,
            "submissionType": str(meta.get("submissiontype", "IETF")),
            "consensus": "true",
        },
    )
    front = ET.SubElement(rfc, "front")
    ET.SubElement(front, "title", {"abbrev": str(meta.get("abbrev", ""))}).text = str(
        meta.get("title", "")
    )
    ET.SubElement(front, "seriesInfo", {"name": "Internet-Draft", "value": DOCNAME})
    author = meta["author"]  # type: ignore[index]
    author_el = ET.SubElement(
        front,
        "author",
        {"fullname": author["fullname"], "initials": "T.", "surname": "Yoshikawa"},
    )
    ET.SubElement(author_el, "organization").text = author["organization"]
    address = ET.SubElement(author_el, "address")
    ET.SubElement(address, "email").text = author["email"]
    draft_date = date.fromisoformat(str(meta.get("date", date.today().isoformat())))
    ET.SubElement(
        front,
        "date",
        {
            "year": str(draft_date.year),
            "month": draft_date.strftime("%B"),
            "day": str(draft_date.day),
        },
    )
    ET.SubElement(front, "area").text = str(meta.get("area", "Routing"))
    ET.SubElement(front, "workgroup").text = str(meta.get("wg", "SIDROPS"))
    for keyword in meta.get("keywords", []):  # type: ignore[union-attr]
        ET.SubElement(front, "keyword").text = str(keyword)
    abstract_el = ET.SubElement(front, "abstract")
    for block in consume_blocks(abstract.splitlines()):
        add_block(abstract_el, block)

    middle_el = ET.SubElement(rfc, "middle")
    add_sections(middle_el, parse_sections(middle))

    back_el = ET.SubElement(rfc, "back")
    # Keep references compact.  xml2rfc/datatracker can replace these with
    # complete bibxml references if desired.
    normative = ET.SubElement(back_el, "references")
    ET.SubElement(normative, "name").text = "Normative References"
    bcp14 = ET.SubElement(
        normative,
        "referencegroup",
        {"anchor": "BCP14", "target": "https://www.rfc-editor.org/info/bcp14"},
    )
    for number in ("2119", "8174"):
        add_bibxml(bcp14, f"reference.RFC.{number}.xml")
    for number in (
        "6480", "6487", "6488", "6916", "7935", "8182",
        "9286", "9582", "9589", "9691", "9881", "9882",
    ):
        add_bibxml(normative, f"reference.RFC.{number}.xml")
    for name in (
        "ietf-lamps-pq-composite-sigs",
        "ietf-lamps-cms-composite-sigs",
    ):
        add_bibxml(normative, f"reference.I-D.{name}.xml")
    reference(
        normative,
        "FIPS204",
        "Module-Lattice-Based Digital Signature Standard",
        "FIPS",
        "204",
        "https://doi.org/10.6028/NIST.FIPS.204",
        organization="National Institute of Standards and Technology",
        month="August",
        year="2024",
    )
    informative = ET.SubElement(back_el, "references")
    ET.SubElement(informative, "name").text = "Informative References"
    for number in (
        "7942", "8032", "8209", "8608", "9323", "9814", "9909",
    ):
        add_bibxml(informative, f"reference.RFC.{number}.xml")
    for name in ("ietf-sidrops-rpki-ccr", "ietf-sidrops-aspa-profile"):
        add_bibxml(informative, f"reference.I-D.{name}.xml")
    reference(
        informative,
        "FIPS186-5",
        "Digital Signature Standard (DSS)",
        "FIPS",
        "186-5",
        "https://doi.org/10.6028/NIST.FIPS.186-5",
        organization="National Institute of Standards and Technology",
        month="February",
        year="2023",
    )
    reference(
        informative,
        "FIPS205",
        "Stateless Hash-Based Digital Signature Standard",
        "FIPS",
        "205",
        "https://doi.org/10.6028/NIST.FIPS.205",
        organization="National Institute of Standards and Technology",
        month="August",
        year="2024",
    )
    reference(
        informative,
        "Doesburg2025",
        "Post-Quantum Cryptography for the RPKI",
        target="https://www.sidnlabs.nl/en/news-and-blogs/thesis-pqc-for-the-rpki",
        author_fullname="Dirk Doesburg",
        author_initials="D.",
        author_surname="Doesburg",
        organization="Radboud University",
        month="June",
        year="2025",
    )
    reference(
        informative,
        "pqRPKI",
        "pqRPKI: A Practical RPKI Architecture for the Post-Quantum Era",
        target="https://arxiv.org/abs/2603.06968",
        author_fullname="W. Li et al.",
        month="March",
        year="2026",
    )
    reference(
        informative,
        "pqc-rpki-lab",
        "pqc-rpki-lab experimental harness",
        target=(
            "https://github.com/marokiki/pqc-rpki-lab/releases/tag/"
            f"{DOCNAME}"
        ),
        author_fullname="Tomoki Yoshikawa",
        author_initials="T.",
        author_surname="Yoshikawa",
        month="July",
        year="2026",
    )
    back_sections_text = back.split("# References", 1)[0].strip()
    if back_sections_text:
        add_sections(back_el, parse_sections(back_sections_text))
    return rfc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", choices=("00", "01"), default="01")
    args = parser.parse_args()
    global SOURCE, DOCNAME
    DOCNAME = f"draft-yoshikawa-sidrops-pqc-rpki-{args.revision}"
    SOURCE = ROOT / "ietf" / f"{DOCNAME}.md"
    meta, abstract, middle, back = split_source(SOURCE.read_text())
    OUTDIR.mkdir(parents=True, exist_ok=True)
    xml_root = build_xml(meta, abstract, middle, back)
    xml_path = OUTDIR / f"{DOCNAME}.xml"
    ET.indent(xml_root)
    ET.ElementTree(xml_root).write(xml_path, encoding="utf-8", xml_declaration=True)
    ET.parse(xml_path)
    print(xml_path)


if __name__ == "__main__":
    main()
