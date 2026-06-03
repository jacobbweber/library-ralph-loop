#!/usr/bin/env python3
import os
import sys
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
                
        return metadata
    except Exception:
        return None

def build_catalog(library_dir, workspace):
    nodes = []
    links = []
    tags_map = {}
    categories_map = {}
    types_map = {}
    
    notes_data = {}
    
    if not library_dir.exists():
        return
        
    # Read files and compile basic details
    for root, _, files in os.walk(library_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
            
            file_path = Path(root) / file
            rel_path = file_path.relative_to(workspace)
            posix_path = str(rel_path).replace("\\", "/")
            
            # Skip compiling the index itself
            if posix_path.endswith("/index.md"):
                continue
                
            metadata = parse_yaml_front_matter(file_path)
            if not metadata:
                continue
                
            title = metadata.get("title", file_path.stem)
            note_type = metadata.get("type", "unknown")
            tags = metadata.get("tags", [])
            categories = metadata.get("categories", [])
            summary = metadata.get("summary", "No summary.")
            status = metadata.get("status", "draft")
            
            notes_data[posix_path] = {
                "title": title,
                "type": note_type,
                "tags": tags,
                "categories": categories,
                "summary": summary,
                "status": status,
                "links": []
            }
            
            # Populate mappings
            for t in tags:
                tags_map.setdefault(t, []).append(posix_path)
            for c in categories:
                categories_map.setdefault(c, []).append(posix_path)
            types_map.setdefault(note_type, []).append(posix_path)
            
            nodes.append({
                "id": posix_path,
                "title": title,
                "type": note_type,
                "tags": tags,
                "summary": summary,
                "status": status
            })

    # Resolve links to map connections
    for posix_path, data in notes_data.items():
        try:
            with open(workspace / posix_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
            
        found_links = re.findall(r"\]\((?:file:///)?([^\)]+\.md)\)", content)
        for link in found_links:
            link_clean = link.split("#")[0].strip()
            target_posix = link_clean
            
            if not target_posix.startswith("dev/") and not target_posix.startswith("prod/"):
                note_dir = Path(posix_path).parent
                target_path = (workspace / note_dir / target_posix).resolve()
                try:
                    target_posix = str(target_path.relative_to(workspace)).replace("\\", "/")
                except Exception:
                    continue
            
            if target_posix in notes_data and target_posix != posix_path:
                links.append({
                    "source": posix_path,
                    "target": target_posix,
                    "type": "references"
                })
                notes_data[posix_path]["links"].append(target_posix)

    # Save network_index.json
    network_path = library_dir / "network_index.json"
    with open(network_path, "w", encoding="utf-8") as f:
        json.dump({"nodes": nodes, "links": links}, f, indent=2)
    logger.info(f"Cataloger: Saved programmatic graph to {network_path.relative_to(workspace)}")

    # Write human-readable index.md
    index_path = library_dir / "index.md"
    
    # We construct the Markdown index content
    md = []
    md.append("---")
    md.append("id: \"system_index\"")
    md.append("title: \"Library Catalog Index\"")
    md.append("type: \"system_doc\"")
    md.append("tags: [\"index\", \"catalog\", \"system\"]")
    md.append("status: \"stable\"")
    md.append("summary: \"Automated Master Index of the Library files.\"")
    md.append("---")
    md.append("\n# Library Master Index Catalog\n")
    md.append(f"*This index is automatically rebuilt by `cataloger.py`.*")
    md.append(f"\nTotal Cataloged Notes: **{len(nodes)}**\n")
    
    # 1. Grouped by Category
    md.append("## 📁 Grouped by Category\n")
    if not categories_map:
        md.append("*No categories classified yet.*\n")
    for category, paths in sorted(categories_map.items()):
        md.append(f"### {category.capitalize()}")
        for p in sorted(paths):
            info = notes_data[p]
            md.append(f"- **[{info['title']}](file:///{workspace.as_posix()}/{p})** ({info['type']}) — *{info['summary']}*")
        md.append("")
        
    # 2. Grouped by Note Type
    md.append("## 📝 Grouped by Document Type\n")
    for ntype, paths in sorted(types_map.items()):
        md.append(f"### {ntype.upper()}")
        for p in sorted(paths):
            info = notes_data[p]
            md.append(f"- **[{info['title']}](file:///{workspace.as_posix()}/{p})** — *{info['summary']}*")
        md.append("")

    # 3. Grouped by Tags
    md.append("## 🏷️ Popular Tags\n")
    if not tags_map:
        md.append("*No tags applied yet.*\n")
    else:
        # Sort tags by count
        sorted_tags = sorted(tags_map.items(), key=lambda x: len(x[1]), reverse=True)
        for tag, paths in sorted_tags:
            paths_links = []
            for p in sorted(paths):
                info = notes_data[p]
                paths_links.append(f"[{info['title']}](file:///{workspace.as_posix()}/{p})")
            md.append(f"- **#{tag}** ({len(paths)}): {', '.join(paths_links)}")
        md.append("")
        
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    logger.info(f"Cataloger: Saved human catalog index to {index_path.relative_to(workspace)}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Rebuild Library Catalog Index.")
    parser.add_argument("--dir", type=str, default="dev/library", help="Directory to index (dev/library or prod/library)")
    
    args = parser.parse_args()
    
    workspace = Path(__file__).parent.parent.parent.resolve()
    target_dir = (workspace / args.dir).resolve()
    
    try:
        build_catalog(target_dir, workspace)
    except Exception:
        logger.exception("Unhandled exception in prod/tools/cataloger.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
