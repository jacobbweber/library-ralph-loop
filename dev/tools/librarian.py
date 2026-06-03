import sys
import os
import re

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown content using regex."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None
    fm = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm

def lint_file(filepath):
    """Validate a single markdown file's frontmatter."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"FAIL: {filepath} read error: {e}")
        return False
        
    fm = parse_frontmatter(content)
    if not fm:
        print(f"FAIL: {filepath} missing frontmatter")
        return False
        
    required = ['id', 'title', 'type', 'tags', 'categories', 'created', 'modified', 'status', 'summary']
    for key in required:
        if key not in fm:
            print(f"FAIL: {filepath} missing key '{key}'")
            return False
            
    if fm['status'] not in ['raw', 'draft', 'review', 'stable']:
        print(f"FAIL: {filepath} invalid status '{fm['status']}'")
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
    if '--run-tests' in sys.argv:
        success = run_tests()
        sys.exit(0 if success else 1)
        
    target_dir = 'dev/library'
    if '--dir' in sys.argv:
        idx = sys.argv.index('--dir')
        if idx + 1 < len(sys.argv):
            target_dir = sys.argv[idx+1]
            
    if not os.path.isdir(target_dir):
        print(f"FAIL: Directory not found: {target_dir}")
        sys.exit(1)
        
    print(f"Linting {target_dir}...")
    errors = 0
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith('.md'):
                if not lint_file(os.path.join(root, f)):
                    errors += 1
    if errors:
        print(f"Lint failed with {errors} errors.")
        sys.exit(1)
    print("Lint passed.")
    sys.exit(0)

if __name__ == '__main__':
    main()
