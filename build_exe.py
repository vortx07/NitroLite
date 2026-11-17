import os
import subprocess
import sys

project_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_dir)

print(f"[*] Building NitroLite.exe in: {project_dir}")

cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconsole",
    "--onefile",
    "--clean",
    "--name=NitroLite",
    "--icon=assets/icon.ico",
    "--add-data=assets;assets",
    "--collect-all=customtkinter",
    "--collect-all=pystray",
    "--collect-all=darkdetect",
    "main.py",
]

print("[*] Executing:", " ".join(cmd))
result = subprocess.run(cmd)
if result.returncode == 0:
    dist_exe = os.path.join(project_dir, "dist", "NitroLite.exe")
    target_exe = os.path.join(project_dir, "NitroLite.exe")
    if os.path.exists(dist_exe):
        import shutil
        shutil.copy2(dist_exe, target_exe)
        print(f"\n[+] Build successful! Executable ready at:\n    {target_exe}")
    sys.exit(0)
else:
    print("\n[-] Build failed with exit code:", result.returncode)
    sys.exit(result.returncode)
