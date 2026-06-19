#!/usr/bin/env python3
"""Render the PQC RPKI markdown draft into submission helper artifacts.

This is intentionally small and dependency-free.  It produces RFCXML v3 that is
well-formed and suitable for xml2rfc/datatracker validation, plus a plain-text
review copy.  It is not a full mmark implementation.
"""

from __future__ import annotations

import re
import textwrap
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ietf" / "draft-yoshikawa-sidrops-pqc-rpki-00.md"
OUTDIR = ROOT / "ietf" / "submission"
BIBXML_DIR = ROOT / "ietf" / "bibxml"
DOCNAME = "draft-yoshikawa-sidrops-pqc-rpki-00"


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

    for raw in lines:
        line = raw.rstrip()
        if not line:
            flush_para()
            flush_bullet()
            flush_numbered()
            continue
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
        flush_bullet()
        flush_numbered()
        para.append(line)
    flush_para()
    flush_bullet()
    flush_numbered()
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


def add_sections(parent: ET.Element, sections: list[Section]) -> None:
    stack: list[tuple[int, ET.Element]] = [(0, parent)]
    for sec in sections:
        while stack and stack[-1][0] >= sec.level:
            stack.pop()
        container = stack[-1][1]
        element = ET.SubElement(container, "section", {"anchor": anchor(sec.title)})
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
    for number in (
        "2119", "8174", "6480", "6487", "6488", "6916", "7935", "8182",
        "9286", "9582", "9589", "9814", "9881", "9882", "9909",
    ):
        add_bibxml(normative, f"reference.RFC.{number}.xml")
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
    reference(
        normative,
        "FIPS205",
        "Stateless Hash-Based Digital Signature Standard",
        "FIPS",
        "205",
        "https://doi.org/10.6028/NIST.FIPS.205",
        organization="National Institute of Standards and Technology",
        month="August",
        year="2024",
    )
    informative = ET.SubElement(back_el, "references")
    ET.SubElement(informative, "name").text = "Informative References"
    add_bibxml(informative, "reference.RFC.7942.xml")
    for name in (
        "ietf-lamps-pq-composite-sigs",
        "ietf-lamps-cms-composite-sigs",
        "doesburg-sidrops-nullscheme",
    ):
        add_bibxml(informative, f"reference.I-D.{name}.xml")
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
        "pqc-rpki-lab",
        "pqc-rpki-lab experimental harness",
        target="https://github.com/marokiki/pqc-rpki-lab/releases/tag/draft-yoshikawa-sidrops-pqc-rpki-00",
        author_fullname="Tomoki Yoshikawa",
        author_initials="T.",
        author_surname="Yoshikawa",
        month="June",
        year="2026",
    )
    back_sections_text = back.split("# References", 1)[0].strip()
    if back_sections_text:
        add_sections(back_el, parse_sections(back_sections_text))
    return rfc


def plain_text(text: str) -> str:
    body = re.sub(r"^---.*$", "", text, flags=re.MULTILINE)
    body = re.sub(r"`([^`]+)`", r"\1", body)
    lines: list[str] = []
    for line in body.splitlines():
        if not line or line.startswith("#"):
            lines.append(line)
        else:
            lines.extend(textwrap.wrap(line, width=72) or [""])
    return "\n".join(lines) + "\n"


def main() -> None:
    meta, abstract, middle, back = split_source(SOURCE.read_text())
    OUTDIR.mkdir(parents=True, exist_ok=True)
    xml_root = build_xml(meta, abstract, middle, back)
    xml_path = OUTDIR / f"{DOCNAME}.xml"
    ET.indent(xml_root)
    ET.ElementTree(xml_root).write(xml_path, encoding="utf-8", xml_declaration=True)
    ET.parse(xml_path)
    md_path = OUTDIR / f"{DOCNAME}.md"
    md_path.write_text(SOURCE.read_text())
    txt_path = OUTDIR / f"{DOCNAME}.txt"
    txt_path.write_text(plain_text(SOURCE.read_text()))
    print(xml_path)
    print(md_path)
    print(txt_path)


if __name__ == "__main__":
    main()
