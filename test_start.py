import urllib.request
import json
url = "http://localhost:8000/api/live-interview/start"
payload = {
    "candidate_name": "Test",
    "exam": "Test",
    "subject": "Test",
    "language": "English",
    "difficulty": "Medium",
    "interview_mode": "Voice",
    "duration": 20
}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as res:
        print(res.status)
        print(res.read().decode('utf-8'))
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
