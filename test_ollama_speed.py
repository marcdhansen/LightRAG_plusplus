import time

import requests

prompt = "A" * 10000
data = {"model": "qwen2.5-coder:1.5b", "prompt": prompt, "stream": False}

start = time.time()
print("Sending request with 10K prompt...")
response = requests.post("http://localhost:11434/api/generate", json=data)
end = time.time()

if response.status_code == 200:
    print(f"Success! Time taken: {end - start:.2f}s")
    print(f"Response: {response.json().get('response', '')[:100]}...")
else:
    print(f"Error {response.status_code}: {response.text}")
