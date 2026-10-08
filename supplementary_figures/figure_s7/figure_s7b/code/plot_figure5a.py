from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[3]
subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root/"总控代码/重建主图.ps1"), "-Figures", "5"], check=True)
