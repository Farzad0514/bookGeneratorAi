import requests

url = "http://127.0.0.1:11434/api/generate"
data = {
    "model": "llama3.1:8b",
    "prompt": "What is the capital of Germany.",
    "stream": False
}

response = requests.post(url, json=data)
print(response.json())
