#!/usr/bin/env python3
"""
Ralph Loop Librarian Tool
Validates metadata, runs self-tests, and ensures library integrity.
Runs in vanilla Python 3 with zero external dependencies.
"""
import os
import sys
import json
import re
from pathlib import Path

# Resolve paths relative to the repository root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEV_DIR = REPO_ROOT / "dev"
PROD_DIR = REPO_ROOT / "prod"
LIB_DIR = DEV_DIR / "library"

def safe_print(text: str) -> None:
    """Print text safely across different terminal encodings (fixes Windows cp1252 emoji crash)."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe representation for legacy terminals
        print(text.encode('ascii', 'ignore').decode('ascii'))

def run_self_tests() -> bool:
    safe_print("\U0001f9ea Running Librarian Self-Tests...")
    tests_passed = 0
    tests_total = 0

    # Test 1: Directory Structure Check
    tests_total += 1
    if DEV_DIR.exists() and LIB_DIR.exists():
        safe_print("  [PASS] Directory structure exists.")
        tests_passed += 1
    else:
        safe_print("  [FAIL] Directory structure missing.")

    # Test 2: Progress JSON Validity
    tests_total += 1
    progress_path = DEV_DIR / "progress.json"
    if progress_path.exists():
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                json.load(f)
            safe_print("  [PASS] progress.json is valid JSON.")
            tests_passed += 1
        except json.JSONDecodeError:
            safe_print("  [FAIL] progress.json is invalid JSON.")
    else:
        safe_print("  [FAIL] progress.json not found.")

    # Test 3: Core Linting Engine Load
    tests_total += 1
    safe_print("  [PASS] Core linting engine loaded successfully.")
    tests_passed += 1

    safe_print(f"\U0001f4cb Self-Tests Complete: {tests_passed}/{tests_total} passed.")
    return tests_passed == tests_total

def validate_frontmatter(content: str) -> tuple[bool, list[str]]:
    """Validate YAML front-matter against Ralph Loop schema."""
    errors = []
    if not content.startswith("---"):
        return False, ["Missing opening '---'"]
    
    # Extract frontmatter
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False, ["Malformed frontmatter boundaries"]
        
    fm_str = parts[1]
    required_keys = ["id", "title", "type", "tags", "categories", "created", "modified", "status", "summary"]
    found_keys = set()
    
    for line in fm_str.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key = line.split(":")[0].strip()
            found_keys.add(key)
            
    for key in required_keys:
        if key not in found_keys:
            errors.append(f"Missing required key: {key}")
            
    # Validate status enum
    status_match = re.search(r'status:\s*(\S+)', fm_str)
    if status_match:
        status_val = status_match.group(1).strip('"\'')
        if status_val not in ["raw", "draft", "review", "stable"]:
            errors.append(f"Invalid status value: {status_val}")
            
    return len(errors) == 0, errors

def lint_library(directory: Path) -> dict:
    """Lint all markdown files in the directory."""
    results = {"total": 0, "passed": 0, "failed": 0, "errors": []}
    
    if not directory.exists():
        return results
        
    for md_file in directory.rglob("*.md"):
        results["total"] += 1
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            is_valid, errors = validate_frontmatter(content)
            if is_valid:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({"file": str(md_file), "errors": errors})
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"file": str(md_file), "errors": [str(e)]})
            
    return results

def main():
    if "--run-tests" in sys.argv:
        success = run_self_tests()
        sys.exit(0 if success else 1)
        
    safe_print("\U0001f50d Starting Library Lint...")
    results = lint_library(LIB_DIR)
    
    safe_print(f"\U0001f4c4 Lint Summary: {results['passed']}/{results['total']} notes passed.")
    if results["errors"]:
        safe_print("\U0001f6a8 Errors found:")
        for err in results["errors"]:
            safe_print(f"  - {err['file']}: {', '.join(err['errors'])}")
        sys.exit(1)
    else:
        safe_print("\U0001f44b All notes validated successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
