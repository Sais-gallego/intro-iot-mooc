import os
import subprocess
import tempfile
import urllib.request
import json
import time

# 1. Fetch git token
tpath = os.path.join(tempfile.gettempdir(), "gitcred.txt")
with open(tpath, "w") as f:
    f.write("protocol=https\nhost=github.com\n\n")

proc = subprocess.run("git credential fill", input=open(tpath, "rb").read(), stdout=subprocess.PIPE, shell=True)
if os.path.exists(tpath):
    os.remove(tpath)

token = None
for line in proc.stdout.decode("utf-8").splitlines():
    if line.startswith("password="):
        token = line[9:]
        break

if not token:
    print("Error: Could not retrieve GitHub PAT")
    exit(1)

print("Found GitHub PAT")

# 2. Check / Create GitHub repo: intro-iot-mooc
repo_name = "intro-iot-mooc"
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Antigravity-Agent"
}

req_check = urllib.request.Request(f"https://api.github.com/repos/Sais-gallego/{repo_name}", headers=headers)
repo_exists = False
try:
    with urllib.request.urlopen(req_check) as resp:
        if resp.status == 200:
            repo_exists = True
            print("Repository already exists on GitHub")
except urllib.error.HTTPError as e:
    if e.code == 404:
        repo_exists = False
    else:
        print(f"Error checking repo: {e}")

if not repo_exists:
    create_payload = json.dumps({
        "name": repo_name,
        "description": "Introduction to the Internet of Things MOOC - University of Helsinki (RTOS, CoAP, MQTT, LoRaWAN, TinyML)",
        "private": False,
        "auto_init": False
    }).encode("utf-8")
    req_create = urllib.request.Request("https://api.github.com/user/repos", data=create_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req_create) as resp:
        print("Created repository on GitHub:", resp.status)

# 3. Configure Git local
subprocess.run("git init", shell=True, check=True)
subprocess.run('git config user.name "Sergio Andrés Ipuz Saavedra"', shell=True, check=True)
subprocess.run('git config user.email "afranklinromero@gmail.com"', shell=True, check=True)
subprocess.run("git branch -M main", shell=True, check=True)
subprocess.run("git add .", shell=True, check=True)
subprocess.run('git commit -m "Complete Introduction to IoT MOOC modules, tests and solutions"', shell=True)

remote_url = f"https://{token}@github.com/Sais-gallego/{repo_name}.git"
subprocess.run("git remote remove origin", shell=True)
subprocess.run(f"git remote add origin {remote_url}", shell=True, check=True)
subprocess.run("git push -u origin main --force", shell=True, check=True)
subprocess.run(f"git remote set-url origin https://github.com/Sais-gallego/{repo_name}.git", shell=True, check=True)

print("Pushed to GitHub main successfully!")

# 4. Star repository
req_star = urllib.request.Request(f"https://api.github.com/user/starred/Sais-gallego/{repo_name}", headers=headers, method="PUT")
try:
    with urllib.request.urlopen(req_star) as resp:
        print("Starred repository:", resp.status)
except Exception as e:
    print("Star error:", e)

# 5. Set topics
topics_payload = json.dumps({
    "names": ["iot", "internet-of-things", "coap", "mqtt", "lorawan", "rtos", "university-of-helsinki", "mooc-fi"]
}).encode("utf-8")
req_topics = urllib.request.Request(
    f"https://api.github.com/repos/Sais-gallego/{repo_name}/topics",
    data=topics_payload,
    headers={**headers, "Accept": "application/vnd.github.mercy-preview+json"},
    method="PUT"
)
try:
    with urllib.request.urlopen(req_topics) as resp:
        print("Set topics:", resp.status)
except Exception as e:
    print("Topics error:", e)
