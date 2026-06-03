#!/usr/bin/env python3
import os
import sys
import argparse
import shutil
from pathlib import Path
import re

def parse_yaml_front_matter(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", content)
        if not match:
            return None
        
        yaml_text = match.group(1)
        metadata = {}
        for line in yaml_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip().strip('"').strip("'")
        return metadata
    except Exception:
        return None

def update_living_documentation(workspace):
    print("Archivist: Rebuilding living production documentation in prod/docs/...")
    prod_dir = workspace / "prod"
    docs_dir = prod_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Gather promoted tools
    tools = []
    tools_dir = prod_dir / "tools"
    if tools_dir.exists():
        for file in sorted(os.listdir(tools_dir)):
            if file.endswith(".py") or file.endswith(".ps1"):
                tools.append(file)
                
    # 2. Gather promoted templates
    templates = []
    templates_dir = prod_dir / "templates"
    if templates_dir.exists():
        for file in sorted(os.listdir(templates_dir)):
            if file.endswith(".md"):
                templates.append(file)

    # Rebuild prod/docs/architecture.md
    arch_content = f"""# Production Architecture Specifications
*This document is automatically updated by the Archivist.*

This library system is optimized for high-speed, token-efficient queries with a 64k context constraint.

## Stable Active Tools (The Roster)
The following management tools are active in the production environment:

"""
    if not tools:
        arch_content += "*No tools have been promoted to production yet.*\n"
    else:
        for t in tools:
            ext = Path(t).suffix
            lang = "Python 3" if ext == ".py" else "PowerShell 7"
            arch_content += f"- **{t}** ({lang}) — System utility located in `prod/tools/`.\n"
            
    arch_content += """
## Directory Layout Rules
All stable, human-readable assets are organized in the following root tree:
- `prod/library/` - Verified wiki articles, Zettelkastens, and clinical briefs.
- `prod/templates/` - Active layouts for structural note-taking.
- `prod/tools/` - Executable scripts for cataloging, search, and quality control.
"""
    with open(docs_dir / "architecture.md", "w", encoding="utf-8") as f:
        f.write(arch_content.strip() + "\n")
        
    # Rebuild prod/docs/system_blueprints.md
    blue_content = f"""# System Design & Document Blueprints
*This document is automatically updated by the Archivist.*

The library classification relies on custom note-taking structures designed for both human readability and low-token AI parsing.

## Production Note Templates
The following templates are registered and stable:

"""
    if not templates:
        blue_content += "*No templates have been promoted to production yet.*\n"
    else:
        for temp in templates:
            # Try to read template summary
            summary = "Structured note layout."
            metadata = parse_yaml_front_matter(templates_dir / temp)
            if metadata and "summary" in metadata:
                summary = metadata["summary"]
            blue_content += f"- **[{temp}](file:///prod/templates/{temp})** — {summary}\n"
            
    blue_content += """
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
"""
    with open(docs_dir / "system_blueprints.md", "w", encoding="utf-8") as f:
        f.write(blue_content.strip() + "\n")

    # Rebuild prod/docs/implementation.md
    impl_content = f"""# Production Implementation & Deployment Guide
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
"""
    with open(docs_dir / "implementation.md", "w", encoding="utf-8") as f:
        f.write(impl_content.strip() + "\n")
        
    print("Archivist: Production documentation successfully updated.")

def promote_file(rel_path_str, workspace):
    src_file = (workspace / rel_path_str).resolve()
    
    if not src_file.exists():
        print(f"Archivist Error: Source file {rel_path_str} does not exist.", file=sys.stderr)
        return False
        
    # Security check
    if not str(src_file).startswith(str(workspace)):
        print("Archivist Error: Security breach. File path is outside workspace.", file=sys.stderr)
        return False
        
    # Determine type of file and target location
    parts = Path(rel_path_str).parts
    
    if "dev" not in parts:
        print("Archivist Error: Can only promote files from 'dev/' branch/folder.", file=sys.stderr)
        return False
        
    # Validate markdown files before promotion
    if src_file.suffix == ".md" and "templates" not in parts:
        metadata = parse_yaml_front_matter(src_file)
        if not metadata:
            print(f"Archivist Error: {rel_path_str} is missing or has invalid front matter.", file=sys.stderr)
            return False
        status = metadata.get("status", "draft")
        if status != "stable":
            print(f"Archivist Warning: Note {rel_path_str} is status '{status}' (not 'stable'). Forcing promote anyway.", file=sys.stderr)
            
    # Map target path
    # Replace the "dev" segment with "prod"
    relative_to_dev = src_file.relative_to(workspace / "dev")
    dest_file = workspace / "prod" / relative_to_dev
    
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dest_file)
    print(f"Archivist: Promoted {rel_path_str} -> {dest_file.relative_to(workspace)}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Archivist Dev-to-Prod component promotion script.")
    parser.add_argument("--promote", type=str, help="Relative path of file in dev to promote (e.g. dev/tools/cataloger.py)")
    parser.add_argument("--update-docs", action="store_true", help="Force update of production living documentation")
    
    args = parser.parse_args()
    workspace = Path(__file__).parent.parent.parent.resolve()
    
    if args.promote:
        success = promote_file(args.promote, workspace)
        if success:
            update_living_documentation(workspace)
            sys.exit(0)
        else:
            sys.exit(1)
            
    if args.update_docs:
        update_living_documentation(workspace)
        sys.exit(0)
        
    parser.print_help()

if __name__ == "__main__":
    main()
