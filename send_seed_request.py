import json, requests, sys, os

API_URL = "https://eajeyq4r3zljoq4rpovy2nthda0vtjqf.lambda-url.ap-south-1.on.aws"
STUDENT_ID = "22P31A1205"
GIT_URL = "https://github.com/vaishu1205/-Secure-PKI-Based-2FA-Microservice-with-Docker"

if not os.path.exists("student_public.pem"):
    print("student_public.pem not found", file=sys.stderr); sys.exit(1)

with open("student_public.pem", "r", encoding="utf-8") as f:
    pem = f.read().strip()

# Replace real newlines with literal backslash-n sequences so JSON contains "\n"
pub_for_json = pem.replace("\n", "\\n")

payload = {
    "student_id": STUDENT_ID,
    "github_repo_url": GIT_URL,
    "public_key": pub_for_json
}

print("Payload preview (truncated public_key):")
print(json.dumps({"student_id": STUDENT_ID, "github_repo_url": GIT_URL, "public_key": pub_for_json[:200]}, indent=2))

headers = {"Content-Type": "application/json"}

try:
    r = requests.post(API_URL, json=payload, headers=headers, timeout=60)
except Exception as e:
    print("Request failed:", e, file=sys.stderr)
    sys.exit(1)

print("HTTP status:", r.status_code)
try:
    print("Response body:", r.text or "(empty)")
except Exception:
    print("Could not read response body")

if r.status_code == 200:
    try:
        j = r.json()
        if j.get("status") == "success" and "encrypted_seed" in j:
            with open("encrypted_seed.txt", "w", encoding="ascii") as out:
                out.write(j["encrypted_seed"])
            print("Success: encrypted_seed.txt written (DO NOT COMMIT).")
        else:
            print("JSON response:", json.dumps(j, indent=2))
    except Exception as e:
        print("Response was not JSON:", e)
