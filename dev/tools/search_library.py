#!/usr/bin/env python3
import os
import sys
import argparse
import json
import re
from pathlib import Path

# Configure centralized logging
_SCRIPT_DIR = Path(__file__).parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from logging_setup import configure_logging
configure_logging(script_name=Path(__file__).name)
import logging
logger = logging.getLogger(__name__)

def parse_yaml_front_matter(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Match front matter block
        match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", content)
        if not match:
            return None
        
        yaml_text = match.group(1)
        metadata = {}
        
        # Simple YAML parser (keys and string/list values)
        for line in yaml_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            
            # Parse list format: ["tag1", "tag2"] or [tag1, tag2]
            if val.startswith("[") and val.endswith("]"):
                list_vals = val[1:-1].split(",")
                metadata[key] = [v.strip().strip('"').strip("'") for v in list_vals if v.strip()]
            # Parse double-quoted string
            elif val.startswith('"') and val.endswith('"'):
                metadata[key] = val[1:-1]
            # Parse single-quoted string
            elif val.startswith("'") and val.endswith("'"):
                metadata[key] = val[1:-1]
            else:
                metadata[key] = val
                
        return metadata
    except Exception as e:
        logger.exception(f"Error parsing front matter in {file_path}: {e}")
        return None

def search_library(target_dir, args):
    results = []
    
    if not target_dir.exists():
        logger.error(f"Directory {target_dir} does not exist.")
        return results
        
    for root, _, files in os.walk(target_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
            
            file_path = Path(root) / file
            relative_path = file_path.relative_to(target_dir.parent.parent)
            
            metadata = parse_yaml_front_matter(file_path)
            if not metadata:
                continue
                
            # Filter matches
            matched = True
            
            if args.type and metadata.get("type", "").lower() != args.type.lower():
                matched = False
                
            if args.tag:
                tags = [t.lower() for t in metadata.get("tags", [])]
                if args.tag.lower() not in tags:
                    matched = False
                    
            if args.category:
                categories = [c.lower() for c in metadata.get("categories", [])]
                if args.category.lower() not in categories:
                    matched = False
                    
            if args.query:
                q = args.query.lower()
                title = metadata.get("title", "").lower()
                summary = metadata.get("summary", "").lower()
                
                # Check in content too
                content_match = False
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read().lower()
                    if q in file_content:
                        content_match = True
                except Exception:
                    pass
                    
                if q not in title and q not in summary and not content_match:
                    matched = False
                    
            if matched:
                results.append({
                    "path": str(relative_path).replace("\\", "/"),
                    "title": metadata.get("title", file_path.stem),
                    "type": metadata.get("type", "unknown"),
                    "tags": metadata.get("tags", []),
                    "categories": metadata.get("categories", []),
                    "summary": metadata.get("summary", "No summary provided."),
                    "modified": metadata.get("modified", "")
                })
                
    return results

def main():
    parser = argparse.ArgumentParser(description="Search the Library metadata and files efficiently.")
    parser.add_argument("--dir", type=str, default="dev/library", help="Directory to search (dev/library or prod/library)")
    parser.add_argument("--tag", type=str, help="Filter by tag")
    parser.add_argument("--category", type=str, help="Filter by category")
    parser.add_argument("--type", type=str, help="Filter by note type")
    parser.add_argument("--query", type=str, help="Free-text search in title, summary, or content")
    parser.add_argument("--output", type=str, choices=["json", "table"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    workspace = Path(__file__).parent.parent.parent.resolve()
    target_dir = (workspace / args.dir).resolve()
    
    results = search_library(target_dir, args)
    
    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        # Table format
        if not results:
            logger.info("No matching files found.")
            return
        
        # Print markdown table
        print("| Title | Path | Type | Tags | Summary |")
        print("|---|---|---|---|---|")
        for r in results:
            tags_str = ", ".join(r["tags"])
            print(f"| {r['title']} | [{r['path']}](file:///{workspace.as_posix()}/{r['path']}) | {r['type']} | {tags_str} | {r['summary']} |")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Unhandled exception in search_library.py")
        sys.exit(1)
