import urllib.request
import json
import sys

def verify():
    print("Verifying local server endpoints...")
    
    # 1. Test homepage
    try:
        response = urllib.request.urlopen("http://127.0.0.1:5000/")
        code = response.getcode()
        html = response.read().decode('utf-8')
        if code == 200 and "<title>Aura Assistant - FAQ & Support Chatbot</title>" in html:
            print("PASS: Homepage loaded successfully.")
        else:
            print(f"FAIL: Homepage loaded with code {code} or missing title.")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL: Homepage request failed: {e}")
        sys.exit(1)

    # 2. Test /api/faqs
    try:
        response = urllib.request.urlopen("http://127.0.0.1:5000/api/faqs")
        code = response.getcode()
        data = json.loads(response.read().decode('utf-8'))
        if code == 200 and "Setup & Getting Started" in data:
            print("PASS: /api/faqs endpoint loaded categories successfully.")
        else:
            print(f"FAIL: /api/faqs returned code {code} or missing categories.")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL: /api/faqs request failed: {e}")
        sys.exit(1)

    # 3. Test /api/chat
    try:
        url = "http://127.0.0.1:5000/api/chat"
        req_data = json.dumps({"message": "setup guide"}).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=req_data, 
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req)
        code = response.getcode()
        data = json.loads(response.read().decode('utf-8'))
        if code == 200 and data.get("match") is True and "Setup" in data.get("category"):
            print(f"PASS: /api/chat matching works: matched '{data.get('question')}' with score {data.get('score'):.2f}.")
        else:
            print(f"FAIL: /api/chat returned code {code} or unexpected payload: {data}")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL: /api/chat request failed: {e}")
        sys.exit(1)
        
    print("\nAll server endpoints verified successfully!")

if __name__ == '__main__':
    verify()
