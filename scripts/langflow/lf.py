import json, urllib.parse, urllib.request
BASE = "https://langflow.rauvbr.com"
UA = {"User-Agent": "langflow-setup"}
def creds():
    lines = open(r"C:\Users\Vitor\langflow-credentials.txt", encoding="utf-8").read().splitlines()
    return lines[1].split(":", 1)[1].strip(), lines[2].split(":", 1)[1].strip()
def token():
    u, p = creds()
    body = urllib.parse.urlencode({"username": u, "password": p}).encode()
    req = urllib.request.Request(BASE + "/api/v1/login", data=body, headers={**UA, "Content-Type": "application/x-www-form-urlencoded"})
    return json.load(urllib.request.urlopen(req, timeout=30))["access_token"]
def call(method, path, tok, payload=None, timeout=180):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={**UA, "Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)
