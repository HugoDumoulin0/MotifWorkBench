"""
Module de résolution du chemin vers Rscript.exe sur Windows.
@author: @jcharlesDS
"""



import os
import shutil
from pathlib import Path


def resolve_rscript() -> str:
    candidate = shutil.which("Rscript") or shutil.which("Rscript.exe")
    if candidate:
        return candidate

    roots = [
        Path("C:/Program Files/R"),
        Path("C:/Program Files (x86)/R"),
    ]
    local_base = os.environ.get("LOCALAPPDATA")
    user_profile = os.environ.get("USERPROFILE")
    if local_base:
        roots.append(Path(local_base) / "Programs" / "R")
    if user_profile:
        roots.append(Path(user_profile) / "AppData" / "Local" / "Programs" / "R")

    found: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        found.extend(root.glob("**/Rscript.exe"))

    if found:
        found.sort(reverse=True)
        return str(found[0])

    raise FileNotFoundError(
        "Rscript introuvable. Ajoutez R au PATH ou installez-le dans un dossier standard Windows."
    )
