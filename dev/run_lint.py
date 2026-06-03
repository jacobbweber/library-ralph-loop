import subprocess
import sys
import os

# Ensure we are in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the librarian linter
result = subprocess.run(
    [sys.executable, "tools/librarian.py"],
    capture_output=True,
    text=True
)

print("=== Librarian Lint Output ===")
print(result.stdout)

if result.returncode != 0:
    print("=== Lint Errors ===")
    print(result.stderr)
    sys.exit(result.returncode)
else:
    print("=== Lint Passed ===")
    sys.exit(0)
