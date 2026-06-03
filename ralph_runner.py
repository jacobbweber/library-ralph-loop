#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

# Paths
WORKSPACE = Path(__file__).parent.resolve()
CONFIG_PATH = WORKSPACE / "config.json"
PROMPT_PATH = WORKSPACE / "PROMPT.md"
DEV_DIR = WORKSPACE / "dev"
PLAN_PATH = DEV_DIR / "plan.md"
PROGRESS_PATH = DEV_DIR / "progress.json"
QUEUE_PATH = DEV_DIR / "research_queue.json"
ERROR_LOG_PATH = DEV_DIR / "last_error.log"

def load_config():
    if not CONFIG_PATH.exists():
        print(f"Error: {CONFIG_PATH} not found. Please restore it.")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def git_is_clean():
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=WORKSPACE, check=True)
        return len(res.stdout.strip()) == 0
    except Exception as e:
        print(f"Warning: Git check failed: {e}")
        return True

def run_git_commit(msg):
    try:
        subprocess.run(["git", "add", "-A"], cwd=WORKSPACE, check=True)
        # Check if there is anything to commit
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=WORKSPACE)
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", msg], cwd=WORKSPACE, check=True)
            print("Git: Committed changes successfully.")
        else:
            print("Git: No changes to commit.")
    except Exception as e:
        print(f"Error during git commit: {e}")

def run_git_rollback():
    print("Warning: Running verification failed. Initiating Git rollback...")
    try:
        # Revert changes to tracked files
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=WORKSPACE, check=True)
        # Remove untracked files/directories, EXCEPT for .gitignored ones (like dev/last_error.log)
        subprocess.run(["git", "clean", "-fd"], cwd=WORKSPACE, check=True)
        print("Git: Reverted working tree to last successful state.")
    except Exception as e:
        print(f"Critical: Git rollback failed: {e}")

def run_validation():
    # Runs the Librarian validation script.
    # Defaulting to librarian.py if it exists, otherwise returning True
    librarian_py = DEV_DIR / "tools" / "librarian.py"
    if not librarian_py.exists():
        print("Validation: dev/tools/librarian.py not found yet. Skipping validation (bootstrapping phase).")
        return True, "No librarian script yet"
    
    print("Validation: Running dev/tools/librarian.py --run-tests...")
    try:
        # Running Python 3. In Windows, python may be python or py or python3.
        # We try running the current executable.
        res = subprocess.run([sys.executable, str(librarian_py), "--run-tests"], capture_output=True, text=True, cwd=WORKSPACE)
        if res.returncode == 0:
            print("Validation: Success! All checks passed.")
            return True, res.stdout
        else:
            print(f"Validation: Failed with exit code {res.returncode}")
            error_output = f"EXIT CODE: {res.returncode}\n\nSTDOUT:\n{res.stdout}\n\nSTDERR:\n{res.stderr}"
            return False, error_output
    except Exception as e:
        print(f"Validation: Error executing script: {e}")
        return False, str(e)

def compile_context(config):
    # Compile prompt components into a single payload
    context_parts = []
    
    # 1. Base Developer Prompt
    if PROMPT_PATH.exists():
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            context_parts.append(f"=== SYSTEM INSTRUCTIONS (PROMPT.md) ===\n{f.read()}")
    else:
        # Placeholder if PROMPT.md does not exist yet
        context_parts.append("=== SYSTEM INSTRUCTIONS ===\nYou are a Ralph Loop Builder Agent. Help design and build the Library system.")
        
    # 2. Critical error state (if any)
    if ERROR_LOG_PATH.exists():
        with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
            context_parts.append(
                f"=== [CRITICAL ERROR] PREVIOUS RUN FAILED ===\n"
                f"Your previous attempt was rolled back due to verification failures.\n"
                f"You must resolve the root cause of this error before proceeding with any other tasks.\n\n"
                f"Error Details:\n{f.read()}\n"
                f"=========================================="
            )
            
    # 3. Plan & Roadmap
    if PLAN_PATH.exists():
        with open(PLAN_PATH, "r", encoding="utf-8") as f:
            context_parts.append(f"=== CURRENT ROADMAP & PLANS (dev/plan.md) ===\n{f.read()}")
            
    # 4. PRD Progress Checklist
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            context_parts.append(f"=== PROGRESS STATUS (dev/progress.json) ===\n{f.read()}")
            
    # 5. Research Queue
    if QUEUE_PATH.exists():
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            context_parts.append(f"=== RESEARCH QUEUE (dev/research_queue.json) ===\n{f.read()}")
            
    # 6. Current Directory Map (Helper for model to know file structure)
    context_parts.append(f"=== CURRENT WORKING DIRECTORY ===\nRunning in workspace: {WORKSPACE}")
    
    return "\n\n".join(context_parts)

def parse_and_apply_changes(response_text):
    # Find all <file path="...">...</file> tags
    file_pattern = re.compile(r'<file path="([^"]+)">([\s\S]*?)<\/file>')
    matches = file_pattern.findall(response_text)
    
    updated_files = []
    for path_str, content in matches:
        target_path = (WORKSPACE / path_str).resolve()
        
        # Security check: Ensure file is written within workspace
        if not str(target_path).startswith(str(WORKSPACE)):
            print(f"Warning: Model attempted to write outside workspace: {path_str}. Blocked.")
            continue
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean leading/trailing newlines that occur from XML format
        if content.startswith("\n"):
            content = content[1:]
        if content.endswith("\n"):
            content = content[:-1]
            
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Runner: Updated/Created file: {path_str}")
        updated_files.append(path_str)
        
    # Find all <delete_file path="..."/> tags
    delete_pattern = re.compile(r'<delete_file path="([^"]+)"\s*/>')
    del_matches = delete_pattern.findall(response_text)
    for path_str in del_matches:
        target_path = (WORKSPACE / path_str).resolve()
        if not str(target_path).startswith(str(WORKSPACE)):
            print(f"Warning: Model attempted to delete outside workspace: {path_str}. Blocked.")
            continue
        if target_path.exists():
            target_path.unlink()
            print(f"Runner: Deleted file: {path_str}")
            updated_files.append(path_str)
            
    return updated_files

def call_lm_studio(config, context_prompt):
    api_url = f"{config['api_base']}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": context_prompt
            }
        ],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"]
    }
    
    req = urllib.request.Request(api_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            duration = time.time() - start_time
            
            choices = res_json.get("choices", [])
            if not choices:
                print(f"API Debug: Response JSON: {res_json}")
                return None, 0, 0, duration
                
            response_text = choices[0].get("message", {}).get("content", "")
            if not response_text:
                print(f"API Debug: Choices returned, but content is empty. Full message: {choices[0].get('message')}")
            
            usage = res_json.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return response_text, prompt_tokens, completion_tokens, duration
    except urllib.error.URLError as e:
        print(f"API Error: Failed to connect to LM Studio: {e}")
        return None, 0, 0, time.time() - start_time
    except Exception as e:
        print(f"API Error: Unexpected exception: {e}")
        return None, 0, 0, time.time() - start_time

def main():
    # Make sure dev directories exist
    DEV_DIR.mkdir(parents=True, exist_ok=True)
    (DEV_DIR / "library").mkdir(parents=True, exist_ok=True)
    (DEV_DIR / "templates").mkdir(parents=True, exist_ok=True)
    (DEV_DIR / "tools").mkdir(parents=True, exist_ok=True)
    
    config = load_config()
    max_iters = config.get("max_iterations", 50)
    
    print(f"Starting Ralph Loop. Model: {config['model']}. Max iterations: {max_iters}.")
    print(f"LM Studio API Base: {config['api_base']}")
    
    iteration = 0
    while iteration < max_iters:
        iteration += 1
        print(f"\n--- TURN {iteration} / {max_iters} ---")
        
        # 1. Compile context
        context_prompt = compile_context(config)
        
        # 2. Call API
        print(f"Runner: Querying model {config['model']}...")
        response_text, p_tok, c_tok, duration = call_lm_studio(config, context_prompt)
        
        if not response_text:
            print("Runner: Received empty or error response. Sleeping and retrying...")
            time.sleep(config.get("sleep_seconds_between_turns", 5))
            continue
            
        print(f"Runner: Received response. Duration: {duration:.2f}s. Tokens: {p_tok} prompt, {c_tok} completion.")
        
        # 3. Apply changes (parses file blocks)
        files_changed = parse_and_apply_changes(response_text)
        
        # 4. Check if stop token was emitted
        complete = "<promise>COMPLETE</promise>" in response_text or "<promise>COMPLETED</promise>" in response_text
        
        # 5. Run Validation
        if files_changed:
            valid, err_msg = run_validation()
            if valid:
                # Validation passed. Commit.
                if config.get("git_commit_on_success", True):
                    commit_msg = f"ralph-loop turn {iteration}: completed task"
                    # Try to parse custom task details from response if possible
                    run_git_commit(commit_msg)
                
                # Delete error log if it was resolved
                if ERROR_LOG_PATH.exists():
                    ERROR_LOG_PATH.unlink()
                
                config["stats"]["successful_turns"] += 1
            else:
                # Validation failed. Write error log and rollback.
                with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
                    f.write(err_msg)
                
                run_git_rollback()
                config["stats"]["failed_turns"] += 1
        else:
            print("Runner: No files changed this turn.")
            
        # Update Stats in config
        config["stats"]["total_turns"] = iteration
        config["stats"]["total_tokens_consumed"] += p_tok
        config["stats"]["total_tokens_generated"] += c_tok
        save_config(config)
        
        if complete:
            print("Runner: Stop signal <promise>COMPLETE</promise> detected. Terminating loop.")
            break
            
        sleep_time = config.get("sleep_seconds_between_turns", 2)
        print(f"Runner: End of turn {iteration}. Sleeping for {sleep_time}s...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
