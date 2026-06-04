import requests
import json

print("Firing bloated Gemini payload to ContextShield proxy...")

# Simulating a massive chunk of context bloat from an IDE
bloated_code = '''```python
def calculate_metrics():
    """
    This is a massive legacy docstring that wastes hundreds of tokens.
    It explains the architectural history of the function and provides
    extensive changelogs that the LLM does not actually need to read
    in order to complete the code generation task.
    
    Author: John Doe
    Date: 2023-01-01
    Ticket: PROJ-1234
    
    ContextShield's native AST parser should cleanly eradicate this
    entire string literal before forwarding the payload to Google.
    """
    data = [1, 2, 3, 4, 5]
    # An unnecessary inline comment
    total = sum(data)
    return total
```'''

# Standard Gemini API format
gemini_payload = {
    "contents": [{
        "parts": [{
            "text": f"Please refactor this Python function:\n\n{bloated_code}"
        }]
    }]
}

# Hitting the local ContextShield proxy interceptor
proxy_url = "http://localhost:8000/v1beta/models/gemini-1.5-pro:generateContent"

try:
    response = requests.post(proxy_url, json=gemini_payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    try:
        print("Response received from proxy (forwarded from Google/Fallback):")
        print(json.dumps(response.json(), indent=2)[:500] + "\n... (truncated)")
    except Exception:
        print(response.text)
        
    print("\nCheck your React Dashboard! You should see the savings spike.")
except Exception as e:
    print(f"Failed to connect to ContextShield: {e}")
