"""
Outils de génération, import/export et validation des métadonnées corpus
@jcharlesDS (2026)
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

BASE_METADATA_COLUMNS = ["id", "genre", "word_count", "sentence_count"]
HEADER_ALIASES = {
    "num_words": "word_count",
    "num_sent": "sentence_count",
    "num_sents": "sentence_count",
    "sentences_count": "sentence_count",
}


def normalize_metadata_header(header: str) -> str:
    """Normalise les alias historiques de colonnes metadata."""
    return HEADER_ALIASES.get(header, header)


def normalize_metadata_row(row: dict[str, object]) -> dict[str, object]:
    """Normalise les clés d'une ligne metadata et fusionne les alias connus."""
    normalized: dict[str, object] = {}
    for key, value in row.items():
        canonical = normalize_metadata_header(key)
        if canonical in normalized and normalized[canonical] not in ("", None):
            continue
        normalized[canonical] = value
    return normalized

def count_words(text: str) -> int:
    tokens = re.findall(r"\b[\wÀ-ÿ]+(?:['-][\wÀ-ÿ]+)?\b", text, flags=re.UNICODE)
    return len(tokens)

def count_sentences(text: str) -> int:
    matches = re.findall(r"[.!?]+(?:[\"'»”)\]]*)", text)
    return max(len(matches), 1 if text.strip() else 0)

def scan_corpus_dir(corpus_dir: str | Path) -> list[dict[str, object]]:
    corpus_path = Path(corpus_dir)
    rows: list[dict[str, object]] = []
    
    if not corpus_path.exists():
        return rows
    
    for txt_file in sorted(corpus_path.glob("*.txt")):
        content = txt_file.read_text(encoding="utf-8", errors="ignore")
        rows.append(
            {
                "id": txt_file.stem,
                "genre": "",
                "word_count": count_words(content),
                "sentence_count": count_sentences(content),
            }
        )
    return rows

def load_metadata_tsv(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    file_path = Path(path)
    if not file_path.exists():
        return [], []
    
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        raw_headers = list(reader.fieldnames or [])
        headers: list[str] = []
        for header in raw_headers:
            canonical = normalize_metadata_header(header)
            if canonical not in headers:
                headers.append(canonical)

        rows = []
        for row in reader:
            normalized = normalize_metadata_row({key: value or "" for key, value in row.items()})
            rows.append({key: normalized.get(key, "") for key in headers})
    return headers, rows

def write_metadata_tsv(path: str | Path, headers: list[str], rows: list[dict[str, object]]):
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})

def merge_corpus_and_metadata(
    corpus_rows: list[dict[str, object]],
    imported_headers: list[str],
    imported_rows: list[dict[str, str]],
) -> tuple[list[str], list[dict[str, object]]]:
    normalized_headers: list[str] = []
    for header in imported_headers:
        canonical = normalize_metadata_header(header)
        if canonical not in normalized_headers:
            normalized_headers.append(canonical)
    custom_headers = [h for h in normalized_headers if h not in BASE_METADATA_COLUMNS]
    headers = BASE_METADATA_COLUMNS +  [h for h in custom_headers if h not in BASE_METADATA_COLUMNS]
    
    imported_map: dict[str, dict[str, str]] = {}
    for row in imported_rows:
        row = normalize_metadata_row(row)
        row_id = (row.get("id") or "").strip()
        if row_id:
            imported_map[row_id] = row
    
    merged: list[dict[str, object]] = []
    corpus_ids: set[str] = set()
    
    for base_row in corpus_rows:
        row_id = str(base_row["id"])
        corpus_ids.add(row_id)
        imported = imported_map.get(row_id, {})
        
        merged_row: dict[str, object] = {header: "" for header in headers}
        merged_row.update(base_row)
        merged_row["genre"] = imported.get("genre", merged_row.get("genre", ""))
        if imported.get("word_count", "") not in ("", None):
            merged_row["word_count"] = imported.get("word_count", "")
        if imported.get("sentence_count", "") not in ("", None):
            merged_row["sentence_count"] = imported.get("sentence_count", "")
        
        for header in custom_headers:
            merged_row[header] = imported.get(header, "")
        
        merged.append(merged_row)
        
    for row_id, imported in imported_map.items():
        if row_id in corpus_ids:
            continue
        
        extra_row: dict[str, object] = {header: "" for header in headers}
        extra_row["id"] = row_id
        extra_row["genre"] = imported.get("genre", "")
        extra_row["word_count"] = ""
        extra_row["sentence_count"] = imported.get("sentence_count", "")
        
        for header in custom_headers:
            extra_row[header] = imported.get(header, "")
        
        merged.append(extra_row)
    
    return headers, merged

def validate_metadata(corpus_dir: str | Path, headers: list[str], rows: list[dict[str, object]]) -> dict[str, object]:
    corpus_ids = {str(row["id"]) for row in scan_corpus_dir(corpus_dir)}
    
    metadata_ids: list[str] = []
    duplicates: set[str] = set()
    
    for row in rows:
        row_id = str(row.get("id", "")).strip()
        if not row_id:
            continue
        
        if row_id in metadata_ids:
            duplicates.add(row_id)
        metadata_ids.append(row_id)
    
    metadata_ids_set = set(metadata_ids)
    
    missing_required = [col for col in BASE_METADATA_COLUMNS if col not in headers]
    missing_in_metadata = sorted(corpus_ids - metadata_ids_set)
    missing_in_corpus = sorted(metadata_ids_set - corpus_ids)
    
    return {
        "missing_required_columns": missing_required,
        "missing_in_metadata": missing_in_metadata,
        "missing_in_corpus": missing_in_corpus,
        "duplicates": sorted(duplicates),
        "corpus_count": len(corpus_ids),
        "metadata_count": len(metadata_ids),
    }
