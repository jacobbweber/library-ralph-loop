#!/usr/bin/env python3
import sys
import argparse
import json
import urllib.request
import urllib.parse
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

def clean_html(text):
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common HTML entities
    text = text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#x27;", "'").replace("&nbsp;", " ")
    return text.strip()

def search_wikipedia(query):
    # Query wikipedia search
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded_query}&limit=5&namespace=0&format=json"
    
    try:
        req = urllib.request.Request(search_url, headers={"User-Agent": "RalphLoopLibrary/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        results = []
        titles = data[1]
        summaries = data[2]
        links = data[3]
        
        for i in range(len(titles)):
            results.append({
                "title": titles[i],
                "snippet": summaries[i],
                "url": links[i],
                "source": "Wikipedia"
            })
        return results
    except Exception as e:
        logger.exception(f"Wikipedia search failed: {e}")
        return []

def search_duckduckgo(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    # We must use a browser-like User Agent otherwise DuckDuckGo blocks us
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8")
            
        # Parse results using regex.
        # DDG HTML results are inside container classes
        # Title/URL regex:
        # <a class="result__url" href="[url]">[url_display]</a>
        # Snippet regex:
        # <a class="result__snippet" ...> [snippet] </a>
        
        results = []
        
        # Match result containers
        # We can extract links and snippets by finding result__snippet and working backwards,
        # or matching results__links links.
        # Let's find result snippets and result URLs
        urls = re.findall(r'<a class="result__url" href="([^"]+)"', html)
        snippets = re.findall(r'<a class="result__snippet"[^>]*>([\s\S]*?)</a>', html)
        titles = re.findall(r'<a class="result__link"[^>]*>([\s\S]*?)</a>', html)
        
        limit = min(len(urls), len(snippets), len(titles), 5)
        for i in range(limit):
            # Clean up URLs (DDG sometimes redirects them: e.g. /l/?kh=-1&uddg=https%3A%2F%2F...)
            target_url = urls[i]
            if "/l/?kh=" in target_url:
                parsed = urllib.parse.urlparse(target_url)
                qs = urllib.parse.parse_qs(parsed.query)
                if "uddg" in qs:
                    target_url = qs["uddg"][0]
                    
            results.append({
                "title": clean_html(titles[i]),
                "snippet": clean_html(snippets[i]),
                "url": target_url,
                "source": "DuckDuckGo"
            })
            
        return results
    except Exception as e:
        logger.exception(f"DuckDuckGo search failed: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Zero-dependency Web Search Scraper.")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--engine", type=str, choices=["ddg", "wiki", "auto"], default="auto", help="Search engine selection")
    parser.add_argument("--output", type=str, choices=["json", "markdown"], default="markdown", help="Output format")
    
    args = parser.parse_args()
    
    results = []
    if args.engine == "wiki":
        results = search_wikipedia(args.query)
    elif args.engine == "ddg":
        results = search_duckduckgo(args.query)
    else:
        # Auto: try Wikipedia first for conceptual searches, then fall back or merge with DDG
        # If query looks like a specific concept (few words), query Wikipedia
        word_count = len(args.query.split())
        if word_count <= 4:
            results = search_wikipedia(args.query)
        
        # If no wiki results or query is complex, query DDG
        if not results:
            results = search_duckduckgo(args.query)
            
    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        # Markdown output
        print(f"# Search Results for: {args.query}\n")
        if not results:
            logger.info("No results found.")
            return
            
        for i, r in enumerate(results, 1):
            print(f"### {i}. {r['title']}")
            print(f"- **Source**: {r['source']}")
            print(f"- **URL**: {r['url']}")
            print(f"- **Snippet**: {r['snippet']}\n")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Unhandled exception in web_search.py")
        sys.exit(1)
