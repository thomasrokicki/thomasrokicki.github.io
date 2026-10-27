#!/usr/bin/env python3
"""Validate cv/data.yaml and regenerate the marked regions of public/index.html.

Each region sits between `<!-- BEGIN generated:NAME ... -->` and
`<!-- END generated:NAME -->`; everything outside the markers is left untouched.
Exits non-zero (without writing) on broken data; TODOs are only reported.
"""

import html
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "cv" / "data.yaml"
SITE = ROOT / "public"  # web root: the only directory the server exposes
INDEX = SITE / "index.html"

LINK_ICONS = {
    "pdf": "far fa-file-pdf",
    "code": "fab fa-github",
    "video": "fas fa-video",
    "website": "fa fa-table",
    "thesis": "fas fa-book",
}
PROFILE_ICONS = {
    "github": "fab fa-github",
    "twitter": "fab fa-twitter",
    "linkedin": "fab fa-linkedin",
    "scholar": "ai ai-google-scholar ai-1x",
    "cv": "ai ai-cv ai-1x",
}
AWARD_ICONS = {"gold": "fas fa-trophy", "silver": "fas fa-medal"}

# Allowed fields per kind of entry: (required, optional).
FIELDS = {
    "root": ({"profile", "positions", "education", "publications", "talks"}, set()),
    "profile": ({"name", "title", "email", "location", "website", "links"}, set()),
    "profile link": ({"kind", "url"}, {"cv"}),
    "position": ({"title", "institution", "location", "start"}, {"team", "end"}),
    "education": (
        {"degree", "institution", "location", "start"},
        {"team", "end", "thesis", "supervisors", "jury"},
    ),
    "jury": (set(), {"president", "reviewers", "examiners"}),
    "publication": ({"title", "authors", "venue", "venue_short", "year"}, {"icon", "award", "links"}),
    "award": ({"level", "label"}, set()),
    "talk": ({"year", "event", "title", "location"}, {"description", "virtual", "links"}),
    "link": ({"kind", "url"}, set()),
}


# --- Validation ---------------------------------------------------------------


def check_fields(errors, where, obj, kind):
    if not isinstance(obj, dict):
        errors.append(f"{where}: expected a mapping, got {type(obj).__name__}")
        return False
    required, optional = FIELDS[kind]
    errors.extend(f"{where}: missing field '{k}'" for k in sorted(required - obj.keys()))
    errors.extend(f"{where}: unknown field '{k}'" for k in sorted(obj.keys() - required - optional))
    return True


def check_url(errors, where, url, kinds, kind):
    if kind not in kinds:
        errors.append(f"{where}: unknown link kind '{kind}' (expected one of {', '.join(kinds)})")
    if not isinstance(url, str):
        errors.append(f"{where}: url must be a string")
    elif not re.match(r"[a-z]+:", url) and not (SITE / url).is_file():
        errors.append(f"{where}: local file 'public/{url}' does not exist")


def check_links(errors, where, links):
    for i, link in enumerate(links or []):
        if check_fields(errors, f"{where}.links[{i}]", link, "link"):
            check_url(errors, f"{where}.links[{i}]", link.get("url"), LINK_ICONS, link.get("kind"))


def check_entries(errors, data, section, kind, extra=None):
    entries = data.get(section)
    if not isinstance(entries, list):
        errors.append(f"{section}: expected a list")
        return
    for i, entry in enumerate(entries):
        where = f"{section}[{i}]"
        if check_fields(errors, where, entry, kind) and extra:
            extra(errors, where, entry)


def walk(value, path=""):
    """Yield (path, value) for every node of the YAML tree."""
    yield path, value
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")


def validate(data):
    errors = []
    if not check_fields(errors, "data.yaml", data, "root"):
        return errors, []

    profile = data["profile"]
    if check_fields(errors, "profile", profile, "profile"):
        for i, link in enumerate(profile.get("links") or []):
            where = f"profile.links[{i}]"
            if check_fields(errors, where, link, "profile link"):
                check_url(errors, where, link.get("url"), PROFILE_ICONS, link.get("kind"))
    me = profile.get("name") if isinstance(profile, dict) else None

    def check_education(errors, where, entry):
        if "jury" in entry:
            check_fields(errors, f"{where}.jury", entry["jury"], "jury")

    def check_publication(errors, where, pub):
        if not isinstance(pub.get("year"), int):
            errors.append(f"{where}: year must be a number")
        if me not in (pub.get("authors") or []):
            errors.append(f"{where}: '{me}' is not among the authors (typo in a name?)")
        if "award" in pub and check_fields(errors, f"{where}.award", pub["award"], "award"):
            if pub["award"].get("level") not in AWARD_ICONS:
                errors.append(f"{where}.award: level must be one of {', '.join(AWARD_ICONS)}")
        check_links(errors, where, pub.get("links"))

    def check_talk(errors, where, talk):
        if not isinstance(talk.get("year"), int):
            errors.append(f"{where}: year must be a number")
        check_links(errors, where, talk.get("links"))

    check_entries(errors, data, "positions", "position")
    check_entries(errors, data, "education", "education", check_education)
    check_entries(errors, data, "publications", "publication", check_publication)
    check_entries(errors, data, "talks", "talk", check_talk)

    todos = []
    for path, value in walk(data):
        if isinstance(value, dict) and value.keys() & {"en", "fr"} and value.keys() != {"en", "fr"}:
            errors.append(f"{path}: translated text needs exactly 'en' and 'fr'")
        if isinstance(value, str) and "TODO" in value:
            todos.append(path)
    return errors, todos


# --- HTML generation ----------------------------------------------------------


def text(value):
    """Escape a plain or translated field for HTML (the website is in English)."""
    if isinstance(value, dict):
        value = value["en"]
    return html.escape(str(value), quote=False)


def attr(value):
    return html.escape(str(value), quote=True)


def with_links(value):
    """Escape a field and turn its [text](url) links into anchors."""
    return re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{m.group(2)}" target="_blank">{m.group(1)}</a>',
        text(value),
    )


def icon_list(links, icons, wrapper):
    items = [
        f'    <li><a href="{attr(link["url"])}" target="_blank"><i class="{icons[link["kind"]]}"></i></a></li>'
        for link in links
    ]
    return [f'<div class="{wrapper}">', "  <ul>", *items, "  </ul>", "</div>"]


def profile_titles(profile):
    return [f"<h2>{text(profile['name'])}</h2>", f"<h4>{text(profile['title'])}</h4>"]


def profile_contact(profile):
    email = text(profile["email"]).replace("@", " [at] ")
    return [
        *icon_list(profile["links"], PROFILE_ICONS, "social-links"),
        "",
        '<div class="info-list">',
        "  <ul>",
        f'    <li><span class="value"><i class="fas fa-envelope"></i> {email}</span></li>',
        f'    <li><span class="value"><i class="fas fa-map-marker-alt"></i> {text(profile["location"])}</span></li>',
        "  </ul>",
        "</div>",
    ]


def publications(pubs, me):
    lines = []
    for pub in pubs:
        authors = ", ".join(f"<u>{text(a)}</u>" if a == me else text(a) for a in pub["authors"])
        icon = f'<i class="{attr(pub["icon"])}"></i> ' if "icon" in pub else ""
        lines += [
            '<div class="ci-text">',
            f"  <h4>{icon}{text(pub['title'])}</h4>",
            f"  <p>{authors}<br>",
            f"  Accepted at the {text(pub['venue'])} ({text(pub['venue_short'])}) {pub['year']}</p>",
        ]
        if "award" in pub:
            level = pub["award"]["level"]
            lines.append(
                f'  <div class="award-badge award-{level}"><i class="{AWARD_ICONS[level]}"></i> '
                f"{text(pub['award']['label'])}</div>"
            )
        lines += ["  " + line for line in icon_list(pub.get("links", []), LINK_ICONS, "paper-icons")]
        lines += ["</div>", '<div class="white-space-10"></div>', ""]
    return lines[:-1]


def talks(entries):
    lines = []
    for talk in entries:
        place = text(talk["location"])
        if talk.get("virtual"):
            place = f"<strike>{place}</strike> Virtual event"
        description = [f"        {with_links(talk['description'])}<br>"] if "description" in talk else []
        lines += [
            '<div class="ci-text">',
            f"  <h4>{talk['year']}</h4>",
            "  <ul>",
            "    <li>",
            f'        <i class="fas fa-chalkboard-teacher"></i> <b>{text(talk["event"])}</b>: {text(talk["title"])}<br>',
            *description,
            f"        {place}",
            "    </li>",
            "  </ul>",
            *("  " + line for line in icon_list(talk.get("links", []), LINK_ICONS, "paper-icons")),
            "</div>",
            "",
            '<div class="white-space-30"></div>',
            "",
        ]
    return lines[:-3]


def inject(page, name, lines):
    pattern = re.compile(
        rf"^([ \t]*)<!-- BEGIN generated:{name}\b[^\n]*-->\n.*?^[ \t]*<!-- END generated:{name} -->",
        re.S | re.M,
    )
    match = pattern.search(page)
    if not match:
        sys.exit(f"error: public/index.html has no 'generated:{name}' markers")
    indent = match.group(1)
    begin, _, _ = match.group(0).partition("\n")
    body = "".join(f"{indent}{line}\n" if line else "\n" for line in lines)
    end = f"{indent}<!-- END generated:{name} -->"
    return page[: match.start()] + f"{begin}\n{body}{end}" + page[match.end() :]


def main():
    try:
        data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        sys.exit(f"error: {DATA.relative_to(ROOT)}: {e}")

    errors, todos = validate(data)
    for path in todos:
        print(f"warning: TODO left in {path}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

    profile = data["profile"]
    regions = {
        "profile-titles": profile_titles(profile),
        "profile-contact": profile_contact(profile),
        "publications": publications(data["publications"], profile["name"]),
        "talks": talks(data["talks"]),
    }
    page = INDEX.read_text(encoding="utf-8")
    updated = page
    for name, lines in regions.items():
        updated = inject(updated, name, lines)
    if updated != page:
        INDEX.write_text(updated, encoding="utf-8")
        print("public/index.html regenerated")
    else:
        print("public/index.html up to date")


if __name__ == "__main__":
    main()
