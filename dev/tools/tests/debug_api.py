#!/usr/bin/env python3
import urllib.request
import json
import sys

def test_api():
    api_url = "http://192.168.1.29:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "model": "qwen/qwen3.6-35b-a3b",
        "messages": [
            {
                "role": "user",
                "content": "Hello, are you online? Respond with a single word."
            }
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }
    
    req = urllib.request.Request(
        api_url, 
        data=json.dumps(payload).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    try:
        print("Sending debug request to LM Studio...")
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            print("HTTP Status Code:", response.status)
            
            data = json.loads(res_body)
            choices = data.get("choices", [])
            print("Choices length:", len(choices))
            if choices:
                msg = choices[0].get("message", {})
                print("Message keys:", list(msg.keys()))
                content = msg.get("content", "")
                print("Content length:", len(content))
                # Safe print with ascii encoding to prevent console crashes
                print("Content (safe ASCII):", content.encode("ascii", "backslashreplace").decode("ascii"))
    except Exception as e:
        print("Request failed with error:", e)

if __name__ == "__main__":
    test_api()
