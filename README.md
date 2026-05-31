This respository stores my notes for a DND game I play in called `Atheron`. The notes are written in markdown, I use [`Obsidian`](https://obsidian.md) for writting them.

## Character Collation Hook

This repo includes a pre-commit hook that collates character mentions from session notes into `Character/<Character Name>.md`.

Setup (once per clone):

```sh
git config core.hooksPath .githooks
```

Manual run:

```sh
python scripts/collate_characters.py
```
