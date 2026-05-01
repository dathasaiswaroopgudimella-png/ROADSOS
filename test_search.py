import urllib.request
import json

def test_search():
    url = "http://localhost:8000/api/search"
    data = json.dumps({"query": "Apollo"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as f:
            print(f"Status: {f.getcode()}")
            print(f"Response: {json.dumps(json.loads(f.read().decode('utf-8')), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
