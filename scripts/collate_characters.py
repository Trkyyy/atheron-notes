#!/usr/bin/env python3
"""Collate character mentions from session notes into Character/*.md files.

The script scans markdown files in Sessions/ (and Jobs/ if present), finds
mentions of known characters, and writes a generated section for each character
inside Character/<Character Name>.md.

Known characters are discovered from markdown files in Character/ and
Characers/ (legacy typo folder).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Dict, Iterable, List, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "Character"
CHAR_SOURCE_DIRS = [ROOT / "Character", ROOT / "Characers"]
SESSION_DIRS = [ROOT / "Sessions", ROOT / "Jobs"]

AUTO_START = "<!-- AUTO-COLLATED:START -->"
AUTO_END = "<!-- AUTO-COLLATED:END -->"

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[^\]]*)\]\]")
MDLINK_RE = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")


@dataclass(frozen=True)
class Mention:
    session_relpath: str
    line_number: int
    text: str


def list_session_files() -> List[Path]:
    files: List[Path] = []
    for base in SESSION_DIRS:
        if not base.exists():
            continue
        files.extend(sorted(base.glob("*.md"), key=lambda p: p.name.lower()))
    return files


def discover_character_names() -> Set[str]:
    names: Set[str] = set()
    for base in CHAR_SOURCE_DIRS:
        if not base.exists():
            continue
        for path in base.glob("*.md"):
            stem = path.stem.strip()
            if stem:
                names.add(stem)
    return names


def normalize_target(target: str) -> str:
    clean = target.strip().replace("%20", " ")
    name = Path(clean).stem if Path(clean).suffix else Path(clean).name
    return name.strip()


def extract_link_mentions(line: str) -> List[str]:
    names: List[str] = []

    for match in WIKILINK_RE.finditer(line):
        name = normalize_target(match.group(1))
        if name:
            names.append(name)

    for match in MDLINK_RE.finditer(line):
        target = match.group(1).strip()
        if "://" in target:
            continue
        name = normalize_target(target)
        if name:
            names.append(name)

    return names


def build_plain_text_patterns(character_names: Iterable[str]) -> Dict[str, re.Pattern[str]]:
    patterns: Dict[str, re.Pattern[str]] = {}
    for name in character_names:
        escaped = re.escape(name)
        patterns[name] = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
    return patterns


def collect_mentions(
    session_files: List[Path], character_names: Set[str]
) -> Dict[str, List[Mention]]:
    mentions: Dict[str, List[Mention]] = defaultdict(list)
    name_lookup = {name.casefold(): name for name in character_names}
    plain_patterns = build_plain_text_patterns(character_names)

    for session_path in session_files:
        rel = session_path.relative_to(ROOT).as_posix()
        lines = session_path.read_text(encoding="utf-8", errors="ignore").splitlines()

        for i, raw_line in enumerate(lines, start=1):
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped:
                continue

            seen_for_line: Set[str] = set()

            # Linked mentions are preferred and most reliable in Obsidian notes.
            for linked in extract_link_mentions(line):
                canonical = name_lookup.get(linked.casefold())
                if canonical and canonical not in seen_for_line:
                    mentions[canonical].append(Mention(rel, i, stripped))
                    seen_for_line.add(canonical)

            # Plain-text fallback catches unlinked references.
            for name, pattern in plain_patterns.items():
                if name in seen_for_line:
                    continue
                if pattern.search(stripped):
                    mentions[name].append(Mention(rel, i, stripped))
                    seen_for_line.add(name)

    return mentions


def render_generated_section(
    name: str, session_files: List[Path], mentions: List[Mention]
) -> str:
    mentions = sorted(mentions, key=lambda m: (m.session_relpath.lower(), m.line_number, m.text))
    distinct_sessions = sorted({m.session_relpath for m in mentions}, key=str.lower)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: List[str] = []
    lines.append(AUTO_START)
    lines.append("## Collated Mentions")
    lines.append("")
    lines.append(f"- Character: {name}")
    lines.append(f"- Generated: {generated_at}")
    lines.append(f"- Sessions scanned: {len(session_files)}")
    lines.append(f"- Total mentions: {len(mentions)}")
    lines.append(f"- Sessions with mentions: {len(distinct_sessions)}")
    lines.append("")
    lines.append("## Timeline")
    lines.append("")

    if not mentions:
        lines.append("- No mentions found in current session notes.")
        lines.append(AUTO_END)
        return "\n".join(lines)

    grouped: Dict[str, List[Mention]] = defaultdict(list)
    for mention in mentions:
        grouped[mention.session_relpath].append(mention)

    for session in sorted(grouped.keys(), key=str.lower):
        lines.append(f"### {session}")
        seen: Set[Tuple[int, str]] = set()
        for item in grouped[session]:
            key = (item.line_number, item.text)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"- L{item.line_number}: {item.text}")
        lines.append("")

    lines.append(AUTO_END)
    return "\n".join(lines).rstrip() + "\n"


def merge_with_existing(existing: str, generated: str, name: str) -> str:
    has_start = AUTO_START in existing
    has_end = AUTO_END in existing

    if has_start and has_end:
        before, _, tail = existing.partition(AUTO_START)
        _, _, after = tail.partition(AUTO_END)
        merged = before.rstrip() + "\n\n" + generated + after.lstrip("\n")
        return merged.rstrip() + "\n"

    if existing.strip():
        return existing.rstrip() + "\n\n" + generated

    header = f"# {name}\n\n"
    return header + generated


def write_character_files(
    character_names: Set[str], session_files: List[Path], mentions: Dict[str, List[Mention]]
) -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    for name in sorted(character_names, key=str.lower):
        out_path = TARGET_DIR / f"{name}.md"
        existing = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
        generated = render_generated_section(name, session_files, mentions.get(name, []))
        final = merge_with_existing(existing, generated, name)
        out_path.write_text(final, encoding="utf-8")


def main() -> None:
    session_files = list_session_files()
    character_names = discover_character_names()

    if not character_names:
        print("No character files found in Character/ or Characers/. Nothing to do.")
        return

    mentions = collect_mentions(session_files, character_names)
    write_character_files(character_names, session_files, mentions)

    print(
        f"Updated {len(character_names)} character files in {TARGET_DIR.relative_to(ROOT).as_posix()}/"
    )


if __name__ == "__main__":
    main()