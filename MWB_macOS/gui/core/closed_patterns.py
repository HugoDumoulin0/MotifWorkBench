"""
Chargement des motifs clos de la dernière analyse pour le concordancier.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import formate_patterns
import tools


def _load_last_analysis(project_root: Path) -> dict:
    last_analysis = project_root / "logs" / "last_analysis.json"
    if not last_analysis.exists():
        return {}
    try:
        return json.loads(last_analysis.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_pattern_source(
    analysis_root: Path,
    info: dict,
) -> tuple[list, str]:
    config = info.get("config", {}) if isinstance(info, dict) else {}
    use_internal_clustering = bool(config.get("internal_clustering", False))

    if use_internal_clustering:
        medoids_dir = analysis_root / "Clustering_results" / "Medoids"
        if medoids_dir.exists():
            medoid_files = sorted(medoids_dir.glob("*_medoids_3.pk"), key=lambda p: p.stat().st_mtime, reverse=True)
            for medoid_file in medoid_files:
                try:
                    medoids = formate_patterns.load_pk(str(medoid_file))
                    motifs = [value[0] for value in medoids.values() if value and len(value) > 0]
                    if motifs:
                        return motifs, medoid_file.name
                except Exception:
                    continue

    closed_dir = analysis_root / "Patterns_results" / "Closed"
    if not closed_dir.exists():
        return [], ""

    closed_files = sorted(closed_dir.glob("*_closed.pk"), key=lambda p: p.stat().st_mtime, reverse=True)
    for closed_file in closed_files:
        try:
            motifs = tools.from_pk_corpus_to_list(str(closed_file))
            if motifs:
                return motifs, closed_file.name
        except Exception:
            continue

    return [], ""


def load_closed_patterns_from_last_analysis(project_root: Path) -> list[dict[str, str]]:
    """Charge les motifs clos de la dernière analyse et prépare leur requête CQP."""
    info = _load_last_analysis(project_root)
    # Compatibilite de lecture des anciennes analyses.
    analysis_group_name = info.get("analysis_group_name", info.get("corpus_name", ""))
    config_id = info.get("config_id", "")
    if not (analysis_group_name and config_id):
        return []

    analysis_root = project_root / "Data" / "analyses" / analysis_group_name / config_id
    lexic_int_str_path = analysis_root / "Lexiques" / "dico_int_to_str_all_items.pk"
    lexic_str_int_path = analysis_root / "Lexiques" / "dico_str_to_int_all_items.pk"

    try:
        if lexic_int_str_path.exists():
            lexic_int_str = formate_patterns.load_lexique(str(lexic_int_str_path))
        elif lexic_str_int_path.exists():
            lexic_int_str = formate_patterns.make_dict_int_to_str(
                str(lexic_str_int_path),
                str(lexic_int_str_path),
            )
        else:
            return []

        motifs, source_name = _load_pattern_source(analysis_root, info)
        if not motifs:
            return []
    except Exception:
        return []

    entries: list[dict[str, str]] = []
    for index, motif in enumerate(motifs, start=1):
        try:
            motif_str = formate_patterns.from_int_to_str(motif, lexic_int_str)
            cqp_pattern = str(tools.read_req_CQP(motif_str))
            entries.append(
                {
                    "id": str(index),
                    "display": motif_str,
                    "cqp_pattern": cqp_pattern,
                    "source_file": source_name,
                }
            )
        except Exception:
            continue

    return entries
