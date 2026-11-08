#!/usr/bin/env python3
"""Build site content from the GitHub profile repository (nkorf/nkorf).

The profile repository is the single source of truth for publications:
`publications.bib` is converted into one HugoBlox publication bundle per
entry, and the generated `clinical_trials.md` and `policy_citations.md`
are copied in as pages.

Usage:
    python3 scripts/sync_profile.py --profile ../nkorf --site .
"""

import argparse
import importlib.util
import re
import shutil
from pathlib import Path

import yaml

PUB_TYPES = {
    "journal": "article-journal",
    "conference": "paper-conference",
    "book": "chapter",
    "deliverable": "report",
    "dissertation": "thesis",
    "software": "software",
    "dataset": "dataset",
    "workingpaper": "manuscript",
}

CITE_FIELDS = [
    "author", "title", "journal", "booktitle", "editor", "series", "year",
    "volume", "number", "pages", "publisher", "address", "institution",
    "school", "isbn", "doi", "url", "note",
]

TYPE_LABELS = {
    "article-journal": "Journal article",
    "paper-conference": "Conference paper",
    "chapter": "Book chapter",
    "report": "Report",
    "thesis": "Thesis",
    "software": "Software",
    "dataset": "Dataset",
    "manuscript": "Working paper",
}


OLD_LIST_URLS = (
    "publications-journals", "publications-conferences", "publications-edited",
    "publications-selected", "publications-wp", "publications-theses", "list",
)

INDEX_PAGE = (
    "---\ntitle: Publications\naliases:\n"
    + "".join(f"  - /publicationlists/{name}/\n" for name in OLD_LIST_URLS)
    + "  - /publicationlists/\n---\n\n"
    "Numbered as in the [full list on GitHub]"
    "(https://github.com/nkorf/nkorf/blob/main/publications.md), "
    "newest first within each section. CABS denotes the ranking in the "
    "Chartered Association of Business Schools Academic Journal Guide. "
    "See also the [clinical trials](/clinical-trials/) and the "
    "[policy impact](/policy-citations/) of this work.\n"
)


def section_numbers(groups) -> dict:
    """Bib key -> section title, number and overall position, as on GitHub."""
    numbering = {}
    for _, title, numbered in groups:
        for num, entry in numbered:
            numbering[entry["ID"]] = {
                "pub_section": title,
                "pub_number": num,
                "pub_order": len(numbering) + 1,
            }
    return numbering


def load_generator(profile: Path):
    """Import generate_publications.py from the profile repo as a module."""
    spec = importlib.util.spec_from_file_location(
        "generate_publications", profile / "generate_publications.py")
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load generate_publications.py from {profile}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strip_braces(text: str) -> str:
    text = text.replace("{", "").replace("}", "").replace("---", "\u2014").replace("--", "\u2013")
    return re.sub(r"\s+", " ", text).strip()


def author_names(raw: str) -> list:
    """BibTeX 'Surname, I.I. and ...' -> HugoBlox author list ('me' for the owner)."""
    names = []
    for part in re.split(r"\s+and\s+", strip_braces(raw)):
        part = part.strip()
        if not part:
            continue
        if "," in part:
            family, given = [p.strip() for p in part.split(",", 1)]
        else:
            bits = part.split()
            family, given = bits[-1], " ".join(bits[:-1])
        if family.lower() == "korfiatis" and given[:1].upper() == "N":
            names.append("me")
        else:
            names.append(f"{given} {family}".strip())
    return names


def cite_bib(entry: dict) -> str:
    fields = [(k, entry[k]) for k in CITE_FIELDS if entry.get(k)]
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields)
    return f"@{entry['ENTRYTYPE']}{{{entry['ID']},\n{body}\n}}\n"


def publication_page(entry: dict, numbering: dict) -> tuple:
    category = entry.get("category", "journal")
    pub_type = PUB_TYPES.get(category, "article-journal")
    year = re.sub(r"\D", "", entry.get("year", "")) or "1900"
    note = strip_braces(entry.get("note", ""))
    forthcoming = note.lower() in ("forthcoming", "to appear")

    venue = strip_braces(entry.get("journal") or entry.get("booktitle")
                         or entry.get("institution") or entry.get("school")
                         or entry.get("publisher") or "")
    publication = {"name": venue + (" (forthcoming)" if forthcoming else "")}
    if entry.get("volume"):
        publication["volume"] = strip_braces(entry["volume"])
    if entry.get("number"):
        publication["issue"] = strip_braces(entry["number"])
    if entry.get("pages"):
        publication["pages"] = strip_braces(entry["pages"]).replace("--", "-")

    tags = [TYPE_LABELS.get(pub_type, "Publication")]
    if entry.get("cabs"):
        tags.append(f"CABS {entry['cabs']}")
    if entry.get("nct"):
        tags.append("Clinical trial")

    links = []
    nct = entry.get("nct", "").strip()
    if nct:
        links.append({"name": f"NCT{nct}",
                      "url": f"https://clinicaltrials.gov/study/NCT{nct}"})
    for i in ("", "2", "3"):
        url = entry.get(f"url{i}")
        if url and "doi.org" not in url:
            links.append({"name": strip_braces(entry.get(f"urlname{i}", "Link")),
                          "url": url})

    front = {
        "title": strip_braces(entry.get("title", "")),
        "authors": author_names(entry.get("author", "")),
        "date": f"{year}-01-01",
        "publication_types": [pub_type],
        "publication": publication,
        "peer_reviewed": category in ("journal", "conference", "book"),
        "tags": tags,
        "featured": entry.get("cabs", "").strip() == "4",
    }
    if entry["ID"] in numbering:
        front.update(numbering[entry["ID"]])
    if entry.get("cabs"):
        front["cabs"] = entry["cabs"].strip()
    if entry.get("doi"):
        front["hugoblox"] = {"ids": {"doi": entry["doi"].strip()}}
    if links:
        front["links"] = links
    if note and not forthcoming:
        front["summary"] = note

    body = []
    for key, label in (("policycitation", "Policy impact"),
                       ("patentcitation", "Patent citation")):
        if entry.get(key):
            body.append(f"**{label}:** {strip_braces(entry[key])}")
    text = "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True,
                                    width=1000) + "---\n"
    if body:
        text += "\n" + "\n\n".join(body) + "\n"
    return text, cite_bib(entry)


def copy_generated_page(src: Path, dst: Path, title: str, intro: str):
    """Copy a generated profile-repo page, replacing its nav line and H1."""
    lines = src.read_text(encoding="utf-8").splitlines()
    while lines and (lines[0].startswith("[[") or not lines[0].strip()
                     or lines[0].startswith("# ")):
        lines.pop(0)
    front = yaml.safe_dump({"title": title, "type": "page"}, sort_keys=False)
    head = f"---\n{front}---\n\n" + (f"{intro}\n\n" if intro else "")
    dst.write_text(head + "\n".join(lines) + "\n",
                   encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, type=Path,
                    help="checkout of github.com/nkorf/nkorf")
    ap.add_argument("--site", required=True, type=Path, help="Hugo site root")
    args = ap.parse_args()

    gen = load_generator(args.profile)
    entries = gen.load_bibtex(str(args.profile / "publications.bib"))
    if not hasattr(gen, "numbered_by_category"):
        raise SystemExit("generate_publications.py has no numbered_by_category(); "
                         "update github.com/nkorf/nkorf")
    numbering = section_numbers(gen.numbered_by_category(entries))

    pubs = args.site / "content" / "publications"
    for child in pubs.iterdir() if pubs.exists() else []:
        if child.is_dir():
            shutil.rmtree(child)
    pubs.mkdir(parents=True, exist_ok=True)
    (pubs / "_index.md").write_text(INDEX_PAGE, encoding="utf-8")

    for entry in entries:
        page, bib = publication_page(entry, numbering)
        folder = pubs / entry["ID"].lower()
        folder.mkdir()
        (folder / "index.md").write_text(page, encoding="utf-8")
        (folder / "cite.bib").write_text(bib, encoding="utf-8")

    content = args.site / "content"
    copy_generated_page(
        args.profile / "clinical_trials.md", content / "clinical-trials.md",
        "Clinical Trials", "")
    copy_generated_page(
        args.profile / "policy_citations.md", content / "policy-citations.md",
        "Policy Impact", "")

    cv = args.profile / "cv_academic" / "nikolaos_korfiatis_academic_cv.pdf"
    if cv.exists():
        (args.site / "static" / "uploads").mkdir(parents=True, exist_ok=True)
        shutil.copy2(cv, args.site / "static" / "uploads" / "korfiatis_cv.pdf")
    photo = args.profile / "cv_academic" / "photo.jpg"
    if photo.exists():
        dst = args.site / "assets" / "media" / "authors"
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(photo, dst / "me.jpg")

    unlisted = sorted(e["ID"] for e in entries if e["ID"] not in numbering)
    if unlisted:
        print("not in the numbered list (category outside CATEGORY_ORDER): "
              + ", ".join(unlisted))
    print(f"{len(entries)} publications written to {pubs}, "
          f"{len(numbering)} numbered")


if __name__ == "__main__":
    main()
