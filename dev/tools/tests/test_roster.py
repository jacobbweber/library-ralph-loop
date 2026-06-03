#!/usr/bin/env python3
# Roster Tools import unit test
# Used to verify all scripts in dev/tools compile and export correctly.

import os
import sys
from pathlib import Path

def test_imports():
    workspace = Path(__file__).parent.parent.parent.parent.resolve()
    tools_dir = str(workspace / "dev" / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
        
    # Verify imports
    import search_library
    import cataloger
    import librarian
    import archivist
    import research_assistant
    import library_scientist
    import web_search
    
    print("test_imports: All tools imported successfully!")
    return True

if __name__ == "__main__":
    if test_imports():
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)
