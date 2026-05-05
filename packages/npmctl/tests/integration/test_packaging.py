from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "packages" / "npmctl"


def test_package_metadata_urls_point_to_groupsum_npmctl() -> None:
    metadata = tomllib.loads((PACKAGE / "pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["urls"] == {
        "Homepage": "https://github.com/groupsum/npmctl",
        "Documentation": "https://github.com/groupsum/npmctl/tree/master/docs",
        "Issues": "https://github.com/groupsum/npmctl/issues",
        "Repository": "https://github.com/groupsum/npmctl",
    }


def test_installed_console_script_smoke_in_clean_environment(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    dist = tmp_path / "dist"
    subprocess.run([uv, "build", "--package", "npmctl", "--out-dir", str(dist)], cwd=ROOT, check=True)
    wheel = next(dist.glob("npmctl-*.whl"))
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", str(venv)], check=True)
    if os.name == "nt":
        python = venv / "Scripts" / "python.exe"
        script = venv / "Scripts" / "npmctl.exe"
    else:
        python = venv / "bin" / "python"
        script = venv / "bin" / "npmctl"

    subprocess.run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(python),
            str(wheel),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    result = subprocess.run(
        [str(script), "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    assert result.stdout.strip().startswith("npmctl ")
