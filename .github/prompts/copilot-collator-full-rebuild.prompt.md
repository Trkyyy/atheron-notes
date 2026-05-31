# Copilot Prompt: DnD Lore Collator (Full Rebuild)

Act as an Obsidian DnD lore collator for this workspace.

Goal:
Read my campaign notes and generate structured reference files under a new folder named collated, with subfolders for entities like characters, events, countries, organisations, locations, factions, items, and timeline.

Source material to read:
- All markdown files in Sessions
- All markdown files in Characers (yes, this folder name is intentionally misspelled)
- All markdown files in General
- Root markdown files like README.md and TODO List.md

Rules:
1. Do not modify or delete any source notes.
2. Only create or update files inside collated.
3. If collated does not exist, create it.
4. Create these subfolders if missing:
   - collated/characters
   - collated/events
   - collated/countries
   - collated/organisations
   - collated/locations
   - collated/factions
   - collated/items
   - collated/timeline
   - collated/meta
5. Deduplicate entities across notes by canonical name, and keep aliases in an Aliases section.
6. Mark uncertain facts clearly as Unconfirmed.
7. Every extracted fact should include source references (note filename + brief quote or paraphrase).
8. Prefer incremental updates if files already exist (idempotent behavior).

File format requirements:
- Each entity file should contain:
  - Title
  - Summary
  - Known Facts
  - Relationships
  - Timeline Mentions
  - Open Questions
  - Sources
- Create index files:
  - collated/characters/_index.md
  - collated/events/_index.md
  - collated/countries/_index.md
  - collated/organisations/_index.md
  - collated/locations/_index.md
  - collated/factions/_index.md
  - collated/items/_index.md
- Create collated/timeline/campaign-timeline.md ordered by session chronology.
- Create collated/meta/unresolved-questions.md for contradictions or missing details.

Output requirements in chat:
- List files created
- List files updated
- List ambiguous/conflicting lore points
- List any assumptions made
