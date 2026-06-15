"""
Assistant simplifié de création et mise à jour du metadata.tsv.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.core.metadata_tools import (
    BASE_METADATA_COLUMNS,
    inspect_corpus_dir,
    load_metadata_tsv,
    merge_corpus_and_metadata,
    scan_corpus_dir,
    validate_metadata,
    write_metadata_tsv,
)


class MetadataWizardDialog(QDialog):
    def __init__(self, initial_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assistant metadata")
        self.setMinimumSize(980, 720)

        self._initial_config = dict(initial_config)
        self._current_step = 0
        self._headers: list[str] = list(BASE_METADATA_COLUMNS)
        self._rows: list[dict[str, object]] = []
        self._corpus_info: dict[str, object] = {}

        self._build_ui()
        self._load_initial_state()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f7f8fc;
                color: #1f2937;
            }
            QGroupBox {
                color: #111827;
                border: 1px solid #d4d7e3;
                border-radius: 8px;
                margin-top: 8px;
                padding: 10px;
                font-weight: bold;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QLineEdit {
                background: #ffffff;
                color: #111827;
                border: 1px solid #c7ccda;
                border-radius: 4px;
                padding: 6px 8px;
            }
            QPushButton {
                background-color: #3a3a5a;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #4a4a6a;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
                color: #f3f4f6;
            }
            QTableWidget {
                background: #ffffff;
                color: #111827;
                border: 1px solid #d4d7e3;
                border-radius: 6px;
                gridline-color: #e5e7eb;
            }
            QLabel[muted="true"] {
                color: #6b7280;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("Assistant metadata")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        root.addWidget(title)

        subtitle = QLabel(
            "Créer un metadata.tsv ou mettre à jour un metadata.tsv existant en trois étapes simples."
        )
        subtitle.setProperty("muted", True)
        root.addWidget(subtitle)

        self._step_label = QLabel()
        self._step_label.setStyleSheet("font-weight: 600; color: #374151;")
        root.addWidget(self._step_label)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        self._stack.addWidget(self._build_step_corpus())
        self._stack.addWidget(self._build_step_metadata())
        self._stack.addWidget(self._build_step_review())

        nav = QHBoxLayout()
        self._btn_cancel = QPushButton("Annuler")
        self._btn_cancel.clicked.connect(self.reject)
        nav.addWidget(self._btn_cancel)

        nav.addStretch()

        self._btn_prev = QPushButton("Précédent")
        self._btn_prev.clicked.connect(self._go_prev)
        nav.addWidget(self._btn_prev)

        self._btn_next = QPushButton("Suivant")
        self._btn_next.clicked.connect(self._go_next)
        nav.addWidget(self._btn_next)

        self._btn_save = QPushButton("Enregistrer")
        self._btn_save.clicked.connect(self._save_and_accept)
        nav.addWidget(self._btn_save)

        root.addLayout(nav)
        self._update_navigation()

    def _build_step_corpus(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        grp = QGroupBox("1. Corpus")
        form = QFormLayout(grp)

        corpus_row = QHBoxLayout()
        self._corpus_dir_edit = QLineEdit()
        self._corpus_dir_edit.setPlaceholderText("Choisir le dossier du corpus")
        self._corpus_dir_edit.textChanged.connect(self._on_corpus_path_changed)
        corpus_row.addWidget(self._corpus_dir_edit, 1)

        btn_browse = QPushButton("Parcourir")
        btn_browse.clicked.connect(self._browse_corpus_dir)
        corpus_row.addWidget(btn_browse)
        form.addRow("Dossier du corpus :", corpus_row)

        self._step1_summary = QLabel("Sélectionne un dossier de corpus pour commencer.")
        self._step1_summary.setWordWrap(True)
        self._step1_summary.setProperty("muted", True)
        form.addRow("", self._step1_summary)

        layout.addWidget(grp)
        layout.addStretch()
        return page

    def _build_step_metadata(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        grp = QGroupBox("2. Métadonnées")
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(10)

        info = QLabel(
            "Les colonnes `id`, `word_count` et `sentence_count` sont préremplies automatiquement. "
            "Les valeurs déjà présentes dans le metadata existant sont conservées quand elles existent."
        )
        info.setWordWrap(True)
        info.setProperty("muted", True)
        grp_layout.addWidget(info)

        actions = QHBoxLayout()
        self._btn_add_column = QPushButton("Ajouter une colonne")
        self._btn_add_column.clicked.connect(self._add_custom_column)
        actions.addWidget(self._btn_add_column)
        actions.addStretch()
        grp_layout.addLayout(actions)

        genre_fill = QHBoxLayout()
        self._genre_filter_edit = QLineEdit()
        self._genre_filter_edit.setPlaceholderText("Filtre d'ID (vide = tous)")
        genre_fill.addWidget(self._genre_filter_edit, 2)

        self._genre_value_edit = QLineEdit()
        self._genre_value_edit.setPlaceholderText("Valeur à appliquer à genre")
        genre_fill.addWidget(self._genre_value_edit, 1)

        self._btn_apply_genre = QPushButton("Appliquer")
        self._btn_apply_genre.clicked.connect(self._apply_genre_batch)
        genre_fill.addWidget(self._btn_apply_genre)
        grp_layout.addLayout(genre_fill)

        self._table = QTableWidget()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        grp_layout.addWidget(self._table, 1)

        self._step2_summary = QLabel("Aucune métadonnée chargée.")
        self._step2_summary.setProperty("muted", True)
        grp_layout.addWidget(self._step2_summary)

        layout.addWidget(grp, 1)
        return page

    def _build_step_review(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        grp = QGroupBox("3. Validation et enregistrement")
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(12)

        self._review_summary = QLabel("Aucun résumé disponible.")
        self._review_summary.setWordWrap(True)
        grp_layout.addWidget(self._review_summary)

        self._review_issues = QLabel("")
        self._review_issues.setWordWrap(True)
        grp_layout.addWidget(self._review_issues)

        layout.addWidget(grp)
        layout.addStretch()
        return page

    def _load_initial_state(self):
        path_corpus = self._initial_config.get("path_corpus", "")
        if not path_corpus:
            try:
                project_root = Path(__file__).resolve().parents[2]
                last_analysis_path = project_root / "logs" / "last_analysis.json"
                if last_analysis_path.exists():
                    import json

                    with open(last_analysis_path, encoding="utf-8") as handle:
                        config = json.load(handle)
                    path_metadata = config.get("path_metadata", "")
                    if path_metadata:
                        path_corpus = str(Path(path_metadata).parent)
            except Exception:
                pass

        if path_corpus:
            self._corpus_dir_edit.setText(path_corpus)
            self._load_corpus_data(path_corpus)

    def _browse_corpus_dir(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier du corpus",
            self._corpus_dir_edit.text().strip() or ".",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            self._corpus_dir_edit.setText(path)
            self._load_corpus_data(path)

    def _on_corpus_path_changed(self):
        corpus_dir = self._corpus_dir_edit.text().strip()
        self._corpus_info = inspect_corpus_dir(corpus_dir) if corpus_dir else {}
        self._refresh_step1_summary()

    def _load_corpus_data(self, corpus_dir: str):
        self._corpus_info = inspect_corpus_dir(corpus_dir)
        self._refresh_step1_summary()

        corpus_rows = scan_corpus_dir(corpus_dir)
        metadata_path = Path(corpus_dir) / "metadata.tsv"

        if metadata_path.exists():
            headers, imported_rows = load_metadata_tsv(metadata_path)
        else:
            headers, imported_rows = [], []

        self._headers, self._rows = merge_corpus_and_metadata(corpus_rows, headers, imported_rows)
        self._refresh_table()
        self._refresh_review()
        self._update_navigation()

    def _refresh_step1_summary(self):
        if not self._corpus_info:
            self._step1_summary.setText("Sélectionne un dossier de corpus pour commencer.")
            return

        if not self._corpus_info.get("exists"):
            self._step1_summary.setText("Le dossier indiqué n'existe pas.")
            return

        txt_count = self._corpus_info.get("txt_count", 0)
        metadata_exists = self._corpus_info.get("metadata_exists", False)
        metadata_status = "metadata.tsv présent" if metadata_exists else "metadata.tsv absent"
        self._step1_summary.setText(
            f"Dossier prêt.\n{txt_count} fichier(s) .txt détecté(s).\n{metadata_status}."
        )

    def _refresh_table(self):
        self._table.clear()
        self._table.setColumnCount(len(self._headers))
        self._table.setHorizontalHeaderLabels(self._headers)
        self._table.setRowCount(len(self._rows))

        for row_index, row in enumerate(self._rows):
            for col_index, header in enumerate(self._headers):
                item = QTableWidgetItem(str(row.get(header, "")))
                if header in {"id", "word_count", "sentence_count"}:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_index, col_index, item)

        self._step2_summary.setText(
            f"{len(self._rows)} ligne(s) et {len(self._headers)} colonne(s). "
            "Vous pouvez modifier les colonnes utiles comme `genre` et ajouter des colonnes si besoin."
        )

    def _sync_rows_from_table(self):
        rows: list[dict[str, object]] = []
        for row_index in range(self._table.rowCount()):
            row: dict[str, object] = {}
            for col_index, header in enumerate(self._headers):
                item = self._table.item(row_index, col_index)
                row[header] = item.text().strip() if item else ""
            rows.append(row)
        self._rows = rows

    def _add_custom_column(self):
        name, ok = QInputDialog.getText(self, "Nouvelle colonne", "Nom de la colonne :")
        if not ok or not name.strip():
            return

        column_name = name.strip()
        if column_name in self._headers:
            QMessageBox.warning(self, "Colonne existante", "Cette colonne existe déjà.")
            return

        self._sync_rows_from_table()
        self._headers.append(column_name)
        for row in self._rows:
            row[column_name] = ""
        self._refresh_table()
        self._refresh_review()

    def _apply_genre_batch(self):
        self._sync_rows_from_table()

        genre_value = self._genre_value_edit.text().strip()
        filter_value = self._genre_filter_edit.text().strip().lower()

        if not genre_value:
            QMessageBox.warning(self, "Valeur manquante", "Renseigne une valeur à appliquer à la colonne genre.")
            return

        changed = 0
        for row in self._rows:
            row_id = str(row.get("id", "")).lower()
            if not filter_value or filter_value in row_id:
                row["genre"] = genre_value
                changed += 1

        self._refresh_table()
        self._refresh_review()
        QMessageBox.information(self, "Genre appliqué", f"{changed} ligne(s) mise(s) à jour.")

    def _collect_validation_issues(self) -> list[str]:
        self._sync_rows_from_table()
        result = validate_metadata(self._corpus_dir_edit.text().strip(), self._headers, self._rows)
        issues: list[str] = []
        if result["missing_required_columns"]:
            issues.append("Colonnes requises manquantes : " + ", ".join(result["missing_required_columns"]))
        if result["missing_in_metadata"]:
            issues.append(
                f"IDs présents dans le corpus mais absents du metadata : {len(result['missing_in_metadata'])}"
            )
        if result["missing_in_corpus"]:
            issues.append(
                f"IDs présents dans le metadata mais absents du corpus : {len(result['missing_in_corpus'])}"
            )
        if result["duplicates"]:
            issues.append(f"IDs dupliqués dans le metadata : {len(result['duplicates'])}")
        return issues

    def _refresh_review(self):
        corpus_dir = self._corpus_dir_edit.text().strip()
        metadata_path = Path(corpus_dir) / "metadata.tsv" if corpus_dir else Path("metadata.tsv")
        issues = self._collect_validation_issues() if corpus_dir and self._rows else []

        self._review_summary.setText(
            f"Dossier corpus : {corpus_dir or 'non défini'}\n"
            f"Fichier metadata : {metadata_path}\n"
            f"{len(self._rows)} ligne(s), {len(self._headers)} colonne(s)."
        )

        if issues:
            self._review_issues.setStyleSheet(
                "color: #92400e; background: #fffbeb; border: 1px solid #fcd34d; "
                "border-radius: 6px; padding: 8px 10px;"
            )
            self._review_issues.setText("Incohérences à vérifier :\n- " + "\n- ".join(issues))
        else:
            self._review_issues.setStyleSheet(
                "color: #166534; background: #f0fdf4; border: 1px solid #86efac; "
                "border-radius: 6px; padding: 8px 10px;"
            )
            self._review_issues.setText("Aucune incohérence détectée. Le metadata.tsv est prêt à être enregistré.")

    def _can_go_next_from_step(self, step: int) -> bool:
        corpus_dir = self._corpus_dir_edit.text().strip()
        if step == 0:
            return bool(corpus_dir) and self._corpus_info.get("exists") and self._corpus_info.get("txt_count", 0) > 0
        if step == 1:
            self._sync_rows_from_table()
            return bool(self._rows)
        return True

    def _go_prev(self):
        if self._current_step == 0:
            return
        self._current_step -= 1
        self._stack.setCurrentIndex(self._current_step)
        self._update_navigation()

    def _go_next(self):
        if not self._can_go_next_from_step(self._current_step):
            if self._current_step == 0:
                QMessageBox.warning(self, "Corpus incomplet", "Choisis un dossier contenant au moins un fichier .txt.")
            return

        if self._current_step == 0:
            self._load_corpus_data(self._corpus_dir_edit.text().strip())

        if self._current_step == 1:
            self._refresh_review()

        if self._current_step < self._stack.count() - 1:
            self._current_step += 1
            self._stack.setCurrentIndex(self._current_step)
            self._update_navigation()

    def _update_navigation(self):
        step_titles = [
            "Étape 1 sur 3 - Corpus",
            "Étape 2 sur 3 - Métadonnées",
            "Étape 3 sur 3 - Validation et enregistrement",
        ]
        self._step_label.setText(step_titles[self._current_step])
        self._btn_prev.setEnabled(self._current_step > 0)
        self._btn_next.setVisible(self._current_step < self._stack.count() - 1)
        self._btn_save.setVisible(self._current_step == self._stack.count() - 1)
        self._btn_save.setEnabled(bool(self._rows) and bool(self._corpus_dir_edit.text().strip()))

    def _save_and_accept(self):
        corpus_dir = self._corpus_dir_edit.text().strip()
        if not corpus_dir:
            QMessageBox.warning(self, "Corpus manquant", "Choisis d'abord un dossier de corpus.")
            return

        self._sync_rows_from_table()
        metadata_path = Path(corpus_dir) / "metadata.tsv"

        try:
            write_metadata_tsv(metadata_path, self._headers, self._rows)
        except Exception as exc:
            QMessageBox.critical(self, "Enregistrement impossible", f"Impossible d'écrire le metadata.tsv :\n{exc}")
            return

        super().accept()

    def get_result_config(self) -> dict:
        corpus_dir = self._corpus_dir_edit.text().strip()
        metadata_path = str(Path(corpus_dir) / "metadata.tsv") if corpus_dir else ""
        self._sync_rows_from_table()
        return {
            "path_corpus": corpus_dir,
            "path_metadata": metadata_path,
            "list_metadata": list(self._headers),
        }
