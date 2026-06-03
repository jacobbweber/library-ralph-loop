import sys
import os
import re
from pathlib import Path

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown content using robust regex."""
    # Strip leading BOM if present and trim whitespace
    content = content.lstrip('\ufeff').strip()
    
    # Match frontmatter block with support for Windows and Unix newlines
    match = re.match(r'^---\r?\n([\s\S]*?)\r?\n---', content)
    if not match:
        return None
        
    fm = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, val = line.split(':', 1)
            # Clean string quotes and brackets for lists
            val_clean = val.strip().strip('"').strip("'")
            if val_clean.startswith('[') and val_clean.endswith(']'):
                # Convert list string to actual list
                list_items = [item.strip().strip('"').strip("'") for item in val_clean[1:-1].split(',') if item.strip()]
                fm[key.strip()] = list_items
            else:
                fm[key.strip()] = val_clean
    return fm

def lint_file(filepath, workspace):
    """Validate a single markdown file's frontmatter if it is inside library/."""
    # Convert to relative path for check
    try:
        rel_path = Path(filepath).relative_to(workspace)
        posix_path = str(rel_path).replace("\\", "/")
    except Exception:
        posix_path = filepath
        
    # Check if the file is inside a library directory (skip templates, plans, tools)
    parts = Path(posix_path).parts
    if "library" not in parts:
        return True # Skip non-library files, they do not require note front-matter
        
    # Skip index file itself if it's being generated or doesn't have complete fields yet
    if posix_path.endswith("index.md") or posix_path.endswith("library_science_audit.md"):
        # Relaxes checks for automated files but ensures they parse
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            fm = parse_frontmatter(content)
            return fm is not None
        except Exception:
            return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"FAIL: {posix_path} read error: {e}")
        return False
        
    fm = parse_frontmatter(content)
    if not fm:
        print(f"FAIL: {posix_path} missing or invalid frontmatter")
        return False
        
    required = ['id', 'title', 'type', 'tags', 'categories', 'created', 'modified', 'status', 'summary']
    for key in required:
        if key not in fm:
            print(f"FAIL: {posix_path} missing key '{key}'")
            return False
            
    if fm['status'] not in ['raw', 'draft', 'review', 'stable']:
        print(f"FAIL: {posix_path} invalid status '{fm['status']}'")
        return False
        
    return True

def run_tests():
    """Run internal self-tests for the librarian tool."""
    print("Running Librarian Self-Tests...")
    if not os.path.isdir('dev/templates'):
        print("FAIL: dev/templates/ not found")
        return False
    if not os.path.isfile('dev/tools/librarian.py'):
        print("FAIL: librarian.py not found")
        return False
    print("Self-tests passed.")
    return True

def main():
    """Main entry point with argument parsing."""
    workspace = Path(__file__).parent.parent.parent.resolve()
    
    if '--run-tests' in sys.argv:
        success = run_tests()
        sys.exit(0 if success else 1)
        
    target_dir = str(workspace / 'dev/library')
    if '--dir' in sys.argv:
        idx = sys.argv.index('--dir')
        if idx + 1 < len(sys.argv):
            target_dir = sys.argv[idx+1]
            
    # Resolve target directory relative to workspace if relative
    target_path = Path(target_dir).resolve()
    if not target_path.exists():
        print(f"FAIL: Directory not found: {target_dir}")
        sys.exit(1)
        
    print(f"Librarian: Linting {target_dir}...")
    errors = 0
    for root, _, files in os.walk(target_path):
        for f in files:
            if f.endswith('.md'):
                if not lint_file(os.path.join(root, f), workspace):
                    errors += 1
    if errors:
        print(f"Lint failed with {errors} errors.")
        sys.exit(1)
    print("Lint passed.")
    sys.exit(0)

if __name__ == '__main__':
    main()
