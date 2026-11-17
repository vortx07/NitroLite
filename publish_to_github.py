import os
import sys
import json
import urllib.request
import urllib.error
import subprocess

PROJECT_DIR = r"C:\Users\arifs\.gemini\antigravity\scratch\NitroLite"
GIT_EXE = r"C:\Users\arifs\AppData\Local\GitHubDesktop\app-3.6.11\resources\app\git\cmd\git.exe"

os.chdir(PROJECT_DIR)

def get_token():
    proc = subprocess.Popen([GIT_EXE, "credential", "fill"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, _ = proc.communicate(input="protocol=https\nhost=github.com\n\n")
    for line in stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise Exception("Could not find GitHub OAuth token in Credential Manager")

token = get_token()
print("[*] Successfully loaded GitHub OAuth token.")

# 1. Create Repository via GitHub API
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "NitroLite-Publisher"
}

repo_payload = {
    "name": "NitroLite",
    "description": "🚀 Ultra-lightweight native hardware monitor & fan controller for Acer Nitro and Predator laptops (~28MB RAM vs ~600MB NitroSense).",
    "homepage": "https://github.com/vortx07/NitroLite",
    "private": False,
    "has_issues": True,
    "has_projects": True,
    "has_wiki": True
}

print("[*] Creating GitHub repository vortx07/NitroLite...")
try:
    req = urllib.request.Request(
        "https://api.github.com/user/repos",
        data=json.dumps(repo_payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print(f"[+] Repository created: {res.get('html_url')}")
except urllib.error.HTTPError as e:
    err_body = e.read().decode()
    if "name already exists" in err_body:
        print("[!] Repository already exists on GitHub, proceeding.")
    else:
        print("[-] Error creating repository:", err_body)
        sys.exit(1)

# 2. Set Topics
print("[*] Setting repository topics...")
topics_payload = {
    "names": ["acer", "acer-nitro", "nitrosense", "fan-control", "hardware-monitor", "windows-11", "lightweight", "python"]
}
try:
    req = urllib.request.Request(
        "https://api.github.com/repos/vortx07/NitroLite/topics",
        data=json.dumps(topics_payload).encode("utf-8"),
        headers={**headers, "Accept": "application/vnd.github.mercy-preview+json"},
        method="PUT"
    )
    with urllib.request.urlopen(req) as resp:
        print("[+] Topics updated successfully.")
except Exception as e:
    print("[!] Could not set topics:", e)

# 3. Initialize Git locally and push
def run_git(*args):
    cmd = [GIT_EXE] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 and "nothing to commit" not in p.stdout + p.stderr:
        print(f"Git {' '.join(args)} warning/output:", p.stderr.strip() or p.stdout.strip())
    return p

print("[*] Initializing local Git repository...")
run_git("init", "-b", "main")
run_git("config", "user.name", "vortx07")
run_git("config", "user.email", "arifsidhik31@gmail.com")

print("[*] Staging files...")
run_git("add", ".")

print("[*] Creating commit...")
run_git("commit", "-m", "Initial release: NitroLite v1.0.0 - Lightweight Acer Nitro Hardware Dashboard")

print("[*] Configuring remote origin...")
# Setup authenticated remote URL with token for clean headless push
remote_url = f"https://vortx07:{token}@github.com/vortx07/NitroLite.git"
run_git("remote", "remove", "origin")
run_git("remote", "add", "origin", remote_url)

print("[*] Pushing code to GitHub main branch...")
push_res = run_git("push", "-u", "origin", "main", "--force")
if push_res.returncode == 0 or "Everything up-to-date" in push_res.stderr or "branch 'main' set up to track" in push_res.stderr:
    print("[+] Successfully pushed code to GitHub!")
else:
    print("[-] Git push output:", push_res.stderr)

# Reset remote URL to normal clean HTTPS URL (without embedded token)
run_git("remote", "set-url", "origin", "https://github.com/vortx07/NitroLite.git")

# 4. Create GitHub Release v1.0.0 & Upload NitroLite.exe
exe_path = os.path.join(PROJECT_DIR, "NitroLite.exe")
if os.path.exists(exe_path):
    print(f"[*] Found NitroLite.exe ({os.path.getsize(exe_path) / (1024*1024):.1f} MB). Creating GitHub Release v1.0.0...")
    release_payload = {
        "tag_name": "v1.0.0",
        "target_commitish": "main",
        "name": "NitroLite v1.0.0",
        "body": "### 🚀 NitroLite v1.0.0 - Initial Public Release\n\nUltra-lightweight Acer Nitro & Predator hardware dashboard and fan control utility.\n\n#### Highlights:\n- **~28 MB RAM** vs 600 MB official NitroSense (over 95% reduction)\n- Real-time CPU & GPU temperature, fan RPM, and clock monitoring\n- 1-click Performance Profiles (Eco, Quiet, Balanced, Gaming)\n- Auto, Max (100%), and Custom Fan Speed Sliders\n- Quick Toggles: Windows Key Lock, LCD Overdrive, Backlight Timeout\n- System Tray minimization with quick menu\n\n#### Assets:\nDownload `NitroLite.exe` below to run immediately without needing Python installed.",
        "draft": False,
        "prerelease": False
    }

    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/vortx07/NitroLite/releases",
            data=json.dumps(release_payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            rel_data = json.loads(resp.read().decode())
            upload_url = rel_data.get("upload_url", "").split("{")[0]
            release_html = rel_data.get("html_url")
            print(f"[+] Release created: {release_html}")

            # Upload binary
            print("[*] Uploading NitroLite.exe to Release assets...")
            with open(exe_path, "rb") as f:
                exe_bytes = f.read()

            upload_req = urllib.request.Request(
                f"{upload_url}?name=NitroLite.exe",
                data=exe_bytes,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/octet-stream",
                    "User-Agent": "NitroLite-Publisher"
                },
                method="POST"
            )
            with urllib.request.urlopen(upload_req) as upload_resp:
                print("[+] Successfully uploaded NitroLite.exe to GitHub Release!")
    except Exception as e:
        print("[!] Note on release creation:", e)

print("\n🎉 ALL DONE! Your repository is live at: https://github.com/vortx07/NitroLite")
