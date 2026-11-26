#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export the saved (closed) motifs of one analysis, with their CQP query, as JSON.
Used by the Shiny concordancer (CQP_concordancer.r), which cannot read pickles.

Usage: python export_closed_patterns.py <analysis_root> <output.json>

Same logic as gui/core/closed_patterns.py, but for an explicit analysis root
(not logs/last_analysis.json), and reading the config from analysis_info.json.
"""

import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
for p in (str(SRC_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import formate_patterns  # noqa: E402
import tools  # noqa: E402

try:
    from gui.core.analysis_paths import resolve_analysis_artifact  # noqa: E402
except Exception:  # keep working outside the GUI environment
    def resolve_analysis_artifact(analysis_root, stage, key, fallback):
        return fallback


def load_pattern_source(analysis_root: Path, config: dict):
    """Medoids if internal clustering was used, otherwise the closed patterns."""
    if config.get("internal_clustering", False):
        medoids_dir = analysis_root / "Clustering_results" / "Medoids"
        if medoids_dir.exists():
            for medoid_file in sorted(medoids_dir.glob("*_medoids_3.pk"),
                                      key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    medoids = formate_patterns.load_pk(str(medoid_file))
                    motifs = [v[0] for v in medoids.values() if v and len(v) > 0]
                    if motifs:
                        return motifs, medoid_file.name
                except Exception:
                    continue

    closed_dir = analysis_root / "Patterns_results" / "Closed"
    if closed_dir.exists():
        for closed_file in sorted(closed_dir.glob("*_closed.pk"),
                                  key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                motifs = tools.from_pk_corpus_to_list(str(closed_file))
                if motifs:
                    return motifs, closed_file.name
            except Exception:
                continue
    return [], ""


def export(analysis_root: Path):
    info_path = analysis_root / "analysis_info.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
    config = info.get("config", {}) if isinstance(info, dict) else {}

    lexiques = resolve_analysis_artifact(analysis_root, "dmt4", "lexiques", analysis_root / "Lexiques")
    int_str = Path(lexiques) / "dico_int_to_str_all_items.pk"
    str_int = Path(lexiques) / "dico_str_to_int_all_items.pk"
    if int_str.exists():
        lexic = formate_patterns.load_lexique(str(int_str))
    elif str_int.exists():
        lexic = formate_patterns.make_dict_int_to_str(str(str_int), str(int_str))
    else:
        return {"source_file": "", "patterns": []}

    motifs, source_name = load_pattern_source(analysis_root, config)
    entries = []
    for index, motif in enumerate(motifs, start=1):
        try:
            motif_str = formate_patterns.from_int_to_str(motif, lexic)
            entries.append({
                "id": index,
                "display": motif_str,
                "cqp_pattern": str(tools.read_req_CQP(motif_str)),
            })
        except Exception:
            continue
    return {"source_file": source_name, "patterns": entries}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: export_closed_patterns.py <analysis_root> <output.json>")
    result = export(Path(sys.argv[1]).resolve())
    Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
