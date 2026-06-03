# Production Implementation & Deployment Guide
*This document is automatically updated by the Archivist.*

## Installation & Setup
This system is completely portable and contains no external package dependencies.

### Running Search Queries
To run a high-speed metadata search:
```bash
# Python
python prod/tools/search_library.py --dir prod/library --tag target_tag

# PowerShell 7
pwsh prod/tools/search_library.ps1 -Dir prod/library -Tag target_tag
```

### Library Indexing & Cataloging
To rebuild the dynamic index file (`prod/library/index.md`) and check backlinks:
```bash
python prod/tools/cataloger.py --dir prod/library
```
