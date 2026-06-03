#!/usr/bin/env python3
"""
Ralph Loop Librarian Tool
Validates metadata, lints YAML front-matter, and runs self-tests.
Uses only standard Python libraries.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

# Configuration
REQUIRED_FIELDS = [
    "id", "title", "type", "tags", "categories", 
    "created", "modified", "status", "summary"
]
VALID_TYPES = [
    "zettelkasten", "diwk", "soap", "qec", "feynman", 
    "cornell", "sdlc_project", "work_journal", "brain_dump", 
    "research_brief", "system_doc"
]
VALID_STATUSES = ["raw", "draft", "review", "stable"]

def parse_frontmatter(content):
    """Extracts YAML front-matter from markdown content."""
    if not content.startswith('---'):
        return None
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None
    
    yaml_block = parts[1]
    metadata = {}
    
    # Simple YAML parser for key: value pairs
    for line in yaml_block.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Handle lists like [tag1, tag2]
            if value.startswith('[') and value.endswith(']'):
                value = [item.strip().strip('"').strip("'") for item in value[1:-1].split(',')]
            else:
                # Remove quotes
                value = value.strip('"').strip("'")
            
            metadata[key] = value
            
    return metadata

def validate_note(content, filepath=""):
    """Validates a note's front-matter."""
    errors = []
    metadata = parse_frontmatter(content)
    
    if not metadata:
        errors.append(f"Missing or invalid front-matter in {filepath}")
        return errors
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in metadata:
            errors.append(f"Missing required field '{field}' in {filepath}")
    
    # Validate types
    if 'type' in metadata and metadata['type'] not in VALID_TYPES:
        errors.append(f"Invalid type '{metadata['type']}' in {filepath}. Valid: {VALID_TYPES}")
        
    # Validate statuses
    if 'status' in metadata and metadata['status'] not in VALID_STATUSES:
        errors.append(f"Invalid status '{metadata['status']}' in {filepath}. Valid: {VALID_STATUSES}")
        
    # Validate date formats (YYYY-MM-DD)
    date_fields = ['created', 'modified']
    for field in date_fields:
        if field in metadata:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', metadata[field]):
                errors.append(f"Invalid date format for '{field}' in {filepath}. Expected YYYY-MM-DD")
                
    return errors

def lint_directory(directory):
    """Lints all markdown files in a directory."""
    results = {'files_checked': 0, 'errors': []}
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return {'error': f'Directory {directory} does not exist'}
        
    for file_path in dir_path.rglob('*.md'):
        try:
            content = file_path.read_text(encoding='utf-8')
            errors = validate_note(content, str(file_path))
            results['files_checked'] += 1
            if errors:
                results['errors'].extend(errors)
        except Exception as e:
            results['errors'].append(f"Error reading {file_path}: {str(e)}")
            
    return results

def run_tests():
    """Runs self-tests for the Librarian."""
    print("Running Librarian Self-Tests...")
    test_cases = [
        {
            "name": "Valid Note",
            "content": "---\nid: 202310271200\ntitle: Test Note\ntype: zettelkasten\ntags: [test]\ncategories: [test]\ncreated: 2023-10-27\nmodified: 2023-10-27\nstatus: raw\nsummary: A test note.\n---\nContent",
            "should_pass": True
        },
        {
            "name": "Missing ID",
            "content": "---\ntitle: Test Note\ntype: zettelkasten\ntags: [test]\ncategories: [test]\ncreated: 2023-10-27\nmodified: 2023-10-27\nstatus: raw\nsummary: A test note.\n---\nContent",
            "should_pass": False
        },
        {
            "name": "Invalid Type",
            "content": "---\nid: 202310271200\ntitle: Test Note\ntype: invalid_type\ntags: [test]\ncategories: [test]\ncreated: 2023-10-27\nmodified: 2023-10-27\nstatus: raw\nsummary: A test note.\n---\nContent",
            "should_pass": False
        },
        {
            "name": "Invalid Status",
            "content": "---\nid: 202310271200\ntitle: Test Note\ntype: zettelkasten\ntags: [test]\ncategories: [test]\ncreated: 2023-10-27\nmodified: 2023-10-27\nstatus: invalid_status\nsummary: A test note.\n---\nContent",
            "should_pass": False
        },
        {
            "name": "Invalid Date",
            "content": "---\nid: 202310271200\ntitle: Test Note\ntype: zettelkasten\ntags: [test]\ncategories: [test]\ncreated: 2023/10/27\nmodified: 2023-10-27\nstatus: raw\nsummary: A test note.\n---\nContent",
            "should_pass": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for case in test_cases:
        errors = validate_note(case['content'])
        is_pass = len(errors) == 0
        
        if is_pass == case['should_pass']:
            print(f"  [PASS] {case['name']}")
            passed += 1
        else:
            print(f"  [FAIL] {case['name']}")
            print(f"    Expected: {'Pass' if case['should_pass'] else 'Fail'}")
            print(f"    Got: {'Pass' if is_pass else 'Fail'}")
            if errors:
                print(f"    Errors: {errors}")
            failed += 1
            
    print(f"\nTests Run: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return failed == 0

def main():
    parser = argparse.ArgumentParser(description='Ralph Loop Librarian Tool')
    parser.add_argument('--run-tests', action='store_true', help='Run self-tests')
    parser.add_argument('--lint', type=str, help='Lint a directory')
    args = parser.parse_args()
    
    if args.run_tests:
        success = run_tests()
        sys.exit(0 if success else 1)
        
    if args.lint:
        results = lint_directory(args.lint)
        if 'error' in results:
            print(f"Error: {results['error']}")
            sys.exit(1)
            
        print(f"Linted {results['files_checked']} files.")
        if results['errors']:
            print(f"Found {len(results['errors'])} errors:")
            for error in results['errors']:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("All files passed linting.")
            sys.exit(0)
            
    parser.print_help()
    sys.exit(1)

if __name__ == '__main__':
    main()
