#!/usr/bin/env python3
import os
import sys
import argparse
import time
import subprocess
import json
from pathlib import Path
import re

# Configure centralized logging
_SCRIPT_DIR = Path(__file__).parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from logging_setup import configure_logging
configure_logging(script_name=Path(__file__).name)
import logging
logger = logging.getLogger(__name__)

def create_research_brief(query, workspace):
    # Run the web_search script to get JSON results
    web_search_py = workspace / "dev" / "tools" / "web_search.py"
    if not web_search_py.exists():
        logger.error("Research Assistant Error: dev/tools/web_search.py not found.")
        return False
        
    logger.info(f"Research Assistant: Querying web search for '{query}'...")
    try:
        res = subprocess.run(
            [sys.executable, str(web_search_py), query, "--output", "json"],
            capture_output=True, text=True, check=True
        )
        results = json.loads(res.stdout)
    except Exception as e:
        logger.exception("Research Assistant Error executing search")
        return False
        
    if not results:
        logger.warning("Research Assistant: No search results returned.")
        return False
        
    # Generate clean filename from query
    clean_query_name = "".join([c if c.isalnum() else "_" for c in query.lower()]).strip("_")
    clean_query_name = re.sub(r"_+", "_", clean_query_name)[:50]
    
    timestamp = time.strftime("%Y%m%d%H%M")
    date_str = time.strftime("%Y-%m-%d")
    
    briefs_dir = workspace / "dev" / "library" / "research_briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    
    brief_path = briefs_dir / f"brief_{clean_query_name}.md"
    
    # Compile synthesis
    md = []
    md.append("---")
    md.append(f"id: \"{timestamp}\"")
    md.append(f"title: \"Research Brief: {query}\"")
    md.append("type: \"research_brief\"")
    md.append("tags: [\"research\", \"web_search\", \"synthesis\"]")
    md.append("categories: [\"research\"]")
    md.append(f"created: \"{date_str}\"")
    md.append(f"modified: \"{date_str}\"")
    md.append("status: \"draft\"")
    md.append(f"summary: \"Research synthesis and sources gathered for query: {query}.\"")
    md.append("---")
    md.append(f"\n# Research Brief: {query}\n")
    md.append(f"**Date Compiled**: {date_str}  ")
    md.append(f"**Status**: Draft  ")
    md.append(f"**Source**: Automated Web Crawl\n")
    
    md.append("## 🔍 Core Question / Topic")
    md.append(f"> What are the key details, definitions, and systems associated with **{query}**?\n")
    
    md.append("## 📊 Synthesized Findings (Information & Knowledge)")
    md.append("Here is the synthesized summary of observations from search engines:\n")
    
    for i, r in enumerate(results, 1):
        md.append(f"### {i}. {r['title']}")
        md.append(f"- **Source**: {r['source']}")
        md.append(f"- **URL**: {r['url']}")
        md.append(f"- **Summary**: {r['snippet']}\n")
        
    md.append("## 💡 Architectural Insights / Wisdom")
    md.append("Based on the data collected above, the following systems, actions, or ideas are proposed:")
    md.append(f"- [ ] Propose library integration or note structures for: *{query}*.")
    md.append("- [ ] Review backlinks and expand concepts to Zettelkasten nodes.\n")
    
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
        
    relative_brief_path = brief_path.relative_to(workspace)
    logger.info(f"Research Assistant: Created research brief at {relative_brief_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Research Assistant for compiling web search briefs.")
    parser.add_argument("query", type=str, help="Search query to research")
    
    args = parser.parse_args()
    workspace = Path(__file__).parent.parent.parent.resolve()
    try:
        success = create_research_brief(args.query, workspace)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        logger.exception("Unhandled exception in research_assistant.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
