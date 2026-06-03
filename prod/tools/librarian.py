#!/usr/bin/env python3
import os
import sys
import argparse
import re
import json
from pathlib import Path

# Config
ALLOWED_TYPES = {
    "diwk", "concept_map", "zettelkasten", "soap", "qec", 
    "feynman", "cornell", "eisenhower", "sdlc_project", 
    "work_journal", "brain_dump", "research_brief", "system_doc"
}

ALLOWED_STATUSES = {"raw", "draft", "review", "stable"}

def parse_yaml_front_matter(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", content)
        if not match:
            return None, "Missing front matter delimiters (---)"
        
        yaml_text = match.group(1)
        metadata = {}
        
        for line in yaml_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            
            if val.startswith("[") and val.endswith("]"):
                list_vals = val[1:-1].split(",")
                metadata[key] = [v.strip().strip('"').strip("'") for v in list_vals if v.strip()]
            elif val.startswith('"') and val.endswith('"'):
                metadata[key] = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                metadata[key] = val[1:-1]
            else:
                metadata[key] = val
                
        return metadata, None
    except Exception as e:
        return None, str(e)

def lint_library(library_dir, workspace):
    errors = []
    notes = {}
    
    if not library_dir.exists():
        return errors, notes
        
    # First pass: Parse all metadata
    for root, _, files in os.walk(library_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
            
            file_path = Path(root) / file
            relative_path = file_path.relative_to(workspace)
            posix_path = str(relative_path).replace("\\", "/")
            
            metadata, err = parse_yaml_front_matter(file_path)
            if err:
                errors.append(f"LINT ERROR: [{posix_path}] Invalid front matter syntax: {err}")
                continue
                
            notes[posix_path] = {
                "path": file_path,
                "metadata": metadata,
                "content": ""
            }
            
            # Read content for link parsing
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    notes[posix_path]["content"] = f.read()
            except Exception:
                pass
                
            # Check required fields
            for field in ["id", "title", "type", "tags", "status"]:
                if field not in metadata:
                    errors.append(f"LINT ERROR: [{posix_path}] Missing required front matter field: '{field}'")
            
            # Check type validity
            note_type = metadata.get("type", "")
            if note_type and note_type not in ALLOWED_TYPES:
                errors.append(f"LINT ERROR: [{posix_path}] Invalid note type '{note_type}'. Must be one of: {', '.join(sorted(ALLOWED_TYPES))}")
                
            # Check status validity
            status = metadata.get("status", "")
            if status and status not in ALLOWED_STATUSES:
                errors.append(f"LINT ERROR: [{posix_path}] Invalid status '{status}'. Must be one of: {', '.join(ALLOWED_STATUSES)}")
                
    # Second pass: Check links and backlinks
    for posix_path, note_info in notes.items():
        content = note_info["content"]
        # Find markdown links: [text](file:///workspace_relative_path.md) or [text](relative_path.md)
        links = re.findall(r"\]\((?:file:///)?([^\)]+\.md)\)", content)
        
        for link in links:
            # Clean link query parameters or anchors
            link_clean = link.split("#")[0].strip()
            
            # Check absolute workspace link vs relative link
            target_posix = link_clean
            if not target_posix.startswith("dev/") and not target_posix.startswith("prod/"):
                # It's a relative link from the note
                note_dir = Path(posix_path).parent
                target_path = (workspace / note_dir / target_posix).resolve()
                try:
                    target_posix = str(target_path.relative_to(workspace)).replace("\\", "/")
                except Exception:
                    errors.append(f"LINT ERROR: [{posix_path}] Broken relative link: '{link}' (points outside workspace)")
                    continue
            
            if target_posix not in notes:
                # Check if it points to a physical file that exists in prod or dev
                phys_path = workspace / target_posix
                if not phys_path.exists():
                    errors.append(f"LINT ERROR: [{posix_path}] Broken link to file: '{link_clean}'")
                    
    return errors, notes

def run_self_tests(workspace):
    # Runs automated checks on the tools to ensure everything is functional.
    print("Self-Tests: Running checks on tools...")
    
    tools_dir = str(workspace / "dev" / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
        
    # Test 1: Import check and mock search
    try:
        from search_library import search_library
        class MockArgs:
            type = None
            tag = None
            category = None
            query = None
        
        # Test searching the templates directory (should have some .md templates)
        target_dir = workspace / "dev" / "templates"
        results = search_library(target_dir, MockArgs())
        print(f"Self-Tests: Search library loaded. Found {len(results)} mock templates.")
    except Exception as e:
        return False, f"Self-Test Search Failed: {e}"
        
    # Test 2: Web Search parser validation
    try:
        from web_search import clean_html
        test_html = "<p>Hello &quot;World&quot;</p>"
        cleaned = clean_html(test_html)
        if cleaned != 'Hello "World"':
            return False, f"Self-Test Web Search Scraper Failed: expected clean text, got '{cleaned}'"
        print("Self-Tests: Web search utilities checked.")
    except Exception as e:
        return False, f"Self-Test Web Search Clean Failed: {e}"
        
    # Test 3: Cataloger import check
    cataloger_py = workspace / "dev" / "tools" / "cataloger.py"
    if cataloger_py.exists():
        try:
            # Check script syntax
            with open(cataloger_py, "r", encoding="utf-8") as f:
                compile(f.read(), str(cataloger_py), "exec")
            print("Self-Tests: Cataloger syntax validated.")
        except Exception as e:
            return False, f"Self-Test Cataloger Syntax Check Failed: {e}"
            
    print("Self-Tests: All tool checks PASSED.")
    return True, "All tests passed"

def main():
    parser = argparse.ArgumentParser(description="Librarian Quality Assurance Linter.")
    parser.add_argument("--dir", type=str, default="dev/library", help="Directory to lint (dev/library or prod/library)")
    parser.add_argument("--run-tests", action="store_true", help="Run automated test suite for system scripts")
    
    args = parser.parse_args()
    
    workspace = Path(__file__).parent.parent.parent.resolve()
    target_dir = (workspace / args.dir).resolve()
    
    # 1. Run tests if requested
    if args.run_tests:
        success, msg = run_self_tests(workspace)
        if not success:
            print(f"TEST RUNNER FAILED:\n{msg}", file=sys.stderr)
            sys.exit(1)
            
    # 2. Run metadata linter
    print(f"Librarian: Linting folder {args.dir}...")
    errors, notes = lint_library(target_dir, workspace)
    
    if errors:
        print(f"\nLibrarian Linter: Found {len(errors)} issues:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)
    else:
        print("Librarian Linter: Clean repository! 0 errors found.")
        sys.exit(0)

if __name__ == "__main__":
    main()
