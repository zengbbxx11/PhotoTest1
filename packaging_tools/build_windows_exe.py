from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def build():
    project_root = Path(__file__).resolve().parents[1]
    entry_script = project_root / "run_gui.pyw"
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    custom_provider_source = project_root / "custom_providers"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "PhotoQualityWorkbench",
        "--collect-all",
        "customtkinter",
        "--collect-all",
        "matplotlib",
        "--hidden-import",
        "PIL._tkinter_finder",
        str(entry_script),
    ]

    print("Running:", " ".join(command))
    subprocess.run(command, cwd=project_root, check=True)

    output_root = dist_dir / "PhotoQualityWorkbench"
    output_custom_providers = output_root / "custom_providers"
    output_custom_providers.mkdir(parents=True, exist_ok=True)
    readme_source = custom_provider_source / "README.md"
    if readme_source.exists():
        shutil.copy2(readme_source, output_custom_providers / "README.md")

    print("\nBuild finished.")
    print(f"EXE directory: {output_root}")


if __name__ == "__main__":
    build()
