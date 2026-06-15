"""
Assistant simplifié de création et modification du metadata.tsv
@jcharlesDS (2026)
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog,
    QGroupBox, QWidget, QStackedWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from gui.core.metadata_tools import (
    BASE_METADATA_COLUMNS,
    scan_corpus_dir,
    load_metadata_tsv,
    write_metadata_tsv,
    merge_corpus_and_metadata,
    validate_metadata,
)


class MetadataWizardDialog(QDialog):
    def __init__(self, initial_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assistant metadata")
        self.setMinimumSize(1080, 760)

        self._headers: list[str] = list(BASE_METADATA_COLUMNS)
        self._rows: list[dict[str, object]] = []
        self._last_validation_result: dict[str, object] | None = None
        self._current_step = 0

        self._initial_config = dict(initial_config)
        self._build_ui()
        self._load_initial_state()
        self._fit_to_screen()

    def _build_ui(self):
        self.setStyleSheet("""
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
            QTableWidget {
                background: #ffffff;
                color: #111827;
                border: 1px solid #d4d7e3;
                border-radius: 6px;
                gridline-color: #e5e7eb;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("Assistant metadata")
        title.setFont(QFont("Helvetica Neue", 17, QFont.Weight.Bold))
        root.addWidget(title)

        subtitle = QLabel(
            "Créez un metadata.tsv pour un corpus qui n'en a pas encore, "
            "ou chargez un metadata.tsv existant pour le modifier."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #4b5563;")
        root.addWidget(subtitle)

        self._step_label = QLabel()
        self._step_label.setStyleSheet("color: #6b7280; font-size: 13px;")
        root.addWidget(self._step_label)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_source_page())
        self._stack.addWidget(self._build_editor_page())
        self._stack.addWidget(self._build_validation_page())
        root.addWidget(self._stack, 1)

        buttons = QHBoxLayout()
        self._btn_cancel = QPushButton("Annuler")
        self._btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(self._btn_cancel)

        buttons.addStretch()

        self._btn_previous = QPushButton("Précédent")
        self._btn_previous.clicked.connect(self._go_previous)
        buttons.addWidget(self._btn_previous)

        self._btn_next = QPushButton("Suivant")
        self._btn_next.clicked.connect(self._go_next)
        buttons.addWidget(self._btn_next)

        self._btn_ok = QPushButton("Enregistrer et fermer")
        self._btn_ok.clicked.connect(self.accept)
        buttons.addWidget(self._btn_ok)

        root.addLayout(buttons)
        self._update_step_ui()

    def _fit_to_screen(self):
        """Ajuste la taille initiale du dialogue à l'écran disponible."""
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 860)
            return

        available = screen.availableGeometry()
        width = max(1080, int(available.width() * 0.82))
        height = max(760, int(available.height() * 0.88))
        width = min(width, available.width())
        height = min(height, available.height())
        self.resize(width, height)

    def _build_source_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        group = QGroupBox("Étape 1. Corpus")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)
        layout.setSpacing(10)

        intro = QLabel(
            "Choisissez le dossier du corpus. L'assistant détecte automatiquement "
            "si un metadata.tsv existe déjà et se place en mode création ou modification."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #4b5563; font-weight: normal;")
        group_layout.addWidget(intro)

        corpus_row = QHBoxLayout()
        corpus_label = QLabel("Dossier corpus :")
        corpus_label.setFixedWidth(150)
        self._corpus_dir_edit = QLineEdit()
        self._btn_browse_corpus = QPushButton("Parcourir")
        self._btn_browse_corpus.clicked.connect(self._browse_corpus_dir)
        corpus_row.addWidget(corpus_label)
        corpus_row.addWidget(self._corpus_dir_edit, 1)
        corpus_row.addWidget(self._btn_browse_corpus)
        group_layout.addLayout(corpus_row)

        metadata_row = QHBoxLayout()
        metadata_label = QLabel("Fichier metadata :")
        metadata_label.setFixedWidth(150)
        self._metadata_path_edit = QLineEdit()
        self._btn_browse_metadata = QPushButton("Choisir le fichier")
        self._btn_browse_metadata.clicked.connect(self._browse_metadata_path)
        metadata_row.addWidget(metadata_label)
        metadata_row.addWidget(self._metadata_path_edit, 1)
        metadata_row.addWidget(self._btn_browse_metadata)
        group_layout.addLayout(metadata_row)

        self._source_status_label = QLabel("Aucune source sélectionnée.")
        self._source_status_label.setWordWrap(True)
        self._source_status_label.setStyleSheet(
            "color: #374151; background: #f8fafc; border: 1px solid #e5e7eb; "
            "border-radius: 6px; padding: 10px; font-weight: normal;"
        )
        group_layout.addWidget(self._source_status_label)

        actions = QHBoxLayout()
        self._btn_scan = QPushButton("Créer / actualiser à partir du corpus")
        self._btn_scan.clicked.connect(self._scan_corpus)
        actions.addWidget(self._btn_scan)

        self._btn_import = QPushButton("Charger un metadata existant")
        self._btn_import.clicked.connect(self._import_tsv)
        actions.addWidget(self._btn_import)

        self._btn_export = QPushButton("Enregistrer")
        self._btn_export.clicked.connect(self._export_tsv)
        actions.addWidget(self._btn_export)

        actions.addStretch()
        group_layout.addLayout(actions)
        layout.addWidget(group)
        layout.addStretch()
        return page

    def _build_editor_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        group = QGroupBox("Étape 2. Métadonnées")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)
        layout.setSpacing(10)

        intro = QLabel(
            "Les colonnes techniques `id`, `word_count` et `sentence_count` sont "
            "générées automatiquement à partir du corpus. Modifiez surtout les "
            "colonnes descriptives comme `genre` ou vos colonnes personnalisées."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #4b5563; font-weight: normal;")
        group_layout.addWidget(intro)

        self._summary_label = QLabel("Aucune donnée chargée.")
        self._summary_label.setWordWrap(True)
        self._summary_label.setStyleSheet("color: #4b5563; font-weight: normal;")
        group_layout.addWidget(self._summary_label)

        advanced = QGroupBox("Actions facultatives")
        advanced_layout = QVBoxLayout(advanced)
        advanced_layout.setSpacing(8)

        batch_row = QHBoxLayout()
        self._genre_pattern_edit = QLineEdit()
        self._genre_pattern_edit.setPlaceholderText("Filtre d'ID (optionnel, ex: presse, a0, chap)")
        batch_row.addWidget(self._genre_pattern_edit, 2)

        self._genre_value_edit = QLineEdit()
        self._genre_value_edit.setPlaceholderText("Valeur à appliquer dans la colonne genre")
        batch_row.addWidget(self._genre_value_edit, 2)

        self._btn_apply_genre = QPushButton("Remplir le genre")
        self._btn_apply_genre.clicked.connect(self._apply_genre_batch)
        batch_row.addWidget(self._btn_apply_genre)
        advanced_layout.addLayout(batch_row)

        column_row = QHBoxLayout()
        column_help = QLabel("Besoin d'une autre colonne descriptive ?")
        column_help.setStyleSheet("color: #4b5563; font-weight: normal;")
        column_row.addWidget(column_help)
        column_row.addStretch()

        self._btn_add_column = QPushButton("Ajouter une colonne")
        self._btn_add_column.clicked.connect(self._add_custom_column)
        column_row.addWidget(self._btn_add_column)
        advanced_layout.addLayout(column_row)

        group_layout.addWidget(advanced)

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        group_layout.addWidget(self._table, 1)
        layout.addWidget(group, 1)
        return page

    def _build_validation_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        group = QGroupBox("Étape 3. Validation et enregistrement")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)
        layout.setSpacing(10)

        analysis_help = QLabel(
            "Colonnes utilisées ensuite dans l'analyse pour créer des partitions "
            "ou regroupements. Séparez-les par des virgules."
        )
        analysis_help.setWordWrap(True)
        analysis_help.setStyleSheet("color: #4b5563; font-weight: normal;")
        group_layout.addWidget(analysis_help)

        analysis_row = QHBoxLayout()
        analysis_label = QLabel("Colonnes d'analyse :")
        analysis_label.setFixedWidth(150)
        self._analysis_columns_edit = QLineEdit()
        self._analysis_columns_edit.setPlaceholderText("id, genre, word_count, sentence_count")
        analysis_row.addWidget(analysis_label)
        analysis_row.addWidget(self._analysis_columns_edit, 1)
        group_layout.addLayout(analysis_row)

        self._validation_label = QLabel("Aucune validation effectuée pour le moment.")
        self._validation_label.setWordWrap(True)
        self._validation_label.setStyleSheet(
            "color: #374151; background: #f8fafc; border: 1px solid #e5e7eb; "
            "border-radius: 6px; padding: 10px; font-weight: normal;"
        )
        group_layout.addWidget(self._validation_label)

        actions = QHBoxLayout()
        self._btn_validate = QPushButton("Vérifier la cohérence")
        self._btn_validate.clicked.connect(self._validate_current_data)
        actions.addWidget(self._btn_validate)

        self._btn_save_only = QPushButton("Enregistrer maintenant")
        self._btn_save_only.clicked.connect(self._export_tsv)
        actions.addWidget(self._btn_save_only)

        actions.addStretch()
        group_layout.addLayout(actions)
        layout.addWidget(group)
        layout.addStretch()
        return page

    def _update_step_ui(self):
        labels = [
            "Étape 1 sur 3: choisir le corpus et le fichier metadata",
            "Étape 2 sur 3: éditer les métadonnées",
            "Étape 3 sur 3: valider et enregistrer",
        ]
        self._stack.setCurrentIndex(self._current_step)
        self._step_label.setText(labels[self._current_step])
        self._btn_previous.setEnabled(self._current_step > 0)
        self._btn_next.setVisible(self._current_step < 2)
        self._btn_ok.setVisible(self._current_step == 2)

    def _go_previous(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step_ui()

    def _go_next(self):
        if self._current_step == 0:
            self._refresh_source_status()
        elif self._current_step == 1:
            self._sync_rows_from_table()
        if self._current_step < 2:
            self._current_step += 1
            self._update_step_ui()

    def _load_initial_state(self):
        corpus_dir = self._initial_config.get("metadata_corpus_dir", "./Data/Corpus/Textes_raw")
        self._corpus_dir_edit.setText(corpus_dir)

        configured_metadata = self._initial_config.get("path_metadata", "").strip()
        if configured_metadata:
            self._metadata_path_edit.setText(configured_metadata)
        else:
            self._metadata_path_edit.setText(str(Path(corpus_dir) / "metadata.tsv"))

        self._analysis_columns_edit.setText(
            ", ".join(self._initial_config.get("list_metadata", ["id", "genre"]))
        )
        self._refresh_source_status()

        corpus_dir_path = Path(self._corpus_dir_edit.text().strip())
        if corpus_dir_path.exists():
            self._scan_corpus()

        metadata_path = Path(self._metadata_path_edit.text().strip())
        if metadata_path.exists():
            self._import_tsv(path_override=metadata_path)

    def _browse_corpus_dir(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier du corpus",
            self._corpus_dir_edit.text().strip() or ".",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            self._corpus_dir_edit.setText(path)
            current_metadata = self._metadata_path_edit.text().strip()
            if (not current_metadata) or current_metadata.endswith("metadata.tsv"):
                self._metadata_path_edit.setText(str(Path(path) / "metadata.tsv"))
            self._refresh_source_status()

    def _browse_metadata_path(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Choisir le fichier metadata.tsv",
            self._metadata_path_edit.text().strip() or "metadata.tsv",
            "TSV (*.tsv)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            self._metadata_path_edit.setText(path)
            self._refresh_source_status()

    def _sync_rows_from_table(self):
        rows: list[dict[str, object]] = []
        for row_index in range(self._table.rowCount()):
            row: dict[str, object] = {}
            for col_index, header in enumerate(self._headers):
                item = self._table.item(row_index, col_index)
                row[header] = item.text().strip() if item else ""
            rows.append(row)
        self._rows = rows

    def _refresh_source_status(self):
        corpus_dir = Path(self._corpus_dir_edit.text().strip())
        metadata_path = Path(self._metadata_path_edit.text().strip())

        if not self._corpus_dir_edit.text().strip():
            self._source_status_label.setText("Sélectionnez d'abord un dossier de corpus.")
            return

        if not corpus_dir.exists():
            self._source_status_label.setText(
                f"<b>Corpus introuvable.</b><br>{corpus_dir}"
            )
            return

        txt_count = len(list(corpus_dir.glob("*.txt")))
        if metadata_path.exists():
            mode_text = "metadata.tsv détecté : l'assistant est en mode modification."
            color = "#166534"
        else:
            mode_text = "Aucun metadata.tsv détecté : l'assistant créera un nouveau fichier."
            color = "#92400e"

        self._source_status_label.setText(
            f"<b style='color:{color};'>{mode_text}</b><br>"
            f"{txt_count} fichier(s) .txt détecté(s) dans <b>{corpus_dir.name}</b>.<br>"
            f"Fichier cible : {metadata_path}"
        )

    def _refresh_table(self):
        self._table.clear()
        self._table.setColumnCount(len(self._headers))
        self._table.setHorizontalHeaderLabels(self._headers)
        self._table.setRowCount(len(self._rows))

        for row_index, row in enumerate(self._rows):
            for col_index, header in enumerate(self._headers):
                value = str(row.get(header, ""))
                item = QTableWidgetItem(value)

                if header in {"id", "word_count", "sentence_count"}:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(Qt.GlobalColor.lightGray)

                self._table.setItem(row_index, col_index, item)

        custom_headers = [header for header in self._headers if header not in BASE_METADATA_COLUMNS]
        custom_label = ", ".join(custom_headers) if custom_headers else "aucune"
        self._summary_label.setText(
            f"{len(self._rows)} entrée(s) | {len(self._headers)} colonne(s)<br>"
            f"Colonnes éditables principales : genre, {custom_label}"
        )

    def _refresh_validation_label(self, result: dict[str, object] | None = None):
        if result is None:
            self._validation_label.setText("Aucune validation effectuée pour le moment.")
            return

        issues = []
        if result["missing_required_columns"]:
            issues.append("Colonnes requises manquantes: " + ", ".join(result["missing_required_columns"]))
        if result["missing_in_metadata"]:
            issues.append(f"IDs du corpus absents du metadata: {len(result['missing_in_metadata'])}")
        if result["missing_in_corpus"]:
            issues.append(f"IDs du metadata absents du corpus: {len(result['missing_in_corpus'])}")
        if result["duplicates"]:
            issues.append(f"IDs dupliqués dans le metadata: {len(result['duplicates'])}")

        if issues:
            self._validation_label.setText(
                "<b style='color:#b91c1c;'>Des incohérences ont été détectées.</b><br>"
                + "<br>".join(issues)
            )
        else:
            self._validation_label.setText(
                f"<b style='color:#166534;'>Metadata cohérent.</b><br>"
                f"{result['corpus_count']} texte(s) dans le corpus, "
                f"{result['metadata_count']} ligne(s) dans le metadata."
            )

    def _scan_corpus(self, _checked: bool = False):
        try:
            corpus_dir = self._corpus_dir_edit.text().strip()
            if not corpus_dir:
                QMessageBox.warning(self, "Corpus manquant", "Renseignez d'abord le dossier du corpus.")
                return

            current_headers = list(self._headers)
            current_rows = list(self._rows)
            corpus_rows = scan_corpus_dir(corpus_dir)

            if not corpus_rows:
                QMessageBox.warning(self, "Corpus vide", "Aucun fichier .txt trouvé dans ce dossier.")
                return

            self._headers, self._rows = merge_corpus_and_metadata(
                corpus_rows,
                current_headers,
                [{h: str(row.get(h, "")) for h in current_headers} for row in current_rows],
            )

            if not self._analysis_columns_edit.text().strip():
                self._analysis_columns_edit.setText(", ".join(self._headers))

            self._refresh_source_status()
            self._refresh_table()
            self._last_validation_result = None
            self._refresh_validation_label()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur scan corpus", f"Impossible de scanner le corpus:\n{exc}")

    def _import_tsv(self, _checked: bool = False, path_override: Path | None = None):
        try:
            path = path_override
            if path is None:
                selected, _ = QFileDialog.getOpenFileName(
                    self,
                    "Charger un metadata.tsv existant",
                    self._metadata_path_edit.text().strip() or ".",
                    "TSV (*.tsv)",
                    options=QFileDialog.Option.DontUseNativeDialog,
                )
                if not selected:
                    return
                path = Path(selected)

            headers, imported_rows = load_metadata_tsv(path)
            if not headers:
                QMessageBox.warning(self, "Import impossible", "Le fichier TSV est vide ou invalide.")
                return

            self._metadata_path_edit.setText(str(path))

            corpus_rows = scan_corpus_dir(self._corpus_dir_edit.text().strip())
            self._headers, self._rows = merge_corpus_and_metadata(corpus_rows, headers, imported_rows)

            if not self._analysis_columns_edit.text().strip():
                self._analysis_columns_edit.setText(", ".join(self._headers))

            self._refresh_source_status()
            self._refresh_table()
            self._validate_current_data(show_success=False)
        except Exception as exc:
            QMessageBox.critical(self, "Erreur import metadata", f"Impossible de charger le fichier TSV:\n{exc}")

    def _export_tsv(self, _checked: bool = False):
        try:
            self._sync_rows_from_table()
            metadata_path = self._metadata_path_edit.text().strip()
            if not metadata_path:
                QMessageBox.warning(self, "Chemin manquant", "Renseignez d'abord le chemin du metadata.tsv.")
                return

            write_metadata_tsv(metadata_path, self._headers, self._rows)
            self._refresh_source_status()
            QMessageBox.information(self, "Enregistrement réussi", f"metadata.tsv enregistré vers :\n{metadata_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur export metadata", f"Impossible d'enregistrer le fichier TSV:\n{exc}")

    def _validate_current_data(self, _checked: bool = False, show_success: bool = True):
        self._sync_rows_from_table()
        result = validate_metadata(self._corpus_dir_edit.text().strip(), self._headers, self._rows)
        self._last_validation_result = result
        self._refresh_validation_label(result)

        issues = []
        if result["missing_required_columns"]:
            issues.append("Colonnes requises manquantes: " + ", ".join(result["missing_required_columns"]))
        if result["missing_in_metadata"]:
            issues.append(f"IDs présents dans le corpus mais absents du metadata: {len(result['missing_in_metadata'])}")
        if result["missing_in_corpus"]:
            issues.append(f"IDs présents dans le metadata mais absents du corpus: {len(result['missing_in_corpus'])}")
        if result["duplicates"]:
            issues.append(f"IDs dupliqués dans le metadata: {len(result['duplicates'])}")

        if issues:
            QMessageBox.warning(
                self,
                "Validation metadata/corpus",
                "Des incohérences ont été détectées:\n\n- " + "\n- ".join(issues)
            )
        elif show_success:
            QMessageBox.information(
                self,
                "Validation réussie",
                "Le metadata.tsv est cohérent avec le corpus."
            )

    def _apply_genre_batch(self, _checked: bool = False):
        self._sync_rows_from_table()

        genre_value = self._genre_value_edit.text().strip()
        pattern = self._genre_pattern_edit.text().strip().lower()

        if not genre_value:
            QMessageBox.warning(self, "Genre manquant", "Renseignez une valeur de genre.")
            return

        changed = 0
        for row in self._rows:
            row_id = str(row.get("id", "")).lower()
            if not pattern or pattern in row_id:
                row["genre"] = genre_value
                changed += 1

        self._refresh_table()
        QMessageBox.information(
            self,
            "Attribution du genre",
            f"{changed} ligne(s) mise(s) à jour."
        )

    def _add_custom_column(self, _checked: bool = False):
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

        if self._analysis_columns_edit.text().strip():
            current = [x.strip() for x in self._analysis_columns_edit.text().split(",") if x.strip()]
            if column_name not in current:
                current.append(column_name)
                self._analysis_columns_edit.setText(", ".join(current))

    def get_result_config(self) -> dict:
        self._sync_rows_from_table()
        metadata_path = self._metadata_path_edit.text().strip() or "./Data/Corpus/metadata.tsv"
        list_metadata = [
            x.strip()
            for x in self._analysis_columns_edit.text().split(",")
            if x.strip()
        ] or list(self._headers)

        return {
            "path_metadata": metadata_path,
            "metadata_corpus_dir": self._corpus_dir_edit.text().strip() or "./Data/Corpus/Textes_raw",
            "list_metadata": list_metadata,
        }

    def accept(self):
        self._sync_rows_from_table()

        metadata_path = self._metadata_path_edit.text().strip()
        if not metadata_path:
            QMessageBox.warning(self, "Chemin manquant", "Renseignez le chemin de sortie du metadata.tsv.")
            return

        try:
            write_metadata_tsv(metadata_path, self._headers, self._rows)
        except Exception as exc:
            QMessageBox.critical(self, "Export impossible", f"Impossible d'écrire le metadata.tsv:\n{exc}")
            return

        super().accept()
