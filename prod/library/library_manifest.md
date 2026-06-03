---
id: "202606030000"
title: "Library System Manifest & Guidelines"
type: "system_doc"
tags: ["manifest", "guidelines", "system"]
categories: ["system"]
created: "2026-06-03"
modified: "2026-06-03"
status: "stable"
summary: "Manifest document outlining the taxonomy, roster, and development loop rules."
---

# Library System Manifest & Guidelines

Welcome to the Library System. This repository is a portable, human-readable, and AI-searchable wiki database managed by a self-improving Ralph Loop.

---

## 1. Directory Strategy
The library maintains strict folder isolation:
- `dev/` - Sandbox folder where all drafting, research, and coding occurs.
- `prod/` - Stable production folder containing verified assets. Promoted *only* via the Archivist script.

---

## 2. Note Types & Taxonomy
We support the following structured templates from `dev/templates/`:
1. **DIWK** (`diwk`) - Pyramid of Insight analysis.
2. **Concept Map** (`concept_map`) - Directed, labeled system relationship mapping.
3. **Zettelkasten** (`zettelkasten`) - Atomic single-idea notes.
4. **SOAP** (`soap`) - Factual session and encounter logs.
5. **QEC** (`qec`) - Thesis question and evidence charts.
6. **Feynman** (`feynman`) - Simple jargon-free explanations.
7. **Cornell** (`cornell`) - Recall cues and summarizations.
8. **Eisenhower** (`eisenhower`) - Prioritization quad-boards.
9. **SDLC Project** (`sdlc_project`) - Software dev task tracking.
10. **Work Journal** (`work_journal`) - Daily progress tracking.
11. **Brain Dump** (`brain_dump`) - Raw inbox for capturing fleeing thoughts (starts as `status: raw`).

---

## 3. Roster Roles
The library operations are facilitated by 5 scripts located in `tools/`:
- **Librarian** - Validates front-matter formatting, links, and runs tests.
- **Cataloger** - Builds the visual link network and Markdown indexes.
- **Archivist** - Promotes files to production and manages living specifications.
- **Research Assistant** - Pulls web pages to resolve topic searches.
- **Library Scientist** - Performs taxonomical audits and designs new structures.
