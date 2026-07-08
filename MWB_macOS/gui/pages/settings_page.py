"""
Page Paramètres : Configuration de l'application.
@jcharlesDS (2026)
"""

import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QComboBox, QSpinBox, QMessageBox,
    QFormLayout, QDialog, QListWidget, QListWidgetItem, QCheckBox, QFileDialog
)
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import Qt, QUrl

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT
from gui.core.app_settings import load_app_settings, save_app_settings
from gui.core.prepared_archive import (
    create_prepared_archive,
    default_archive_path,
    has_prepared_archive_content,
)


class SettingsPage(BasePage):
    """Page de paramètres de l'application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._settings_file = self._project_root / "logs" / "app_settings.json"
        
        # Charger les paramètres de l'application
        self._load_settings()
        
        self._build_ui()
        self._refresh_cache_info()
    
    def _load_settings(self):
        """Charge les paramètres de l'application depuis app_settings.json."""
        self._settings = load_app_settings(self._project_root)
    
    def _save_settings(self):
        """Sauvegarde les paramètres dans app_settings.json."""
        try:
            save_app_settings(self._project_root, self._settings)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de sauvegarder les paramètres:\n{e}")
            return False
    
    # --- Construction UI ---
    
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)
        
        # Titre
        layout.addWidget(self.make_title(
            "Paramètres de l'application",
            "Gérez les dossiers, modèles NLP, logs et paramètres avancés."
        ))
        
        # Section 1: Dossiers de l'application
        layout.addWidget(self._build_folders_section())
        
        # Section 2: Modèles NLP
        layout.addWidget(self._build_models_section())
        
        # Section 3: Logs et diagnostic
        layout.addWidget(self._build_logs_section())
        
        # Section 4: Paramètres avancés
        layout.addWidget(self._build_advanced_section())
        
        layout.addStretch()
        
        scroll.setWidget(content)
        outer.addWidget(scroll)
        
        # Bouton global d'enregistrement en bas
        bottom_bar = QWidget()
        bottom_bar.setStyleSheet("background-color: #ffffff; border-top: 1px solid #e5e7eb; padding: 12px;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(32, 12, 32, 12)
        
        btn_save_all = QPushButton("Enregistrer les paramètres")
        btn_save_all.setFixedHeight(40)
        btn_save_all.setFixedWidth(220)
        btn_save_all.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:pressed {{
                background-color: #2a2a4a;
            }}
        """)
        btn_save_all.clicked.connect(self._save_all_settings)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_save_all)
        bottom_layout.addStretch()
        
        outer.addWidget(bottom_bar)
    
    # === SECTION 1: DOSSIERS ===
    
    def _build_folders_section(self):
        """Section dossiers de l'application."""
        group = self.make_group("Dossiers de l'application")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Dossier Corpus
        corpus_dir = self._project_root / "Data" / "Corpus"
        layout.addWidget(self._folder_row(
            "Corpus",
            corpus_dir,
            "Dossiers contenant les corpus à analyser."
        ))
        
        # Dossier Analyses
        analyses_dir = self._project_root / "Data" / "analyses"
        layout.addWidget(self._folder_row(
            "Analyses",
            analyses_dir,
            "Résultats des analyses (patterns, clustering, statistiques)."
        ))
        
        # Dossier Logs
        logs_dir = self._project_root / "logs"
        layout.addWidget(self._folder_row(
            "Logs",
            logs_dir,
            "Fichiers de logs de l'application et des analyses."
        ))
        
        return group
    
    def _folder_row(self, label: str, path: Path, description: str):
        """Crée une ligne pour un dossier avec bouton d'ouverture."""
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(8, 4, 8, 4)
        row_layout.setSpacing(12)
        
        # Label et description
        text_container = QWidget()
        text_container.setStyleSheet("background-color: transparent;")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        lbl = QLabel(label)
        lbl.setFont(QFont("Helvetica Neue", 13, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        text_layout.addWidget(lbl)
        
        path_lbl = QLabel(str(path))
        path_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent; font-size: 12px;")
        text_layout.addWidget(path_lbl)
        
        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent; font-size: 11px; font-style: italic;")
        text_layout.addWidget(desc_lbl)
        
        row_layout.addWidget(text_container, 1)
        
        # Bouton Ouvrir
        btn_open = QPushButton("Ouvrir")
        btn_open.setFixedHeight(32)
        btn_open.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:pressed {{
                background-color: #2a2a4a;
            }}
        """)
        btn_open.clicked.connect(lambda: self._open_folder(path))
        row_layout.addWidget(btn_open)

        manage_handler = None
        if label == "Corpus":
            manage_handler = self._open_corpus_manager
        elif label == "Analyses":
            manage_handler = self._open_analysis_manager

        if manage_handler is not None:
            btn_manage = QPushButton("Gérer…")
            btn_manage.setFixedHeight(32)
            btn_manage.setStyleSheet(self._button_style("#8a3a3a"))
            btn_manage.clicked.connect(manage_handler)
            row_layout.addWidget(btn_manage)
        
        return container
    
    def _open_folder(self, path: Path):
        """Ouvre un dossier dans le finder/explorateur."""
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_corpus_manager(self):
        corpus_root = self._project_root / "Data" / "Corpus"
        entries = []
        if corpus_root.exists():
            for child in sorted(corpus_root.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    entries.append((child.name, child))

        dialog = FolderDeletionDialog(
            "Gestion des corpus",
            "Sélectionnez les dossiers de corpus à supprimer.",
            entries,
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_paths = dialog.selected_paths()
        if not selected_paths:
            return

        names = [path.name for path in selected_paths]
        reply = QMessageBox.question(
            self,
            "Supprimer des corpus",
            "Supprimer les corpus sélectionnés ?\n\n" + "\n".join(names),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted = 0
        errors = []
        for path in selected_paths:
            try:
                shutil.rmtree(path)
                deleted += 1
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")

        self._show_deletion_summary("corpus", deleted, errors)

    def _open_analysis_manager(self):
        analyses_root = self._project_root / "Data" / "analyses"
        entries = []
        if analyses_root.exists():
            for analysis_group_dir in sorted(analyses_root.iterdir()):
                if not analysis_group_dir.is_dir() or analysis_group_dir.name.startswith("."):
                    continue
                for config_dir in sorted(analysis_group_dir.iterdir()):
                    if config_dir.is_dir() and not config_dir.name.startswith("."):
                        label = f"{analysis_group_dir.name} / {config_dir.name}"
                        entries.append((label, config_dir))

        dialog = FolderDeletionDialog(
            "Gestion des analyses",
            "Sélectionnez les dossiers de configurations à supprimer.",
            entries,
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_paths = dialog.selected_paths()
        if not selected_paths:
            return

        labels = [f"{path.parent.name} / {path.name}" for path in selected_paths]
        reply = QMessageBox.question(
            self,
            "Supprimer des analyses",
            "Supprimer les configurations sélectionnées ?\n\n" + "\n".join(labels),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted = 0
        errors = []
        for path in selected_paths:
            try:
                shutil.rmtree(path)
                deleted += 1
                parent = path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
            except Exception as exc:
                errors.append(f"{path.parent.name}/{path.name}: {exc}")

        self._show_deletion_summary("analyses", deleted, errors)

    def _show_deletion_summary(self, target_label: str, deleted: int, errors: list[str]):
        if errors:
            QMessageBox.warning(
                self,
                "Suppression partielle",
                f"{deleted} {target_label} supprimé(s).\n\nErreurs:\n" + "\n".join(errors)
            )
            return

        QMessageBox.information(
            self,
            "Suppression terminée",
            f"{deleted} {target_label} supprimé(s) avec succès."
        )
    
    # === SECTION 2: MODÈLES NLP ===
    
    def _build_models_section(self):
        """Section modèles NLP."""
        group = self.make_group("Modèles NLP")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Info sur les caches
        info_container = QWidget()
        info_container.setStyleSheet("background-color: transparent;")
        info_layout = QFormLayout(info_container)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(8)
        
        # Stanza
        self._lbl_stanza_cache = QLabel("Calcul en cours...")
        self._lbl_stanza_cache.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent;")
        info_layout.addRow(self._make_bold_label("Stanza:"), self._lbl_stanza_cache)
        
        # SpaCy
        self._lbl_spacy_cache = QLabel("Calcul en cours...")
        self._lbl_spacy_cache.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent;")
        info_layout.addRow(self._make_bold_label("SpaCy:"), self._lbl_spacy_cache)
        
        # Total
        self._lbl_total_cache = QLabel("Calcul en cours...")
        self._lbl_total_cache.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        self._lbl_total_cache.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        info_layout.addRow(self._make_bold_label("Total:"), self._lbl_total_cache)
        
        layout.addWidget(info_container)
        
        # Boutons d'action
        actions_container = QWidget()
        actions_container.setStyleSheet("background-color: transparent;")
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(8, 8, 8, 4)
        actions_layout.setSpacing(10)
        
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setFixedHeight(32)
        btn_refresh.setStyleSheet(self._button_style(ACCENT))
        btn_refresh.clicked.connect(self._refresh_cache_info)
        actions_layout.addWidget(btn_refresh)
        
        btn_clean = QPushButton("Nettoyer les caches")
        btn_clean.setFixedHeight(32)
        btn_clean.setStyleSheet(self._button_style("#8a3a3a"))
        btn_clean.clicked.connect(self._clean_model_caches)
        actions_layout.addWidget(btn_clean)
        
        actions_layout.addStretch()
        
        layout.addWidget(actions_container)
        
        return group
    
    def _make_bold_label(self, text: str) -> QLabel:
        """Crée un label en gras."""
        lbl = QLabel(text)
        lbl.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        return lbl
    
    def _button_style(self, bg_color: str) -> str:
        """Style pour les boutons."""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {bg_color}cc;
            }}
            QPushButton:pressed {{
                background-color: {bg_color}aa;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #888888;
            }}
        """
    def _refresh_cache_info(self):
        """Rafraîchit les informations sur les caches de modèles."""
        # Initialiser les tailles à 0
        stanza_size = 0
        spacy_size = 0
        
        # Stanza
        try:
            from stanza.resources.common import DEFAULT_MODEL_DIR
            stanza_dir = Path(DEFAULT_MODEL_DIR)
            stanza_size = self._get_dir_size(stanza_dir) if stanza_dir.exists() else 0
            self._lbl_stanza_cache.setText(
                f"{self._format_size(stanza_size)} — {stanza_dir}"
            )
        except Exception as e:
            self._lbl_stanza_cache.setText(f"Erreur: {e}")
        
        # SpaCy
        try:
            import spacy
            import site
            import sys
            # Dans SpaCy 3.x, les modèles sont des packages dans site-packages
            # Chercher les packages fr_*, en_*, etc.
            spacy_size = 0
            spacy_models = []
            
            # Obtenir tous les emplacements possibles de site-packages
            site_dirs = []
            
            # 1. site.getsitepackages() - emplacements standard
            try:
                site_dirs.extend(site.getsitepackages())
            except:
                pass
            
            # 2. site.getusersitepackages() - installation utilisateur
            try:
                user_site = site.getusersitepackages()
                if user_site:
                    site_dirs.append(user_site)
            except:
                pass
            
            # 3. sys.path - tous les chemins de recherche Python
            # Filtrer pour garder seulement les site-packages et dist-packages
            for path in sys.path:
                if ('site-packages' in path or 'dist-packages' in path) and path not in site_dirs:
                    site_dirs.append(path)
            
            # Chercher les modèles dans tous les emplacements
            checked_paths = set()  # Éviter les doublons
            for site_pkg in site_dirs:
                try:
                    site_pkg_path = Path(site_pkg)
                    if not site_pkg_path.exists() or str(site_pkg_path) in checked_paths:
                        continue
                    checked_paths.add(str(site_pkg_path))
                    
                    # Patterns de modèles SpaCy communs
                    for pattern in ['fr_*', 'en_*', 'de_*', 'es_*', 'it_*', 'pt_*', 'xx_*']:
                        for model_dir in site_pkg_path.glob(pattern):
                            if model_dir.is_dir() and model_dir.name not in spacy_models:
                                spacy_models.append(model_dir.name)
                                spacy_size += self._get_dir_size(model_dir)
                except:
                    continue
            
            # Affichage avec le premier chemin trouvé (le plus pertinent)
            primary_path = site_dirs[0] if site_dirs else 'site-packages'
            model_info = f" ({len(spacy_models)} modèle(s))" if spacy_models else " (aucun modèle)"
            locations_info = f" dans {len(checked_paths)} emplacement(s)" if len(checked_paths) > 1 else ""
            
            self._lbl_spacy_cache.setText(
                f"{self._format_size(spacy_size)}{model_info}{locations_info} — {primary_path}"
            )
        except Exception as e:
            self._lbl_spacy_cache.setText(f"Erreur: {e}")
        
        # Total
        total_size = stanza_size + spacy_size
        self._lbl_total_cache.setText(self._format_size(total_size))
    
    def _get_dir_size(self, path: Path) -> int:
        """Calcule la taille totale d'un dossier en octets."""
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except Exception:
            pass
        return total
    
    def _format_size(self, size: int) -> str:
        """Formate une taille en octets en unité lisible."""
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} To"
    
    def _clean_model_caches(self):
        """Nettoie les caches des modèles NLP."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir supprimer tous les caches de modèles NLP ?\n\n"
            "Les modèles seront retéléchargés automatiquement lors de la prochaine utilisation.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted = []
            errors = []
            
            # Stanza
            try:
                from stanza.resources.common import DEFAULT_MODEL_DIR
                stanza_dir = Path(DEFAULT_MODEL_DIR)
                if stanza_dir.exists():
                    shutil.rmtree(stanza_dir)
                    deleted.append("Stanza")
            except Exception as e:
                errors.append(f"Stanza: {e}")
            
            # SpaCy
            try:
                import spacy
                import site
                import sys
                # Dans SpaCy 3.x, les modèles sont des packages dans site-packages
                # Chercher dans tous les emplacements possibles
                site_dirs = []
                
                try:
                    site_dirs.extend(site.getsitepackages())
                except:
                    pass
                
                try:
                    user_site = site.getusersitepackages()
                    if user_site:
                        site_dirs.append(user_site)
                except:
                    pass
                
                for path in sys.path:
                    if ('site-packages' in path or 'dist-packages' in path) and path not in site_dirs:
                        site_dirs.append(path)
                
                deleted_count = 0
                for site_pkg in site_dirs:
                    try:
                        site_pkg_path = Path(site_pkg)
                        if not site_pkg_path.exists():
                            continue
                        
                        for pattern in ['fr_*', 'en_*', 'de_*', 'es_*', 'it_*', 'pt_*', 'xx_*']:
                            for model_dir in site_pkg_path.glob(pattern):
                                if model_dir.is_dir():
                                    shutil.rmtree(model_dir)
                                    deleted_count += 1
                    except:
                        continue
                
                if deleted_count > 0:
                    deleted.append(f"SpaCy ({deleted_count} modèle(s))")
                elif not site_dirs:
                    errors.append("SpaCy: impossible de localiser site-packages")
            except Exception as e:
                errors.append(f"SpaCy: {e}")
            
            # Afficher le résultat
            message = ""
            if deleted:
                message += f"Caches supprimés : {', '.join(deleted)}\n"
            if errors:
                message += f"\nErreurs :\n" + "\n".join(errors)
            
            if not message:
                message = "Aucun cache à supprimer."
            
            QMessageBox.information(self, "Nettoyage terminé", message)
            self._refresh_cache_info()
    
    # === SECTION 3: LOGS ===
    
    def _build_logs_section(self):
        """Section logs et diagnostic."""
        group = self.make_group("Logs et diagnostic")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Formulaire de paramètres
        form_container = QWidget()
        form_container.setStyleSheet("background-color: transparent;")
        form_layout = QFormLayout(form_container)
        form_layout.setContentsMargins(8, 4, 8, 4)
        form_layout.setSpacing(12)
        
        # Niveau de verbosité
        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["minimal", "normal", "détaillé", "debug"])
        self._log_level_combo.setCurrentText(self._settings.get("log_level", "normal"))
        self._log_level_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }
        """)
        form_layout.addRow(
            self._make_bold_label("Niveau de verbosité:"),
            self._log_level_combo
        )
        
        # Temps de conservation
        self._log_retention_spin = QSpinBox()
        self._log_retention_spin.setRange(1, 365)
        self._log_retention_spin.setValue(self._settings.get("log_retention_days", 30))
        self._log_retention_spin.setSuffix(" jours")
        self._log_retention_spin.setStyleSheet("""
            QSpinBox {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }
        """)
        form_layout.addRow(
            self._make_bold_label("Conservation des logs:"),
            self._log_retention_spin
        )

        layout.addWidget(form_container)
        
        # Bouton d'action
        actions_container = QWidget()
        actions_container.setStyleSheet("background-color: transparent;")
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(8, 8, 8, 4)
        actions_layout.setSpacing(10)
        
        btn_clean_logs = QPushButton("Nettoyer les anciens logs")
        btn_clean_logs.setFixedHeight(32)
        btn_clean_logs.setStyleSheet(self._button_style("#8a3a3a"))
        btn_clean_logs.clicked.connect(self._clean_old_logs)
        actions_layout.addWidget(btn_clean_logs)
        
        actions_layout.addStretch()
        
        layout.addWidget(actions_container)
        
        return group
    
    def _save_all_settings(self):
        """Sauvegarde tous les paramètres de l'application."""
        self._settings["log_level"] = self._log_level_combo.currentText()
        self._settings["log_retention_days"] = self._log_retention_spin.value()
        self._settings["closed_pattern_display_mode"] = self._closed_pattern_display_combo.currentData()
        self._settings["offer_prepared_archive_prompt"] = self._prepared_archive_prompt_checkbox.isChecked()
        
        if self._save_settings():
            QMessageBox.information(
                self,
                "Paramètres enregistrés",
                "Tous les paramètres ont été sauvegardés avec succès.\n\n"
                "Certains changements seront appliqués au prochain démarrage."
            )
    
    def _clean_old_logs(self):
        """Nettoie les logs selon le temps de conservation."""
        logs_dir = self._project_root / "logs"
        if not logs_dir.exists():
            QMessageBox.information(self, "Nettoyage", "Aucun log à nettoyer.")
            return
        
        retention_days = self._log_retention_spin.value()
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer les logs de plus de {retention_days} jours ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import time
            cutoff_time = time.time() - (retention_days * 86400)
            deleted_count = 0
            
            try:
                for log_file in logs_dir.rglob("*.log"):
                    if log_file.stat().st_mtime < cutoff_time:
                        log_file.unlink()
                        deleted_count += 1
                
                QMessageBox.information(
                    self,
                    "Nettoyage terminé",
                    f"{deleted_count} fichier(s) log supprimé(s)."
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    f"Erreur lors du nettoyage des logs:\n{e}"
                )
    
    # === SECTION 4: AVANCÉ ===
    
    def _build_advanced_section(self):
        """Section paramètres avancés."""
        group = self.make_group("Paramètres avancés")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)

        options_container = QWidget()
        options_container.setStyleSheet("background-color: transparent;")
        options_layout = QFormLayout(options_container)
        options_layout.setContentsMargins(8, 4, 8, 4)
        options_layout.setSpacing(12)

        self._closed_pattern_display_combo = QComboBox()
        self._closed_pattern_display_combo.addItem("Afficher le motif", "motif")
        self._closed_pattern_display_combo.addItem("Afficher les mots correspondants", "words")
        current_mode = self._settings.get("closed_pattern_display_mode", "motif")
        index = self._closed_pattern_display_combo.findData(current_mode)
        self._closed_pattern_display_combo.setCurrentIndex(index if index >= 0 else 0)
        self._closed_pattern_display_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }
        """)
        options_layout.addRow(
            self._make_bold_label("Concordancier, motifs :"),
            self._closed_pattern_display_combo
        )

        self._prepared_archive_prompt_checkbox = QCheckBox(
            "Proposer la création d'une archive préparée après la première analyse complète d'un corpus"
        )
        self._prepared_archive_prompt_checkbox.setChecked(
            bool(self._settings.get("offer_prepared_archive_prompt", True))
        )
        self._prepared_archive_prompt_checkbox.setStyleSheet("background-color: transparent;")
        options_layout.addRow(
            self._make_bold_label("Archive préparée :"),
            self._prepared_archive_prompt_checkbox
        )

        layout.addWidget(options_container)

        archive_actions = QWidget()
        archive_actions.setStyleSheet("background-color: transparent;")
        archive_layout = QHBoxLayout(archive_actions)
        archive_layout.setContentsMargins(8, 0, 8, 0)
        archive_layout.setSpacing(10)

        archive_help = QLabel(
            "Vous pouvez aussi créer manuellement un ZIP contenant Textes_tagged et underscore_fix depuis un dossier d'analyse."
        )
        archive_help.setWordWrap(True)
        archive_help.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent; font-size: 12px;")
        archive_layout.addWidget(archive_help, 1)

        btn_export_archive = QPushButton("Créer une archive préparée…")
        btn_export_archive.setFixedHeight(34)
        btn_export_archive.setStyleSheet(self._button_style("#2f6f5f"))
        btn_export_archive.clicked.connect(self._export_prepared_archive_from_analysis)
        archive_layout.addWidget(btn_export_archive)

        layout.addWidget(archive_actions)
        
        # Description
        desc = QLabel(
            "Cette section permet de réinitialiser complètement les paramètres de l'application.\n"
            "Attention : cette action est irréversible."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent; font-size: 12px; padding: 8px;")
        layout.addWidget(desc)
        
        # Bouton de réinitialisation
        btn_reset = QPushButton("Réinitialiser tous les paramètres")
        btn_reset.setFixedHeight(36)
        btn_reset.setStyleSheet(self._button_style("#aa2a2a"))
        btn_reset.clicked.connect(self._reset_all_settings)
        
        btn_container = QWidget()
        btn_container.setStyleSheet("background-color: transparent;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(8, 4, 8, 4)
        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        
        layout.addWidget(btn_container)
        
        return group
    
    def _reset_all_settings(self):
        """Réinitialise tous les paramètres de l'application."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir réinitialiser TOUS les paramètres ?\n\n"
            "Cette action supprimera :\n"
            "• Tous les profils de configuration\n"
            "• Les paramètres de l'application (logs, etc.)\n"
            "• L'historique des analyses\n\n"
            "Les corpus et résultats d'analyses seront préservés.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Double confirmation
            reply2 = QMessageBox.warning(
                self,
                "Dernière confirmation",
                "Cette action est irréversible. Continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply2 == QMessageBox.StandardButton.Yes:
                deleted = []
                errors = []
                
                # Supprimer les profils
                try:
                    profiles_dir = self._project_root / "profiles"
                    if profiles_dir.exists():
                        for profile_file in profiles_dir.glob("*.json"):
                            profile_file.unlink()
                        deleted.append("Profils de configuration")
                except Exception as e:
                    errors.append(f"Profils: {e}")
                
                # Supprimer app_settings.json
                try:
                    if self._settings_file.exists():
                        self._settings_file.unlink()
                        deleted.append("Paramètres de l'application")
                except Exception as e:
                    errors.append(f"Paramètres: {e}")
                
                # Supprimer l'historique
                try:
                    history_file = self._project_root / "logs" / "run_history.json"
                    if history_file.exists():
                        history_file.unlink()
                        deleted.append("Historique des analyses")
                except Exception as e:
                    errors.append(f"Historique: {e}")
                
                # Recharger les paramètres par défaut
                self._load_settings()
                self._log_level_combo.setCurrentText(self._settings.get("log_level", "normal"))
                self._log_retention_spin.setValue(self._settings.get("log_retention_days", 30))
                closed_pattern_mode = self._settings.get("closed_pattern_display_mode", "motif")
                index = self._closed_pattern_display_combo.findData(closed_pattern_mode)
                self._closed_pattern_display_combo.setCurrentIndex(index if index >= 0 else 0)
                self._prepared_archive_prompt_checkbox.setChecked(
                    bool(self._settings.get("offer_prepared_archive_prompt", True))
                )
                
                # Afficher le résultat
                message = ""
                if deleted:
                    message += "Éléments supprimés :\n• " + "\n• ".join(deleted)
                if errors:
                    message += "\n\nErreurs :\n• " + "\n• ".join(errors)
                
                if not message:
                    message = "Rien à réinitialiser."
                
                QMessageBox.information(
                    self,
                    "Réinitialisation terminée",
                    message + "\n\nL'application va redémarrer."
                )

    def _export_prepared_archive_from_analysis(self):
        analyses_root = self._project_root / "Data" / "analyses"
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier d'analyse source",
            str(analyses_root if analyses_root.exists() else self._project_root),
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not selected_dir:
            return

        analysis_root = Path(selected_dir)
        if not has_prepared_archive_content(analysis_root):
            QMessageBox.warning(
                self,
                "Archive impossible",
                "Le dossier sélectionné ne contient ni Textes_tagged ni underscore_fix.",
            )
            return

        selected_corpus = analysis_root.parent.name.replace("analyse_", "", 1) if analysis_root.parent else analysis_root.name
        default_path = default_archive_path(analysis_root, selected_corpus)
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'archive préparée",
            str(default_path),
            "Archives ZIP (*.zip)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not output_path:
            return

        try:
            result = create_prepared_archive(analysis_root, output_path)
            QMessageBox.information(
                self,
                "Archive créée",
                "Archive préparée créée avec succès.\n\n"
                f"Fichier : {result['output_path']}\n"
                f"Contenu : {', '.join(result['included_roots'])}\n"
                f"Fichiers ajoutés : {result['file_count']}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erreur d'export",
                f"Impossible de créer l'archive préparée :\n{exc}",
            )


class FolderDeletionDialog(QDialog):
    """Dialogue de sélection multiple de dossiers à supprimer."""

    def __init__(self, title: str, subtitle: str, entries: list[tuple[str, Path]], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(720, 520)
        self._entries = entries
        self._build_ui(subtitle)

    def _build_ui(self, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel(self.windowTitle())
        title.setFont(QFont("Helvetica Neue", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(subtitle_label)

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list.setStyleSheet("""
            QListWidget {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 4px;
            }
        """)

        if not self._entries:
            item = QListWidgetItem("Aucun dossier disponible.")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._list.addItem(item)
        else:
            for label, path in self._entries:
                item = QListWidgetItem(f"{label}\n{path}")
                item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                self._list.addItem(item)

        layout.addWidget(self._list, 1)

        actions = QHBoxLayout()
        actions.addStretch()

        btn_select_all = QPushButton("Tout sélectionner")
        btn_select_all.setFixedHeight(34)
        btn_select_all.clicked.connect(self._select_all)
        actions.addWidget(btn_select_all)

        layout.addLayout(actions)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFixedHeight(34)
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_delete = QPushButton("Supprimer la sélection")
        btn_delete.setFixedHeight(34)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #8a3a3a;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #a14646;
            }
            QPushButton:pressed {
                background-color: #6e2e2e;
            }
        """)
        btn_delete.clicked.connect(self.accept)
        buttons.addWidget(btn_delete)

        layout.addLayout(buttons)

    def selected_paths(self) -> list[Path]:
        selected = []
        for index in range(self._list.count()):
            item = self._list.item(index)
            raw_path = item.data(Qt.ItemDataRole.UserRole)
            if raw_path and item.checkState() == Qt.CheckState.Checked:
                selected.append(Path(raw_path))
        return selected

    def _select_all(self):
        """Coche tous les dossiers listés dans le dialogue."""
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)
