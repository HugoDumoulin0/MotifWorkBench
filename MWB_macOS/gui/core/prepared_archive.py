"""
Outils de creation d'archives preparees pour reutiliser Textes_tagged et underscore_fix.
"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def resolve_prepared_archive_sources(analysis_root: str | Path) -> dict[str, Path]:
    root = Path(analysis_root)
    tagged = root / "Textes_tagged"
    legacy_tagged = root / "Textes_tagged_stanza"
    underscore = root / "underscore_fix"

    resolved_tagged = tagged if tagged.exists() else legacy_tagged
    return {
        "root": root,
        "tagged": resolved_tagged,
        "underscore_fix": underscore,
    }


def has_prepared_archive_content(analysis_root: str | Path) -> bool:
    sources = resolve_prepared_archive_sources(analysis_root)
    return sources["tagged"].exists() or sources["underscore_fix"].exists()


def default_archive_path(analysis_root: str | Path, selected_corpus: str) -> Path:
    root = Path(analysis_root)
    corpus_slug = selected_corpus.strip() or root.name
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in corpus_slug)
    return root / f"{safe}_prepared.zip"


def create_prepared_archive(analysis_root: str | Path, output_zip: str | Path) -> dict[str, object]:
    sources = resolve_prepared_archive_sources(analysis_root)
    tagged_dir = sources["tagged"]
    underscore_dir = sources["underscore_fix"]
    output_path = Path(output_zip)

    if not tagged_dir.exists() and not underscore_dir.exists():
        raise FileNotFoundError("Aucun dossier Textes_tagged ou underscore_fix disponible pour creer l'archive.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_count = 0
    included_roots: list[str] = []
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as zf:
        for source_dir, archive_root in ((tagged_dir, "Textes_tagged"), (underscore_dir, "underscore_fix")):
            if not source_dir.exists():
                continue
            included_roots.append(archive_root)
            for file_path in sorted(source_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                relative = file_path.relative_to(source_dir)
                zf.write(file_path, Path(archive_root) / relative)
                file_count += 1

    return {
        "output_path": output_path,
        "file_count": file_count,
        "included_roots": included_roots,
    }
