"""
Assistant simplifié de création et mise à jour du metadata.tsv.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QIntValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QToolButton,
    QSpinBox,
    QStackedWidget,
    QStyledItemDelegate,
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


class MetadataColumnDelegate(QStyledItemDelegate):
    def __init__(self, dialog: "MetadataWizardDialog", header: str, parent=None):
        super().__init__(parent)
        self._dialog = dialog
        self._header = header

    def createEditor(self, parent, option, index):
        spec = self._dialog._column_specs.get(self._header, {"type": "text"})
        col_type = spec.get("type", "text")

        if col_type == "closed_list":
            editor = QComboBox(parent)
            editor.setEditable(False)
            editor.addItem("")
            for choice in spec.get("choices", []):
                editor.addItem(choice)
            return editor

        if col_type == "bool":
            editor = QComboBox(parent)
            editor.setEditable(False)
            editor.addItems(["", "true", "false"])
            return editor

        editor = QLineEdit(parent)
        if col_type == "int":
            editor.setValidator(QIntValidator(editor))
        elif col_type == "float":
            validator = QDoubleValidator(editor)
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            editor.setValidator(validator)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole) or ""
        if isinstance(editor, QComboBox):
            pos = editor.findText(str(value))
            editor.setCurrentIndex(pos if pos >= 0 else 0)
        elif isinstance(editor, QLineEdit):
            editor.setText(str(value))

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            value = editor.currentText()
        else:
            value = editor.text()
        normalized = self._dialog._normalize_value_for_column(self._header, value)
        model.setData(index, normalized)


class MetadataWizardDialog(QDialog):
    def __init__(self, initial_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assistant metadata")
        self.setMinimumSize(1080, 760)

        self._initial_config = dict(initial_config)
        self._current_step = 0
        self._headers: list[str] = list(BASE_METADATA_COLUMNS)
        self._rows: list[dict[str, object]] = []
        self._corpus_info: dict[str, object] = {}
        self._column_specs: dict[str, dict[str, object]] = self._default_column_specs()

        self._build_ui()
        self._load_initial_state()

    def _default_column_specs(self) -> dict[str, dict[str, object]]:
        return {
            "id": {"type": "text"},
            "word_count": {"type": "int"},
            "sentence_count": {"type": "int"},
            "genre": {"type": "text"},
        }

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
            QLineEdit, QComboBox, QSpinBox {
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
            "Vous pouvez définir le type des nouvelles colonnes, remplir une sélection, propager une valeur "
            "vers le bas ou limiter une colonne à une liste fermée."
        )
        info.setWordWrap(True)
        info.setProperty("muted", True)
        grp_layout.addWidget(info)

        actions = QHBoxLayout()
        self._btn_add_column = QPushButton("Ajouter une colonne")
        self._btn_add_column.clicked.connect(self._add_custom_column)
        actions.addWidget(self._btn_add_column)

        self._btn_edit_column = QPushButton("Configurer la colonne")
        self._btn_edit_column.clicked.connect(self._configure_selected_column)
        actions.addWidget(self._btn_edit_column)

        self._btn_table_actions = QToolButton()
        self._btn_table_actions.setText("Actions")
        self._btn_table_actions.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._btn_table_actions.setStyleSheet(
            """
            QToolButton {
                background-color: #3a3a5a;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QToolButton:hover {
                background-color: #4a4a6a;
            }
            """
        )
        actions.addWidget(self._btn_table_actions)

        actions.addStretch()
        grp_layout.addLayout(actions)

        batch_group = QGroupBox("Remplissage rapide")
        batch_layout = QVBoxLayout(batch_group)
        batch_layout.setSpacing(8)

        top_row = QHBoxLayout()
        self._fill_column_combo = QComboBox()
        self._fill_column_combo.setMinimumWidth(180)
        top_row.addWidget(self._fill_column_combo)

        self._fill_value_edit = QLineEdit()
        self._fill_value_edit.setPlaceholderText("Valeur à appliquer")
        top_row.addWidget(self._fill_value_edit, 1)

        self._fill_empty_only = QCheckBox("Cellules vides uniquement")
        top_row.addWidget(self._fill_empty_only)
        batch_layout.addLayout(top_row)

        second_row = QHBoxLayout()
        self._btn_fill_selection = QPushButton("Remplir la sélection")
        self._btn_fill_selection.clicked.connect(self._fill_selection_for_column)
        second_row.addWidget(self._btn_fill_selection)

        self._btn_fill_all_rows = QPushButton("Remplir toutes les lignes")
        self._btn_fill_all_rows.clicked.connect(self._fill_all_rows_for_column)
        second_row.addWidget(self._btn_fill_all_rows)

        self._btn_copy_above = QPushButton("Copier la ligne du dessus")
        self._btn_copy_above.clicked.connect(self._copy_value_from_above)
        second_row.addWidget(self._btn_copy_above)

        second_row.addStretch()
        batch_layout.addLayout(second_row)

        genre_fill = QHBoxLayout()
        self._genre_filter_edit = QLineEdit()
        self._genre_filter_edit.setPlaceholderText("Filtre d'ID (vide = tous)")
        genre_fill.addWidget(self._genre_filter_edit, 2)

        self._genre_value_edit = QLineEdit()
        self._genre_value_edit.setPlaceholderText("Valeur à appliquer à genre")
        genre_fill.addWidget(self._genre_value_edit, 1)

        self._btn_apply_genre = QPushButton("Appliquer à genre")
        self._btn_apply_genre.clicked.connect(self._apply_genre_batch)
        genre_fill.addWidget(self._btn_apply_genre)
        batch_layout.addLayout(genre_fill)

        grp_layout.addWidget(batch_group)

        self._table = QTableWidget()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._table.setAlternatingRowColors(True)
        self._table.viewport().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.viewport().customContextMenuRequested.connect(self._open_table_context_menu)
        self._table.viewport().installEventFilter(self)
        self._table.horizontalHeader().sectionDoubleClicked.connect(self._on_header_double_clicked)
        grp_layout.addWidget(self._table, 1)

        self._step2_summary = QLabel("Aucune métadonnée chargée.")
        self._step2_summary.setProperty("muted", True)
        grp_layout.addWidget(self._step2_summary)

        shortcuts_hint = QLabel(
            "Astuce : sélectionnez des cellules puis utilisez le bouton Actions ou les boutons de remplissage."
        )
        shortcuts_hint.setProperty("muted", True)
        grp_layout.addWidget(shortcuts_hint)

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
        self._merge_column_specs_from_rows()
        self._refresh_table()
        self._refresh_review()
        self._update_navigation()

    def _merge_column_specs_from_rows(self):
        for header in self._headers:
            if header not in self._column_specs:
                inferred = "text"
                if header in {"word_count", "sentence_count"}:
                    inferred = "int"
                self._column_specs[header] = {"type": inferred}

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

    def _refresh_fill_column_combo(self):
        current = self._fill_column_combo.currentText() if hasattr(self, "_fill_column_combo") else ""
        self._fill_column_combo.blockSignals(True)
        self._fill_column_combo.clear()
        self._fill_column_combo.addItems(self._headers)
        if current:
            idx = self._fill_column_combo.findText(current)
            if idx >= 0:
                self._fill_column_combo.setCurrentIndex(idx)
        self._fill_column_combo.blockSignals(False)

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

        self._install_column_delegates()
        self._refresh_actions_menu()
        self._refresh_fill_column_combo()

        self._step2_summary.setText(
            f"{len(self._rows)} ligne(s) et {len(self._headers)} colonne(s). "
            "Vous pouvez définir des types, limiter des valeurs et accélérer le remplissage."
        )

    def _install_column_delegates(self):
        for col_index, header in enumerate(self._headers):
            self._table.setItemDelegateForColumn(col_index, MetadataColumnDelegate(self, header, self._table))

    def _sync_rows_from_table(self):
        rows: list[dict[str, object]] = []
        for row_index in range(self._table.rowCount()):
            row: dict[str, object] = {}
            for col_index, header in enumerate(self._headers):
                item = self._table.item(row_index, col_index)
                raw_value = item.text().strip() if item else ""
                row[header] = self._normalize_value_for_column(header, raw_value)
            rows.append(row)
        self._rows = rows

    def _normalize_value_for_column(self, header: str, value: object) -> str:
        spec = self._column_specs.get(header, {"type": "text"})
        col_type = spec.get("type", "text")
        text = str(value).strip() if value is not None else ""

        if text == "":
            return ""

        if col_type == "bool":
            lowered = text.lower()
            return "true" if lowered in {"1", "true", "yes", "oui"} else "false"

        if col_type == "int":
            try:
                return str(int(float(text)))
            except Exception:
                return ""

        if col_type == "float":
            try:
                return str(float(text)).rstrip("0").rstrip(".")
            except Exception:
                return ""

        if col_type == "closed_list":
            choices = [str(c) for c in spec.get("choices", [])]
            return text if text in choices else ""

        return text

    def _ask_column_type(self, current_type: str = "text") -> tuple[str | None, list[str]]:
        options = [
            ("text", "Texte libre"),
            ("closed_list", "Liste fermée"),
            ("bool", "Booléen"),
            ("int", "Numérique entier"),
            ("float", "Numérique décimal"),
        ]
        labels = [label for _, label in options]
        current_index = next((i for i, (value, _) in enumerate(options) if value == current_type), 0)
        selected_label, ok = QInputDialog.getItem(
            self,
            "Type de colonne",
            "Choisissez le type de la colonne :",
            labels,
            current_index,
            False,
        )
        if not ok:
            return None, []

        selected_type = next(value for value, label in options if label == selected_label)
        choices: list[str] = []
        if selected_type == "closed_list":
            raw_choices, ok = QInputDialog.getText(
                self,
                "Liste fermée",
                "Valeurs autorisées (séparées par des virgules) :",
            )
            if not ok:
                return None, []
            choices = [choice.strip() for choice in raw_choices.split(",") if choice.strip()]
            if not choices:
                QMessageBox.warning(self, "Liste vide", "Renseignez au moins une valeur autorisée.")
                return None, []

        return selected_type, choices

    def _add_custom_column(self):
        name, ok = QInputDialog.getText(self, "Nouvelle colonne", "Nom de la colonne :")
        if not ok or not name.strip():
            return

        column_name = name.strip()
        if column_name in self._headers:
            QMessageBox.warning(self, "Colonne existante", "Cette colonne existe déjà.")
            return

        col_type, choices = self._ask_column_type("text")
        if not col_type:
            return

        self._sync_rows_from_table()
        self._headers.append(column_name)
        self._column_specs[column_name] = {"type": col_type}
        if choices:
            self._column_specs[column_name]["choices"] = choices
        for row in self._rows:
            row[column_name] = ""
        self._refresh_table()
        self._refresh_review()

    def _selected_header(self) -> str | None:
        column = self._table.currentColumn()
        if column < 0 or column >= len(self._headers):
            return None
        return self._headers[column]

    def _on_header_double_clicked(self, section: int):
        if 0 <= section < len(self._headers):
            self._table.setCurrentCell(0 if self._table.rowCount() else -1, section)
            self._configure_selected_column()

    def _configure_selected_column(self):
        header = self._selected_header() or self._fill_column_combo.currentText()
        if not header:
            QMessageBox.information(self, "Aucune colonne", "Sélectionnez d'abord une colonne à configurer.")
            return

        if header in {"id", "word_count", "sentence_count"}:
            QMessageBox.information(self, "Colonne verrouillée", "Cette colonne système ne peut pas être reconfigurée.")
            return

        current_spec = self._column_specs.get(header, {"type": "text"})
        col_type, choices = self._ask_column_type(str(current_spec.get("type", "text")))
        if not col_type:
            return

        self._column_specs[header] = {"type": col_type}
        if choices:
            self._column_specs[header]["choices"] = choices

        self._sync_rows_from_table()
        for row in self._rows:
            row[header] = self._normalize_value_for_column(header, row.get(header, ""))
        self._refresh_table()
        self._refresh_review()

    def _selected_target_rows(self) -> list[int]:
        rows = sorted({item.row() for item in self._table.selectedItems()})
        if rows:
            return rows
        current_row = self._table.currentRow()
        return [current_row] if current_row >= 0 else []

    def _fill_rows_for_column(self, row_indexes: list[int], header: str, value: str):
        if not row_indexes:
            QMessageBox.information(self, "Aucune sélection", "Sélectionnez au moins une cellule ou une ligne.")
            return

        normalized = self._normalize_value_for_column(header, value)
        spec = self._column_specs.get(header, {"type": "text"})
        if value.strip() and normalized == "" and spec.get("type") in {"closed_list", "int", "float"}:
            QMessageBox.warning(self, "Valeur invalide", "La valeur n'est pas compatible avec le type de colonne.")
            return

        changed = 0
        col_index = self._headers.index(header)
        for row_index in row_indexes:
            item = self._table.item(row_index, col_index)
            if item is None:
                item = QTableWidgetItem("")
                self._table.setItem(row_index, col_index, item)
            if self._fill_empty_only.isChecked() and item.text().strip():
                continue
            item.setText(normalized)
            changed += 1

        self._sync_rows_from_table()
        self._refresh_review()
        QMessageBox.information(self, "Remplissage terminé", f"{changed} cellule(s) mise(s) à jour.")

    def _fill_selection_for_column(self):
        header = self._fill_column_combo.currentText().strip()
        if not header:
            return
        self._fill_rows_for_column(self._selected_target_rows(), header, self._fill_value_edit.text())

    def _fill_all_rows_for_column(self):
        header = self._fill_column_combo.currentText().strip()
        if not header:
            return
        self._fill_rows_for_column(list(range(self._table.rowCount())), header, self._fill_value_edit.text())

    def _copy_value_from_above(self):
        selected_items = self._table.selectedItems()
        if not selected_items:
            current_row = self._table.currentRow()
            current_col = self._table.currentColumn()
            if current_row <= 0 or current_col < 0:
                QMessageBox.information(self, "Impossible", "Placez-vous sur une cellule située sous une autre valeur.")
                return
            selected_items = [self._table.item(current_row, current_col)]

        changed = 0
        for item in selected_items:
            if item is None:
                continue
            row = item.row()
            col = item.column()
            if row <= 0:
                continue
            source = self._table.item(row - 1, col)
            if source is None:
                continue
            if self._fill_empty_only.isChecked() and item.text().strip():
                continue
            item.setText(source.text())
            changed += 1

        self._sync_rows_from_table()
        self._refresh_review()
        if changed:
            QMessageBox.information(self, "Copie terminée", f"{changed} cellule(s) mise(s) à jour.")

    def _open_table_context_menu(self, pos):
        item = self._table.itemAt(pos)
        if item is not None:
            self._table.setCurrentItem(item)

        menu = self._build_table_actions_menu()
        chosen = menu.exec(self._table.viewport().mapToGlobal(pos))

        self._handle_table_menu_action(chosen)

    def _build_table_actions_menu(self) -> QMenu:
        menu = QMenu(self)
        action_copy_above = menu.addAction("Copier la valeur de la ligne du dessus")
        action_copy_above.setData("copy_above")
        action_fill_selection = menu.addAction("Remplir la sélection avec la valeur saisie")
        action_fill_selection.setData("fill_selection")
        action_fill_all = menu.addAction("Remplir toutes les lignes avec la valeur saisie")
        action_fill_all.setData("fill_all")
        menu.addSeparator()
        action_configure = menu.addAction("Configurer la colonne sélectionnée")
        action_configure.setData("configure_column")
        return menu

    def _refresh_actions_menu(self):
        if hasattr(self, "_btn_table_actions"):
            self._btn_table_actions.setMenu(self._build_table_actions_menu())

    def _handle_table_menu_action(self, action):
        if action is None:
            return
        action_id = action.data()
        if action_id == "copy_above":
            self._copy_value_from_above()
        elif action_id == "fill_selection":
            self._fill_selection_for_column()
        elif action_id == "fill_all":
            self._fill_all_rows_for_column()
        elif action_id == "configure_column":
            self._configure_selected_column()

    def eventFilter(self, obj, event):
        if obj is self._table.viewport() and event.type() == QEvent.Type.ContextMenu:
            pos = event.pos()
            self._open_table_context_menu(pos)
            return True
        return super().eventFilter(obj, event)

    def _apply_genre_batch(self):
        self._sync_rows_from_table()

        genre_value = self._genre_value_edit.text().strip()
        filter_value = self._genre_filter_edit.text().strip().lower()

        if not genre_value:
            QMessageBox.warning(self, "Valeur manquante", "Renseignez une valeur à appliquer à la colonne genre.")
            return

        changed = 0
        for row in self._rows:
            row_id = str(row.get("id", "")).lower()
            if not filter_value or filter_value in row_id:
                if self._fill_empty_only.isChecked() and str(row.get("genre", "")).strip():
                    continue
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

        typed_columns = [
            f"{header} ({self._column_specs.get(header, {}).get('type', 'text')})"
            for header in self._headers
            if self._column_specs.get(header, {}).get("type", "text") != "text"
        ]
        typed_columns_text = ", ".join(typed_columns) if typed_columns else "aucun type spécial défini"

        self._review_summary.setText(
            f"Dossier corpus : {corpus_dir or 'non défini'}\n"
            f"Fichier metadata : {metadata_path}\n"
            f"{len(self._rows)} ligne(s), {len(self._headers)} colonne(s).\n"
            f"Colonnes typées : {typed_columns_text}."
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
                QMessageBox.warning(self, "Corpus incomplet", "Choisissez un dossier contenant au moins un fichier .txt.")
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
            QMessageBox.warning(self, "Corpus manquant", "Choisissez d'abord un dossier de corpus.")
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
            "metadata_column_specs": dict(self._column_specs),
        }
