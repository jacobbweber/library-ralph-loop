# System Design & Document Blueprints
*This document is automatically updated by the Archivist.*

The library classification relies on custom note-taking structures designed for both human readability and low-token AI parsing.

## Production Note Templates
The following templates are registered and stable:

- **[brain_dump.md](file:///prod/templates/brain_dump.md)** — Brain dump template for capturing raw, unprocessed ideas and temporary references.
- **[concept_map.md](file:///prod/templates/concept_map.md)** — Concept Map system hub template for mapping node relationships and feedback loops.
- **[cornell.md](file:///prod/templates/cornell.md)** — Cornell notes template for lecture, reading, or meeting recall.
- **[diwk.md](file:///prod/templates/diwk.md)** — Pyramid of Insight (DIKW) template for data-driven strategic actions.
- **[eisenhower.md](file:///prod/templates/eisenhower.md)** — Eisenhower Matrix template for urgency and importance task triage.
- **[feynman.md](file:///prod/templates/feynman.md)** — Feynman Technique study template for simplifying complex concepts using analogies.
- **[qec.md](file:///prod/templates/qec.md)** — Question, Evidence, Conclusion (QEC) template for logical thesis analysis.
- **[sdlc_project.md](file:///prod/templates/sdlc_project.md)** — SDLC project template tracking technical scope, milestones, sprint backlogs, and test plans.
- **[soap.md](file:///prod/templates/soap.md)** — SOAP note template for structured clinical or consulting sessions.
- **[work_journal.md](file:///prod/templates/work_journal.md)** — Work journal template for tracking daily/weekly accomplishments, blockers, and decisions.
- **[zettelkasten.md](file:///prod/templates/zettelkasten.md)** — Zettelkasten atomic note template for single-idea indexing.

## Standard YAML Metadata Schema
All files in the library database must validate against this format:
```yaml
---
id: "YYYYMMDDHHMM"      # Strict 12-digit timestamp identifier
title: "Title Name"     # Clear, human-readable title
type: "zettelkasten"    # Registered note structure type
tags: [tag1, tag2]       # Category tags for search indexing
categories: [cat1]      # Broad namespace categorization
created: "YYYY-MM-DD"   # ISO created date
modified: "YYYY-MM-DD"  # ISO last modified date
status: "stable"        # Must be 'stable' to remain in production
summary: "Single-sentence summary of the note contents."
---
```
