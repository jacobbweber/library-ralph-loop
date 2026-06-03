# Production Architecture Specifications
*This document is automatically updated by the Archivist.*

This library system is optimized for high-speed, token-efficient queries with a 64k context constraint.

## Stable Active Tools (The Roster)
The following management tools are active in the production environment:

- **archivist.ps1** (PowerShell 7) — System utility located in `prod/tools/`.
- **archivist.py** (Python 3) — System utility located in `prod/tools/`.
- **cataloger.ps1** (PowerShell 7) — System utility located in `prod/tools/`.
- **cataloger.py** (Python 3) — System utility located in `prod/tools/`.
- **librarian.ps1** (PowerShell 7) — System utility located in `prod/tools/`.
- **librarian.py** (Python 3) — System utility located in `prod/tools/`.
- **library_scientist.ps1** (PowerShell 7) — System utility located in `prod/tools/`.
- **library_scientist.py** (Python 3) — System utility located in `prod/tools/`.
- **research_assistant.ps1** (PowerShell 7) — System utility located in `prod/tools/`.
- **research_assistant.py** (Python 3) — System utility located in `prod/tools/`.
- **search_library.ps1** (PowerShell 7) — System utility located in `prod/tools/`.
- **search_library.py** (Python 3) — System utility located in `prod/tools/`.
- **web_search.ps1** (PowerShell 7) — System utility located in `prod/tools/`.
- **web_search.py** (Python 3) — System utility located in `prod/tools/`.

## Directory Layout Rules
All stable, human-readable assets are organized in the following root tree:
- `prod/library/` - Verified wiki articles, Zettelkastens, and clinical briefs.
- `prod/templates/` - Active layouts for structural note-taking.
- `prod/tools/` - Executable scripts for cataloging, search, and quality control.
