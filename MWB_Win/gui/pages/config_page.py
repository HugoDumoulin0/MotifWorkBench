"""
Page de configuration de l'analyse.
Paramètres simples: paramètres essentiels
Paramètres avancés: tous les paramètres
@jcharlesDS (2026)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QComboBox, QGroupBox,
    QScrollArea, QMessageBox, QInputDialog, QFrame, QDialog, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QLocale
from PyQt6.QtGui import QFont
from pathlib import Path

from gui.config.settings import DEFAULT_CONFIG, list_profiles, save_profile, load_profile, delete_profile
from gui.core.gpu_detect import detect_gpu
from gui.dialogs.metadata_wizard_dialog import MetadataWizardDialog

def _tooltip_label(text: str, tooltip: str) -> QLabel:
    """Label avec tooltip au passage de la souris."""
    label = QLabel(text)
    label.setToolTip(tooltip)
    label.setCursor(Qt.CursorShape.WhatsThisCursor)
    return label

class ConfigPage(QWidget):
    """
    Page de configuration complète de l'analyse.
    """
    
    config_applied = pyqtSignal(dict)  # Signal émis quand la configuration est appliquée
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loading = False  # Flag pour éviter les signaux pendant le chargement
        self._current_profile_name = "Défaut"
        # Charger le premier profil disponible ou DEFAULT_CONFIG
        try:
            profiles = list_profiles()
            if profiles:
                self._current_profile_name = profiles[0]
                self._config = load_profile(profiles[0])
            else:
                self._config = dict(DEFAULT_CONFIG)
        except Exception:
            self._config = dict(DEFAULT_CONFIG)
        
        self._check_icon_path = (Path(__file__).resolve().parent.parent / "assets" / "checkmark.svg").as_posix()
        # Détection GPU au démarrage
        self._gpu_available, self._gpu_description = detect_gpu()
        self._config = self._sanitize_config_for_environment(self._config)
        self._setup_ui()
        self._loading = True
        self._load_config_into_ui(self._config)
        self._loading = False
        # Configuration initiale considérée comme appliquée
        self.config_applied.emit(self._config)
        self._mark_as_applied()

    def _sanitize_config_for_environment(self, cfg: dict) -> dict:
        """Force les options incompatibles avec la machine courante."""
        sanitized = dict(cfg)
        if not self._gpu_available:
            sanitized["use_gpu"] = False
        return sanitized
    
    # =================================
    # Construction de l'UI
    # =================================
    
    def _setup_ui(self):
        self.setStyleSheet(self._page_style())

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        
        # Titre
        title = QLabel("Réglages")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2937; background: transparent;")
        root.addWidget(title)
        
        # Barre GPU
        self._gpu_label = QLabel()
        self._gpu_label.setStyleSheet("color: #4b5563; font-size: 12px; background: transparent;")
        self._refresh_gpu_label()
        root.addWidget(self._gpu_label)
        
        # Indicateur d'état de la configuration
        self._status_label = QLabel("✓ Configuration appliquée")
        self._status_label.setStyleSheet("""
            color: #2e7d32; 
            font-size: 13px; 
            font-weight: bold; 
            background: #e8f5e9; 
            padding: 6px 12px; 
            border-radius: 4px;
        """)
        root.addWidget(self._status_label)
        
        # Sélecteur de mode (simple/avancé)
        mode_bar = QHBoxLayout()
        self._btn_simple = QPushButton("Paramètres simples")
        self._btn_advanced = QPushButton("Paramètres avancés")
        for btn in (self._btn_simple, self._btn_advanced):
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(140)
            btn.setStyleSheet("""
                QPushButton { background:#2a2a3a;
                color:#aaaaaa; border:1px solid transparent; border-radius:6px; padding:6px 16px; font-weight:400; }
                QPushButton:checked { background:#3a3a5a;
                color:#ffffff; font-weight:400; border:1px solid #5a5a7f; }
                QPushButton:hover { background:#333355;
                color:#ffffff; }
            """)
        self._btn_simple.setChecked(True)
        self._btn_simple.clicked.connect(lambda: self._switch_mode("simple"))
        self._btn_advanced.clicked.connect(lambda: self._switch_mode("advanced"))
        mode_bar.addWidget(self._btn_simple)
        mode_bar.addWidget(self._btn_advanced)
        mode_bar.addStretch()
        root.addLayout(mode_bar)
        
        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333355;")
        root.addWidget(sep)
        
        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: #f7f8fc;")
        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: #f7f8fc;")
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setSpacing(16)
        scroll.setWidget(self._scroll_content)
        root.addWidget(scroll, 1)
        
        # Construction des panneaux
        self._build_simple_panel()
        self._build_advanced_panel()
        self._advanced_panel.hide()  # Par défaut, on affiche le mode simple
        
        # Barre de profils + bouton de lancement
        bottom_bar = QHBoxLayout()
        
        self._profile_combo = QComboBox()
        self._profile_combo.setMinimumWidth(160)
        self._profile_combo.setStyleSheet(
            "background:#2a2a3a; color:#ffffff; border:none; border-radius:4px; padding:4px;"
        )
        self._refresh_profile_list()
        
        btn_load = QPushButton("Charger")
        btn_save = QPushButton("Sauvegarder")
        btn_delete = QPushButton("Supprimer")
        for btn in (btn_load, btn_save, btn_delete):
            btn.setMinimumHeight(34)
            btn.setStyleSheet("background:#2a2a3a; color:#cccccc; border:none; border-radius:6px; padding:4px 14px;")
        btn_delete.setStyleSheet("background:#3a1a1a; color:#ff8888; border:none; border-radius:6px; padding:4px 14px;")

        btn_load.clicked.connect(self._on_load_profile)
        btn_save.clicked.connect(self._on_save_profile)
        btn_delete.clicked.connect(self._on_delete_profile)

        profile_label = QLabel("Profil :")
        profile_label.setStyleSheet("background: transparent;")
        bottom_bar.addWidget(profile_label)
        bottom_bar.addWidget(self._profile_combo)
        bottom_bar.addWidget(btn_load)
        bottom_bar.addWidget(btn_save)
        bottom_bar.addWidget(btn_delete)
        bottom_bar.addStretch()
        
        btn_apply = QPushButton("Appliquer la configuration")
        btn_apply.setMinimumHeight(38)
        btn_apply.setStyleSheet("""
            QPushButton { background:#4a4a8a; color:#ffffff; border:none; border-radius:8px; padding:6px 24px; font-weight:bold; }
            QPushButton:hover { background:#5a5aaa; }
        """)
        btn_apply.clicked.connect(self._on_apply)
        bottom_bar.addWidget(btn_apply)

        root.addLayout(bottom_bar)
        
        # Connecter les signaux de changement APRÈS la construction de l'UI
        self._connect_change_signals()

    # ================================
    # Panneau de configuration simple
    # ================================

    def _build_simple_panel(self):
        self._simple_panel = QWidget()
        layout = QVBoxLayout(self._simple_panel)
        layout.setSpacing(12)
        
        # ÉTAPE 5 : Mettre "Corpus et métadonnées" en premier
        # Métadonnées
        grp_meta = QGroupBox("Corpus et métadonnées")
        grp_meta.setStyleSheet(self._group_style())
        form_meta = QFormLayout(grp_meta)

        # ÉTAPE 6 : Créer le label de résumé AVANT de remplir la liste
        self._corpus_summary_label = QLabel("Sélectionnez un corpus pour voir les détails.")
        self._corpus_summary_label.setStyleSheet("color: #6b7280; font-style: italic; font-size: 9pt; padding-left: 4px;")
        self._corpus_summary_label.setWordWrap(True)

        self._w_input_mode = QComboBox()
        self._w_input_mode.addItems([
            "Corpus brut (.txt)",
            "Corpus annoté (.conllu)",
            "Archive préparée (.zip)",
        ])
        self._w_input_mode.setToolTip(
            "Choisissez si l'analyse part de textes bruts, de fichiers CoNLL-U déjà annotés "
            "ou d'une archive ZIP contenant les fichiers préparés."
        )
        self._w_input_mode.currentIndexChanged.connect(self._update_input_mode_state)
        form_meta.addRow(_tooltip_label("Type d'entrée :", "Mode d'entrée pour l'analyse."), self._w_input_mode)

        # Sélecteur de corpus avec dropdown
        corpus_row = QHBoxLayout()
        self._w_corpus_selector = QComboBox()
        self._w_corpus_selector.setMinimumWidth(250)
        self._w_corpus_selector.setToolTip("Sélectionnez le corpus à analyser. Chaque corpus contient des textes .txt et un metadata.tsv.")
        self._refresh_corpus_list()  # Remplir la liste
        corpus_row.addWidget(self._w_corpus_selector)
        
        btn_refresh_corpus = QPushButton("⟳")
        btn_refresh_corpus.setFixedSize(34, 34)
        btn_refresh_corpus.setToolTip("Rafraîchir la liste des corpus")
        btn_refresh_corpus.setStyleSheet("background:#2a2a3a; color:#ffffff; border:none; border-radius:6px; font-size:16px;")
        btn_refresh_corpus.clicked.connect(self._refresh_corpus_list)
        corpus_row.addWidget(btn_refresh_corpus)
        corpus_row.addStretch()
        
        # Renommer en "Corpus à analyser"
        form_meta.addRow(
            _tooltip_label("Corpus à analyser :", "Dossier du corpus contenant les fichiers .txt et metadata.tsv."),
            corpus_row
        )
        
        # Afficher le résumé du corpus
        form_meta.addRow("", self._corpus_summary_label)
        
        # Connecter le changement de corpus pour mettre à jour le résumé
        self._w_corpus_selector.currentTextChanged.connect(self._update_corpus_summary)

        annotated_row = QHBoxLayout()
        self._w_annotated_corpus_path = QLineEdit()
        self._w_annotated_corpus_path.setPlaceholderText("Dossier contenant les fichiers .conllu")
        self._w_annotated_corpus_path.setToolTip("Sélectionnez un dossier de fichiers CoNLL-U déjà annotés.")
        self._w_annotated_corpus_path.textChanged.connect(lambda _text: self._update_corpus_summary(self._w_corpus_selector.currentText()))
        annotated_row.addWidget(self._w_annotated_corpus_path)

        self._btn_browse_annotated = QPushButton("Parcourir…")
        self._btn_browse_annotated.setMinimumHeight(34)
        self._btn_browse_annotated.setStyleSheet(
            "background:#2a2a3a; color:#ffffff; border:none; border-radius:6px; padding:4px 14px;"
        )
        self._btn_browse_annotated.clicked.connect(self._browse_annotated_corpus)
        annotated_row.addWidget(self._btn_browse_annotated)
        form_meta.addRow(
            _tooltip_label("Dossier annoté :", "Dossier source de fichiers .conllu pour sauter l'annotation."),
            annotated_row
        )

        prepared_zip_row = QHBoxLayout()
        self._w_prepared_zip_path = QLineEdit()
        self._w_prepared_zip_path.setPlaceholderText("Archive ZIP contenant Textes_tagged et/ou underscore_fix")
        self._w_prepared_zip_path.setToolTip(
            "Sélectionnez une archive ZIP contenant des fichiers CoNLL-U déjà préparés."
        )
        self._w_prepared_zip_path.textChanged.connect(
            lambda _text: self._update_corpus_summary(self._w_corpus_selector.currentText())
        )
        prepared_zip_row.addWidget(self._w_prepared_zip_path)

        self._btn_browse_prepared_zip = QPushButton("Parcourir…")
        self._btn_browse_prepared_zip.setMinimumHeight(34)
        self._btn_browse_prepared_zip.setStyleSheet(
            "background:#2a2a3a; color:#ffffff; border:none; border-radius:6px; padding:4px 14px;"
        )
        self._btn_browse_prepared_zip.clicked.connect(self._browse_prepared_zip)
        prepared_zip_row.addWidget(self._btn_browse_prepared_zip)
        form_meta.addRow(
            _tooltip_label("Archive préparée :", "ZIP de démonstration pour sauter l'annotation, et éventuellement underscore_fix."),
            prepared_zip_row
        )

        self._w_list_metadata = QLineEdit()
        self._w_list_metadata.setPlaceholderText("id, genre, word_count, sentence_count…")
        self._w_list_metadata.setToolTip("Colonnes du metadata.tsv à utiliser pour les analyses. Séparées par des virgules.")
        form_meta.addRow(_tooltip_label("Partitions :", "Colonnes à utiliser pour regrouper les textes."), self._w_list_metadata)
        
        self._btn_metadata_wizard = QPushButton("Ouvrir l'assistant de métadonnées")
        self._btn_metadata_wizard.setMinimumHeight(34)
        self._btn_metadata_wizard.setStyleSheet(
            "background:#2a2a3a; color:#ffffff; border:none; border-radius:6px; padding:4px 14px;"
        )
        self._btn_metadata_wizard.clicked.connect(self._open_metadata_wizard)
        form_meta.addRow("", self._btn_metadata_wizard)

        layout.addWidget(grp_meta)
        
        # Langue et annotation
        grp_lang = QGroupBox("Langue et annotation")
        grp_lang.setStyleSheet(self._group_style())
        form_lang = QFormLayout(grp_lang)
        
        # Outil d'annotation
        self._w_annotator_tool = QComboBox()
        self._w_annotator_tool.addItems([
            "spaCy",
            "Stanza",
        ])
        self._w_annotator_tool.setToolTip(
            "Outil d'annotation morphosyntaxique :\n"
            "• spaCy : Adaptatif - Transformer (GPU) ou Large (CPU optimisé)\n"
            "• Stanza : Précision maximale mais plus lent"
        )
        self._w_annotator_tool.currentIndexChanged.connect(self._on_annotator_tool_changed)
        form_lang.addRow(_tooltip_label("Outil :", "Outil d'annotation à utiliser."), self._w_annotator_tool)
        
        # Langue
        self._w_language = QComboBox()
        self._w_language.setEditable(True)
        self._w_language.addItems(["fr", "en", "de", "es", "it", "pt"])
        self._w_language.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._w_language.setToolTip(
            "Code langue du corpus pour l'annotation morphosyntaxique "
            "(ex: fr, en, de, es)."
        )
        if self._w_language.lineEdit():
            self._w_language.lineEdit().setPlaceholderText("Code ISO langue, ex: fr")
        form_lang.addRow(_tooltip_label("Langue :", "Langue du corpus (modèles à utiliser)."), self._w_language)

        # Option GPU : affichage adaptatif selon disponibilité ET outil choisi
        self._w_gpu_row_label = _tooltip_label("Accélération :", "Utiliser GPU ou CPU pour l'annotation.")
        if self._gpu_available:
            # GPU détecté : proposer un choix (désactivable selon l'outil)
            self._w_gpu_choice = QComboBox()
            self._w_gpu_choice.addItems(["GPU", "CPU"])
            self._w_gpu_choice.setToolTip(f"GPU détecté : {self._gpu_description}")
            self._w_gpu_row = form_lang.addRow(self._w_gpu_row_label, self._w_gpu_choice)
            self._w_gpu_info_label = None
        else:
            # Pas de GPU : CPU uniquement
            self._w_gpu_choice = None
            self._w_gpu_info_label = QLabel(f"CPU uniquement ({self._gpu_description})")
            self._w_gpu_info_label.setStyleSheet("color: #6b7280; font-style: italic;")
            self._w_gpu_row = form_lang.addRow(self._w_gpu_row_label, self._w_gpu_info_label)

        self._w_accel_warning = QLabel(
            "Le CPU peut parfois être plus rapide que le GPU selon le PC, "
            "l'outil d'annotation et la taille du corpus."
        )
        self._w_accel_warning.setWordWrap(True)
        self._w_accel_warning.setStyleSheet(
            "color: #6b7280; font-style: italic; font-size: 9pt; "
            "padding-left: 4px; padding-top: 2px;"
        )
        form_lang.addRow("", self._w_accel_warning)
        
        # Mettre à jour l'état GPU selon l'outil par défaut
        self._update_gpu_availability()
        
        layout.addWidget(grp_lang)

        # Motifs
        grp_motifs = QGroupBox("Paramètres des motifs (CloSPEC)")
        grp_motifs.setStyleSheet(self._group_style())
        form_motifs = QFormLayout(grp_motifs)

        self._w_minsup = QDoubleSpinBox()
        self._w_minsup.setLocale(QLocale.c())
        self._w_minsup.setDecimals(1)
        self._w_minsup.setRange(0.1, 100.0)
        self._w_minsup.setSingleStep(0.1)
        self._w_minsup.setSuffix(" %")
        self._w_minsup.setToolTip("Support minimal des motifs en pourcentage. Les valeurs décimales sont autorisées (ex. 0.1).")
        self._w_minsup.setToolTip("Fréquence minimale (en % des séquences) pour qu'un motif soit retenu.")
        form_motifs.addRow(_tooltip_label("Support minimal :", "% de textes dans lesquels un motif doit apparaître."), self._w_minsup)

        self._w_itemset_min = QSpinBox()
        self._w_itemset_min.setRange(1, 20)
        self._w_itemset_min.setToolTip("Nombre minimal d'itemsets (informations) que doit contenir un motif.")
        form_motifs.addRow(_tooltip_label("Itemsets min. :", "Longueur minimale des motifs extraits."), self._w_itemset_min)

        layout.addWidget(grp_motifs)

        # Attributs linguistiques
        grp_attrs = QGroupBox("Attributs linguistiques à utiliser")
        grp_attrs.setStyleSheet(self._group_style())
        form_attrs = QFormLayout(grp_attrs)

        self._w_Lemma = QCheckBox("Lemmes")
        self._w_Pos   = QCheckBox("POS (catégories grammaticales)")
        self._w_Dep   = QCheckBox("Dépendances syntaxiques")
        self._w_Form  = QCheckBox("Formes (mots exacts)")
        self._w_Feats = QCheckBox("Traits morphologiques")

        self._w_Lemma.setToolTip("Inclure les lemmes dans la représentation des motifs.")
        self._w_Pos.setToolTip("Inclure les étiquettes POS (NOUN, VERB, ADJ…).")
        self._w_Dep.setToolTip("Inclure les relations de dépendance syntaxique (nsubj, obj…).")
        self._w_Form.setToolTip("Inclure les formes brutes (attention : produit beaucoup plus de motifs).")
        self._w_Feats.setToolTip("Inclure les traits morphologiques (genre, nombre, temps…).")

        for w in (self._w_Lemma, self._w_Pos, self._w_Dep, self._w_Form, self._w_Feats):
            form_attrs.addRow("", w)
        layout.addWidget(grp_attrs)

        layout.addStretch()

        self._scroll_layout.addWidget(self._simple_panel)
    
    # ==================================
    # Panneau de configuration avancée
    # ==================================
    
    def _build_advanced_panel(self):
        self._advanced_panel = QWidget()
        layout = QVBoxLayout(self._advanced_panel)
        layout.setSpacing(12)

        # Stanza
        # Note: Le téléchargement des modèles est maintenant automatique
        # (détection et téléchargement uniquement si nécessaire)

        # Early selection
        self._grp_early = QGroupBox("Early Selection (pré-filtrage des lemmes)")
        self._grp_early.setStyleSheet(self._group_style())
        form_early = QFormLayout(self._grp_early)

        self._w_earlySelection = QCheckBox("Activer l'early selection")
        self._w_earlySelection.setToolTip("Restreint les lemmes candidats avant la fouille pour accélérer l'extraction.")
        self._w_earlySelection.toggled.connect(self._update_early_selection_state)
        form_early.addRow("", self._w_earlySelection)

        self._w_seuil_early = QSpinBox()
        self._w_seuil_early.setRange(1, 10000)
        self._w_seuil_early.setToolTip("Nombre maximum de lemmes retenus pour l'early selection.")
        form_early.addRow(_tooltip_label("Seuil early selection :", "Top-N lemmes les plus fréquents à conserver."), self._w_seuil_early)

        self._w_filter_specifs = QCheckBox("Filtrer par spécificités")
        self._w_filter_specifs.setToolTip("Restreindre l'early selection aux lemmes spécifiques d'une partition.")
        form_early.addRow("", self._w_filter_specifs)

        self._w_partition_cible = QLineEdit()
        self._w_partition_cible.setToolTip("Nom de la partition cible pour le filtrage par spécificités.")
        form_early.addRow(_tooltip_label("Partition cible :", "Valeur de la métadonnée cible pour filtrer les spécificités."), self._w_partition_cible)

        self._w_seuil_banalite = QSpinBox()
        self._w_seuil_banalite.setRange(0, 100)
        self._w_seuil_banalite.setToolTip("Seuil de banalité : lemmes présents dans plus de N partitions sont exclus.")
        form_early.addRow(_tooltip_label("Seuil de banalité :", "Exclure les lemmes trop banals (présents dans trop de partitions)."), self._w_seuil_banalite)

        self._w_early_pos4lemma = QLineEdit()
        self._w_early_pos4lemma.setToolTip("Filtrer les lemmes par POS (ex: ADJ|NOUN|VERB). Laisser vide pour tout.")
        form_early.addRow(_tooltip_label("POS pour early sel. :", "Restreindre l'early selection à ces POS."), self._w_early_pos4lemma)

        self._w_user_input_list = QCheckBox("Utiliser une liste de lemmes manuelle")
        self._w_user_input_list.setToolTip("Utiliser une liste de lemmes fournie manuellement au lieu de l'early selection automatique.")
        self._w_user_input_list.toggled.connect(self._update_manual_lemma_list_state)
        form_early.addRow("", self._w_user_input_list)

        self._w_liste_earlyselection = QLineEdit()
        self._w_liste_earlyselection.setPlaceholderText("président, comité, formation…")
        self._w_liste_earlyselection.setToolTip("Liste de lemmes à utiliser (séparés par des virgules).")
        form_early.addRow(_tooltip_label("Lemmes :", "Liste manuelle de lemmes à cibler."), self._w_liste_earlyselection)

        layout.addWidget(self._grp_early)
        self._update_early_selection_state(self._w_earlySelection.isChecked())

        # Clustering interne
        grp_clust = QGroupBox("Clustering interne")
        grp_clust.setStyleSheet(self._group_style())
        form_clust = QFormLayout(grp_clust)

        self._w_internal_clustering = QCheckBox("Activer le clustering interne des motifs")
        self._w_internal_clustering.setToolTip("Regroupe les motifs similaires après extraction. Recommandé.")
        form_clust.addRow("", self._w_internal_clustering)
        layout.addWidget(grp_clust)

        # Paramètres avancés des motifs
        grp_motifs_adv = QGroupBox("Paramètres avancés des motifs (CloSPEC)")
        grp_motifs_adv.setStyleSheet(self._group_style())
        form_motifs_adv = QFormLayout(grp_motifs_adv)

        self._w_gap_min = QSpinBox()
        self._w_gap_min.setRange(0, 100)
        self._w_gap_min.setToolTip("Gap minimum entre deux itemsets consécutifs d'un motif.")
        form_motifs_adv.addRow(_tooltip_label("Gap min :", "Imposer une discontinuité dans le motif."), self._w_gap_min)

        self._w_gap_max = QSpinBox()
        self._w_gap_max.setRange(0, 100)
        self._w_gap_max.setToolTip("Gap maximum entre deux itemsets consécutifs d'un motif.")
        form_motifs_adv.addRow(_tooltip_label("Gap max :", "Autoriser une discontinuité dans le motif."), self._w_gap_max)

        self._w_threads = QSpinBox()
        self._w_threads.setRange(1, 128)
        self._w_threads.setToolTip("Nombre de threads parallèles pour la fouille BideSpanTree.")
        form_motifs_adv.addRow(_tooltip_label("Threads :", "Nombre de cœurs CPU alloués à la fouille de motifs."), self._w_threads)

        layout.addWidget(grp_motifs_adv)

        # Comparaison & Statistiques
        grp_stats = QGroupBox("Comparaison && Statistiques")
        grp_stats.setStyleSheet(self._group_style())
        form_stats = QFormLayout(grp_stats)

        self._w_specifs = QCheckBox("Calculer les spécificités")
        self._w_specifs.setToolTip("Calcule les scores de spécificité hypergéométrique des motifs par partition.")
        form_stats.addRow("", self._w_specifs)

        self._w_liste_seuils_lemma = QLineEdit()
        self._w_liste_seuils_lemma.setPlaceholderText("100, 200")
        self._w_liste_seuils_lemma.setToolTip("Seuils de fréquence pour la comparaison par lemmes (séparés par des virgules).")
        form_stats.addRow(_tooltip_label("Seuils lemmes :", "Top-N lemmes à inclure dans l'AFC comparative."), self._w_liste_seuils_lemma)

        self._w_downhill_pos4lemma = QLineEdit()
        self._w_downhill_pos4lemma.setToolTip("Restreindre la comparaison lemmes à ces POS (ex: ADJ|ADV|NOUN|VERB).")
        form_stats.addRow(_tooltip_label("POS pour lemmes :", "Restreindre les lemmes comparatifs à ces POS."), self._w_downhill_pos4lemma)

        self._w_liste_seuils_bigrams = QLineEdit()
        self._w_liste_seuils_bigrams.setPlaceholderText("100")
        self._w_liste_seuils_bigrams.setToolTip("Seuils de fréquence pour la comparaison par bigrammes.")
        form_stats.addRow(_tooltip_label("Seuils bigrammes :", "Top-N bigrammes à inclure dans l'analyse comparative."), self._w_liste_seuils_bigrams)

        layout.addWidget(grp_stats)
        layout.addStretch()

        self._scroll_layout.addWidget(self._advanced_panel)
    
    # ===============================================
    # Navigation entre les modes simple/avancé
    # ===============================================
    
    def _switch_mode(self, mode: str):
        self._btn_simple.setChecked(mode == "simple")
        self._btn_advanced.setChecked(mode == "advanced")
        self._simple_panel.setVisible(mode == "simple")
        self._advanced_panel.setVisible(mode == "advanced")
    
    def _refresh_corpus_list(self):
        """Charge la liste des corpus disponibles dans Data/Corpus/."""
        
        self._w_corpus_selector.clear()
        
        corpus_base = Path(__file__).resolve().parents[2] / "Data" / "Corpus"
        
        # Lister les sous-dossiers existants
        corpus_list = []
        if corpus_base.exists():
            for item in corpus_base.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    # Vérifier qu'il contient bien des fichiers .txt
                    txt_files = list(item.glob("*.txt"))
                    if txt_files:
                        # Afficher uniquement le nom du dossier, pas le chemin complet
                        corpus_list.append(item.name)
        
        # Ajouter le dernier corpus utilisé si disponible
        project_root = Path(__file__).resolve().parents[2]
        last_analysis_path = project_root / "logs" / "last_analysis.json"
        last_corpus = None
        if last_analysis_path.exists():
            try:
                import json
                with open(last_analysis_path) as f:
                    config = json.load(f)
                    # Extraire le nom du corpus depuis path_corpus ou path_metadata
                    path_corpus = config.get("path_corpus", "")
                    if path_corpus:
                        last_corpus = Path(path_corpus).name
                    else:
                        path_metadata = config.get("path_metadata", "")
                        if path_metadata:
                            last_corpus = Path(path_metadata).parent.name
                        else:
                            last_corpus = None
                    
                    if last_corpus and last_corpus not in corpus_list:
                        corpus_list.insert(0, last_corpus)  # Mettre en premier
            except:
                pass
        
        if not corpus_list:
            # Aucun corpus détecté : ajouter un placeholder
            self._w_corpus_selector.addItem("[Aucun corpus détecté - créez Data/Corpus/mon_corpus/]")
            self._w_corpus_selector.setEnabled(False)
        else:
            corpus_list.sort()
            self._w_corpus_selector.addItems(corpus_list)
            self._w_corpus_selector.setEnabled(True)
        
        # Mettre à jour le résumé si un corpus est déjà sélectionné
        if self._w_corpus_selector.currentText():
            self._update_corpus_summary(self._w_corpus_selector.currentText())
    
    def _update_corpus_summary(self, corpus_name: str):
        """Affiche un résumé du corpus : nb fichiers, présence metadata, date modif."""
        if not corpus_name or corpus_name.startswith("["):
            self._corpus_summary_label.setText("Sélectionnez un corpus pour voir les détails.")
            return
        
        # Reconstruire le chemin complet depuis le nom
        corpus_path = self._get_corpus_path_from_name(corpus_name)
        if not corpus_path:
            self._corpus_summary_label.setText("⚠ Corpus non sélectionné")
            return
        
        corpus_dir = Path(corpus_path)
        if not corpus_dir.exists():
            self._corpus_summary_label.setText("Chemin invalide")
            return

        input_mode = self._get_input_mode()
        if input_mode == "annotated_conllu":
            annotated_dir = Path(self._w_annotated_corpus_path.text().strip())
            if not annotated_dir.exists():
                self._corpus_summary_label.setText("⚠ Dossier annoté non sélectionné ou invalide")
                return
            conllu_files = list(annotated_dir.glob("*.conllu"))
            nb_files = len(conllu_files)
            metadata_file = corpus_dir / "metadata.tsv"
            has_metadata = metadata_file.exists()
            metadata_str = "✓ metadata.tsv présent" if has_metadata else "metadata.tsv absent"
            import datetime
            mtime = annotated_dir.stat().st_mtime
            last_modified = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
            summary = f"{nb_files} fichier(s) .conllu  •  {metadata_str}  •  Modifié: {last_modified}"
            self._corpus_summary_label.setText(summary)
            return

        if input_mode == "prepared_conllu_zip":
            archive_path = Path(self._w_prepared_zip_path.text().strip())
            if not archive_path.exists() or not archive_path.is_file():
                self._corpus_summary_label.setText("⚠ Archive ZIP non sélectionnée ou invalide")
                return
            try:
                import zipfile
                with zipfile.ZipFile(archive_path) as archive:
                    members = [
                        name for name in archive.namelist()
                        if not name.endswith("/") and name.lower().endswith(".conllu")
                    ]
                    has_underscore_fix = any(
                        "underscore_fix/" in name.replace("\\", "/").lower()
                        for name in members
                    )
            except Exception:
                self._corpus_summary_label.setText("⚠ Archive ZIP illisible")
                return

            nb_files = len(members)
            metadata_file = corpus_dir / "metadata.tsv"
            has_metadata = metadata_file.exists()
            metadata_str = "✓ metadata.tsv présent" if has_metadata else "metadata.tsv absent"
            fix_str = "underscore_fix inclus" if has_underscore_fix else "underscore_fix à recalculer"
            import datetime
            mtime = archive_path.stat().st_mtime
            last_modified = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
            summary = f"{nb_files} fichier(s) .conllu  •  {metadata_str}  •  {fix_str}  •  Modifié: {last_modified}"
            self._corpus_summary_label.setText(summary)
            return

        txt_files = list(corpus_dir.glob("*.txt"))
        nb_files = len(txt_files)

        metadata_file = corpus_dir / "metadata.tsv"
        has_metadata = metadata_file.exists()
        metadata_str = "✓ metadata.tsv présent" if has_metadata else "metadata.tsv absent"
        
        # Date de dernière modification (du dossier ou du metadata)
        import datetime
        if has_metadata:
            mtime = metadata_file.stat().st_mtime
        else:
            mtime = corpus_dir.stat().st_mtime
        last_modified = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        
        summary = f"{nb_files} fichier(s) .txt  •  {metadata_str}  •  Modifié: {last_modified}"
        self._corpus_summary_label.setText(summary)
    
    def _get_corpus_path_from_name(self, corpus_name: str) -> str:
        """Convertit le nom du corpus en chemin complet."""
        if not corpus_name or corpus_name.startswith("["):
            return ""
        
        # Si c'est déjà un chemin complet, le retourner tel quel (rétrocompatibilité)
        if corpus_name.startswith("./") or corpus_name.startswith("/"):
            return corpus_name
        
        # Sinon, construire le chemin
        return f"./Data/Corpus/{corpus_name}"

    def _get_input_mode(self) -> str:
        if not hasattr(self, "_w_input_mode"):
            return "raw"
        index = self._w_input_mode.currentIndex()
        if index == 1:
            return "annotated_conllu"
        if index == 2:
            return "prepared_conllu_zip"
        return "raw"

    def _browse_annotated_corpus(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner un dossier de fichiers .conllu",
            self._w_annotated_corpus_path.text().strip() or str(Path.cwd())
        )
        if folder:
            self._w_annotated_corpus_path.setText(folder)

    def _browse_prepared_zip(self):
        archive_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une archive ZIP préparée",
            self._w_prepared_zip_path.text().strip() or str(Path.cwd()),
            "Archives ZIP (*.zip)"
        )
        if archive_path:
            self._w_prepared_zip_path.setText(archive_path)

    def _update_input_mode_state(self, *_args):
        input_mode = self._get_input_mode()
        is_annotated = input_mode == "annotated_conllu"
        is_prepared_zip = input_mode == "prepared_conllu_zip"
        if hasattr(self, "_w_annotated_corpus_path"):
            self._w_annotated_corpus_path.setEnabled(is_annotated)
        if hasattr(self, "_btn_browse_annotated"):
            self._btn_browse_annotated.setEnabled(is_annotated)
        if hasattr(self, "_w_prepared_zip_path"):
            self._w_prepared_zip_path.setEnabled(is_prepared_zip)
        if hasattr(self, "_btn_browse_prepared_zip"):
            self._btn_browse_prepared_zip.setEnabled(is_prepared_zip)
        if hasattr(self, "_w_annotator_tool"):
            self._w_annotator_tool.setEnabled(input_mode == "raw")
        if hasattr(self, "_w_gpu_row_label"):
            self._w_gpu_row_label.setEnabled(input_mode == "raw")
        if hasattr(self, "_w_gpu_choice") and self._w_gpu_choice:
            self._w_gpu_choice.setEnabled(input_mode == "raw")
        if hasattr(self, "_w_gpu_info_label") and self._w_gpu_info_label:
            self._w_gpu_info_label.setEnabled(input_mode == "raw")
        if hasattr(self, "_w_accel_warning"):
            self._w_accel_warning.setEnabled(input_mode == "raw")
        if hasattr(self, "_w_corpus_selector"):
            self._update_corpus_summary(self._w_corpus_selector.currentText())

    def _build_analysis_name_from_corpus_name(self, corpus_name: str) -> str:
        """Construit automatiquement le nom du dossier d'analyse à partir du corpus."""
        if not corpus_name or corpus_name.startswith("["):
            return ""

        normalized_name = Path(corpus_name).name.strip()
        return f"analyse_{normalized_name}" if normalized_name else ""
    
    def _on_annotator_tool_changed(self, index: int):
        """
        Appelé quand l'utilisateur change l'outil d'annotation.
        Met à jour la disponibilité du GPU selon l'outil choisi.
        """
        self._update_gpu_availability()
    
    def _update_gpu_availability(self):
        """
        Met à jour l'affichage de l'option GPU selon l'outil sélectionné.
        Les outils CPU-only désactivent l'option GPU.
        """
        # Importer le factory pour vérifier les capacités GPU
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
        try:
            from annotators import get_annotator
            
            # Extraire le nom de l'outil depuis le texte du dropdown
            annotator_text = self._w_annotator_tool.currentText()
            if "spaCy" in annotator_text:
                annotator_tool = "spacy"
            elif "Stanza" in annotator_text:
                annotator_tool = "stanza"
            else:
                annotator_tool = "spacy"
            
            # Vérifier si l'outil supporte le GPU
            try:
                annotator = get_annotator(annotator_tool)
                tool_supports_gpu = annotator.supports_gpu()
            except:
                tool_supports_gpu = True  # Par défaut, supposer que oui
            
            # Mettre à jour l'UI
            if self._gpu_available and self._w_gpu_choice is not None:
                if tool_supports_gpu:
                    # Outil supporte GPU : activer le choix
                    self._w_gpu_choice.setEnabled(True)
                    self._w_gpu_choice.setToolTip(f"GPU détecté : {self._gpu_description}")
                else:
                    # Outil ne supporte pas GPU : forcer CPU et désactiver
                    self._w_gpu_choice.setCurrentText("CPU")
                    self._w_gpu_choice.setEnabled(False)
                    self._w_gpu_choice.setToolTip(f"{annotator.get_name()} ne supporte pas l'accélération GPU (CPU uniquement)")
            elif self._w_gpu_info_label is not None:
                # Pas de GPU matériel : juste mettre à jour le message
                if tool_supports_gpu:
                    self._w_gpu_info_label.setText(f"CPU uniquement ({self._gpu_description})")
                else:
                    try:
                        annotator_name = get_annotator(annotator_tool).get_name()
                        self._w_gpu_info_label.setText(f"CPU uniquement ({annotator_name} ne supporte pas le GPU)")
                    except:
                        self._w_gpu_info_label.setText(f"CPU uniquement ({self._gpu_description})")
        except ImportError:
            # Annotateurs pas encore installés, ignorer
            pass
        finally:
            sys.path.pop(0)

    def _update_early_selection_state(self, enabled: bool):
        """Grise et désactive les paramètres d'early selection quand l'option est décochée."""
        widgets = [
            self._w_seuil_early,
            self._w_filter_specifs,
            self._w_partition_cible,
            self._w_seuil_banalite,
            self._w_early_pos4lemma,
        ]

        for widget in widgets:
            widget.setEnabled(enabled)

        self._w_user_input_list.setEnabled(True)
        self._update_manual_lemma_list_state(self._w_user_input_list.isChecked())

    def _update_manual_lemma_list_state(self, enabled: bool):
        """Active la saisie des lemmes manuels indépendamment de l'early selection."""
        self._w_liste_earlyselection.setEnabled(enabled)
    
    # ========================================================
    # Chargement et lecture de la configuration dans l'UI
    # ========================================================
    
    def _load_config_into_ui(self, cfg: dict):
        """Remplit tous les widgets avec les valeurs de configuration."""
        # Outil d'annotation
        annotator_tool = cfg.get("annotator_tool", "spacy")
        if annotator_tool == "spacy":
            self._w_annotator_tool.setCurrentIndex(0)
        elif annotator_tool == "stanza":
            self._w_annotator_tool.setCurrentIndex(1)
        else:
            self._w_annotator_tool.setCurrentIndex(0)
        
        # Mettre à jour la disponibilité GPU selon l'outil
        self._update_gpu_availability()
        
        # Langue
        lang = cfg.get("language", "fr")
        idx = self._w_language.findText(lang)
        if idx >= 0:
            self._w_language.setCurrentIndex(idx)
        else:
            self._w_language.setEditText(lang)
        # GPU : adapter selon disponibilité
        if self._gpu_available and self._w_gpu_choice is not None:
            use_gpu = cfg.get("use_gpu", True)  # Par défaut GPU si disponible
            self._w_gpu_choice.setCurrentText("GPU" if use_gpu else "CPU")
        # Si pas de GPU disponible, pas besoin de charger la valeur
        self._w_minsup.setValue(self._coerce_minsup_value(cfg.get("list_minsup_percent", [25])))
        self._w_itemset_min.setValue(cfg.get("list_itemset_min", [3])[0])
        self._w_Lemma.setChecked(cfg.get("Lemma", True))
        self._w_Pos.setChecked(cfg.get("Pos", True))
        self._w_Dep.setChecked(cfg.get("Dep", True))
        self._w_Form.setChecked(cfg.get("Form", False))
        self._w_Feats.setChecked(cfg.get("Feats", False))
        
        # Corpus selector
        path_corpus = cfg.get("path_corpus", "")
        
        if path_corpus:
            # Extraire le nom du corpus depuis le chemin (ex: "./Data/Corpus/Textes_raw" → "Textes_raw")
            corpus_name = Path(path_corpus).name
            
            # Vérifier que le chemin existe réellement
            if not Path(path_corpus).exists():
                # Chemin invalide : ne pas l'ajouter, laisser le dropdown vide ou sur le premier élément
                print(f"⚠ Chemin de corpus invalide dans la config : {path_corpus}")
                print(f"  → Veuillez sélectionner un corpus existant dans Data/Corpus/")
                corpus_name = ""  # Réinitialiser
            
            if corpus_name:
                idx = self._w_corpus_selector.findText(corpus_name)
                if idx >= 0:
                    self._w_corpus_selector.setCurrentIndex(idx)
                else:
                    # Si le nom existe mais n'est pas dans la liste, l'ajouter
                    self._w_corpus_selector.addItem(corpus_name)
                    self._w_corpus_selector.setCurrentText(corpus_name)
        input_mode = cfg.get("input_mode", "raw")
        if input_mode == "annotated_conllu":
            self._w_input_mode.setCurrentIndex(1)
        elif input_mode == "prepared_conllu_zip":
            self._w_input_mode.setCurrentIndex(2)
        else:
            self._w_input_mode.setCurrentIndex(0)
        self._w_annotated_corpus_path.setText(cfg.get("path_annotated_corpus", ""))
        self._w_prepared_zip_path.setText(cfg.get("path_prepared_archive", ""))
        self._w_list_metadata.setText(", ".join(cfg.get("list_metadata", ["id"])))
        self._update_input_mode_state()

        # Avancé
        self._w_earlySelection.setChecked(cfg.get("earlySelection", False))
        self._w_seuil_early.setValue(cfg.get("seuil_early_selection", 200))
        self._w_filter_specifs.setChecked(cfg.get("filter_specifs", False))
        self._w_partition_cible.setText(cfg.get("partition_cible", "test"))
        self._w_seuil_banalite.setValue(cfg.get("seuil_banalité", 2))
        self._w_early_pos4lemma.setText(cfg.get("early_pos4lemma", "ADJ|NOUN|VERB"))
        self._w_user_input_list.setChecked(cfg.get("user_input_list", False))
        self._w_liste_earlyselection.setText(", ".join(cfg.get("liste_earlyselection_lemma", [])))
        self._update_early_selection_state(self._w_earlySelection.isChecked())
        self._update_manual_lemma_list_state(self._w_user_input_list.isChecked())
        self._w_internal_clustering.setChecked(cfg.get("internal_clustering", True))
        self._w_gap_min.setValue(cfg.get("list_gap_min", [0])[0])
        self._w_gap_max.setValue(cfg.get("list_gap_max", [0])[0])
        self._w_threads.setValue(cfg.get("threads", 4))
        self._w_specifs.setChecked(cfg.get("specifs", False))
        self._w_liste_seuils_lemma.setText(", ".join(str(s) for s in cfg.get("liste_seuils_lemma", [100, 200])))
        self._w_downhill_pos4lemma.setText(cfg.get("downhill_pos4lemma", "ADJ|ADV|NOUN|VERB"))
        self._w_liste_seuils_bigrams.setText(", ".join(str(s) for s in cfg.get("liste_seuils_bigrams", [100])))

    def _read_config_from_ui(self) -> dict:
        """Lit tous les widgets et retourne un dict de configuration."""
        def parse_int_list(text: str) -> list[int]:
            try:
                return [int(x.strip()) for x in text.split(",") if x.strip()]
            except ValueError:
                return []

        def parse_str_list(text: str) -> list[str]:
            return [x.strip() for x in text.split(",") if x.strip()]
        
        # Extraire le nom de l'outil depuis le texte du dropdown
        annotator_text = self._w_annotator_tool.currentText()
        if "spaCy" in annotator_text:
            annotator_tool = "spacy"
        elif "Stanza" in annotator_text:
            annotator_tool = "stanza"
        else:
            annotator_tool = "spacy"  # Par défaut

        minsup_value = self._normalize_minsup_value(self._w_minsup.value())

        return {
            # Simple
            "analysis_group_name": self._build_analysis_name_from_corpus_name(self._w_corpus_selector.currentText().strip()) or "analyse_sans_nom",
            "input_mode": self._get_input_mode(),
            "annotator_tool": annotator_tool,
            "language": self._w_language.currentText().strip() or "fr",
            "use_gpu": self._w_gpu_choice.currentText() == "GPU" if (self._gpu_available and self._w_gpu_choice) else False,
            "list_minsup_percent": [minsup_value],
            "list_itemset_min": [self._w_itemset_min.value()],
            "Lemma": self._w_Lemma.isChecked(),
            "Pos": self._w_Pos.isChecked(),
            "Dep": self._w_Dep.isChecked(),
            "Form": self._w_Form.isChecked(),
            "Feats": self._w_Feats.isChecked(),
            "path_corpus": self._get_corpus_path_from_name(self._w_corpus_selector.currentText().strip()),
            "path_annotated_corpus": self._w_annotated_corpus_path.text().strip(),
            "path_prepared_archive": self._w_prepared_zip_path.text().strip(),
            "list_metadata": parse_str_list(self._w_list_metadata.text()),
            # Avancé
            "earlySelection": self._w_earlySelection.isChecked(),
            "seuil_early_selection": self._w_seuil_early.value(),
            "filter_specifs": self._w_filter_specifs.isChecked(),
            "partition_cible": self._w_partition_cible.text().strip(),
            "seuil_banalité": self._w_seuil_banalite.value(),
            "early_pos4lemma": self._w_early_pos4lemma.text().strip(),
            "user_input_list": self._w_user_input_list.isChecked(),
            "liste_earlyselection_lemma": parse_str_list(self._w_liste_earlyselection.text()),
            "internal_clustering": self._w_internal_clustering.isChecked(),
            "list_gap_min": [self._w_gap_min.value()],
            "list_gap_max": [self._w_gap_max.value()],
            "threads": self._w_threads.value(),
            "specifs": self._w_specifs.isChecked(),
            "liste_seuils_lemma": parse_int_list(self._w_liste_seuils_lemma.text()),
            "downhill_pos4lemma": self._w_downhill_pos4lemma.text().strip(),
            "liste_seuils_bigrams": parse_int_list(self._w_liste_seuils_bigrams.text()),
            "mode": "",
        }

    def _coerce_minsup_value(self, raw_value) -> float:
        if isinstance(raw_value, list):
            raw_value = raw_value[0] if raw_value else 25
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            value = 25.0
        return max(0.1, min(100.0, value))

    def _normalize_minsup_value(self, value: float) -> int | float:
        rounded_value = round(float(value), 1)
        if rounded_value.is_integer():
            return int(rounded_value)
        return rounded_value

    def get_config(self) -> dict:
        """Retourne la configuration actuellement appliquée."""
        return self._sanitize_config_for_environment(self._config)

    def _normalized_config_for_compare(self, cfg: dict) -> dict:
        """Retire les champs transitoires pour comparer deux configurations."""
        return {
            key: value
            for key, value in self._sanitize_config_for_environment(cfg).items()
            if not str(key).startswith("_")
        }

    def has_unapplied_changes(self) -> bool:
        """Indique si l'UI contient des modifications non appliquées."""
        current_ui_config = self._normalized_config_for_compare(self._read_config_from_ui())
        applied_config = self._normalized_config_for_compare(self._config)
        return current_ui_config != applied_config

    def get_unapplied_changes_summary(self, max_items: int = 8) -> list[str]:
        """Retourne une liste lisible des paramètres modifiés mais non appliqués."""
        current_ui_config = self._normalized_config_for_compare(self._read_config_from_ui())
        applied_config = self._normalized_config_for_compare(self._config)

        label_map = {
            "analysis_group_name": "Nom du dossier d'analyse",
            "annotator_tool": "Outil d'annotation",
            "language": "Langue",
            "use_gpu": "Accélération",
            "list_minsup_percent": "Support minimal",
            "list_itemset_min": "Itemset min",
            "Lemma": "Lemmes",
            "Pos": "POS",
            "Dep": "Dépendances",
            "Form": "Formes",
            "Feats": "Traits morphologiques",
            "path_corpus": "Corpus",
            "input_mode": "Type d'entrée",
            "path_annotated_corpus": "Dossier annoté",
            "path_prepared_archive": "Archive préparée",
            "list_metadata": "Métadonnées",
            "earlySelection": "Early selection",
            "seuil_early_selection": "Seuil early selection",
            "filter_specifs": "Filtre par spécificités",
            "partition_cible": "Partition cible",
            "seuil_banalité": "Seuil de banalité",
            "early_pos4lemma": "POS early selection",
            "user_input_list": "Liste de lemmes manuelle",
            "liste_earlyselection_lemma": "Lemmes ciblés",
            "internal_clustering": "Clustering interne",
            "list_gap_min": "Gap min",
            "list_gap_max": "Gap max",
            "threads": "Threads",
            "specifs": "Spécificités",
            "liste_seuils_lemma": "Seuils lemmes",
            "downhill_pos4lemma": "POS lemmes comparatifs",
            "liste_seuils_bigrams": "Seuils bigrammes",
        }

        def _fmt(value):
            if isinstance(value, bool):
                return "Oui" if value else "Non"
            if isinstance(value, list):
                return ", ".join(str(v) for v in value) if value else "-"
            if value in ("", None):
                return "-"
            return str(value)

        changes: list[str] = []
        all_keys = list(dict.fromkeys(list(applied_config.keys()) + list(current_ui_config.keys())))
        for key in all_keys:
            old_value = applied_config.get(key)
            new_value = current_ui_config.get(key)
            if old_value != new_value:
                label = label_map.get(key, key)
                changes.append(f"{label} : {_fmt(old_value)} -> {_fmt(new_value)}")

        if len(changes) > max_items:
            hidden_count = len(changes) - max_items
            changes = changes[:max_items] + [f"... et {hidden_count} autre(s) modification(s)"]

        return changes
    
    # ===============================
    # Actions
    # ===============================
    
    def _open_metadata_wizard(self):
        current_cfg = self._read_config_from_ui()
        dialog = MetadataWizardDialog(current_cfg, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            result_cfg = dialog.get_result_config()
            # Mettre à jour le sélecteur de corpus
            path_corpus = result_cfg["path_corpus"]
            idx = self._w_corpus_selector.findText(path_corpus)
            if idx >= 0:
                self._w_corpus_selector.setCurrentIndex(idx)
            else:
                self._w_corpus_selector.addItem(path_corpus)
                self._w_corpus_selector.setCurrentText(path_corpus)
            # Mettre à jour les colonnes de metadata
            self._w_list_metadata.setText(", ".join(result_cfg["list_metadata"]))

    def get_current_config(self) -> dict:
        """Retourne la configuration actuelle lue depuis l'UI (sans persister)."""
        return self._sanitize_config_for_environment(self._read_config_from_ui())
    
    def _on_apply(self, _checked: bool = False, silent: bool = False):
        """Applique la configuration actuelle (avec ou sans message)."""
        self._config = self._sanitize_config_for_environment(self._read_config_from_ui())
        if self._profile_combo.currentText():
            self._current_profile_name = self._profile_combo.currentText()
        self._config["_display_profile_name"] = self._current_profile_name or "Configuration appliquée"
        self.config_applied.emit(self._config)  # Émettre le signal
        self._mark_as_applied()
        if not silent:
            QMessageBox.information(
                self,
                "Configuration appliquée",
                "Les paramètres ont été mis à jour et seront utilisés lors de la prochaine analyse."
            )

    def _on_save_profile(self):
        name, ok = QInputDialog.getText(self, "Sauvegarder le profil", "Nom du profil :")
        if ok and name.strip():
            save_profile(name.strip(), self._read_config_from_ui())
            self._current_profile_name = name.strip()
            self._refresh_profile_list()
            self._profile_combo.setCurrentText(name.strip())

    def _on_load_profile(self):
        """Charge un profil ET l'applique automatiquement."""
        name = self._profile_combo.currentText()
        if not name:
            return
        self._current_profile_name = name
        cfg = self._sanitize_config_for_environment(load_profile(name))
        self._loading = True
        self._load_config_into_ui(cfg)
        self._loading = False
        # Auto-application : charger = appliquer
        self._on_apply(silent=True)
        QMessageBox.information(
            self,
            "Profil appliqué",
            f"Le profil « {name} » a été chargé et appliqué avec succès."
        )

    def _on_delete_profile(self):
        name = self._profile_combo.currentText()
        if not name:
            return
        reply = QMessageBox.question(
            self, "Supprimer le profil",
            f"Supprimer le profil « {name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_profile(name)
            self._refresh_profile_list()

    def _refresh_profile_list(self):
        self._profile_combo.clear()
        self._profile_combo.addItems(list_profiles())

    def _refresh_gpu_label(self):
        gpu_ok, gpu_msg = detect_gpu()
        color = "#2e7d32" if gpu_ok else "#ffaa44"
        self._gpu_label.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent;")
        self._gpu_label.setText(f"{gpu_msg}")    
    def _mark_as_modified(self):
        """Marque la configuration comme modifiée (non appliquée)."""
        if self._loading:  # Ignorer les changements pendant le chargement
            return
        self._status_label.setText("⚠ Modifications non appliquées")
        self._status_label.setStyleSheet("""
            color: #d97706; 
            font-size: 13px; 
            font-weight: bold; 
            background: #fef3c7; 
            padding: 6px 12px; 
            border-radius: 4px;
        """)
    
    def _mark_as_applied(self):
        """Marque la configuration comme appliquée."""
        self._status_label.setText("✓ Configuration appliquée")
        self._status_label.setStyleSheet("""
            color: #2e7d32; 
            font-size: 13px; 
            font-weight: bold; 
            background: #e8f5e9; 
            padding: 6px 12px; 
            border-radius: 4px;
        """)
    
    def _connect_change_signals(self):
        """Connecte tous les widgets pour détecter les modifications manuelles."""
        # QLineEdit
        for widget_name in ['_w_list_metadata', '_w_partition_cible',
                             '_w_early_pos4lemma', '_w_liste_earlyselection', 
                             '_w_liste_seuils_lemma', '_w_downhill_pos4lemma', 
                             '_w_liste_seuils_bigrams']:
            widget = getattr(self, widget_name, None)
            if widget:
                widget.textChanged.connect(self._mark_as_modified)
        
        # QComboBox
        for widget_name in ['_w_corpus_selector', '_w_annotator_tool', '_w_language']:
            widget = getattr(self, widget_name, None)
            if widget:
                widget.currentIndexChanged.connect(self._mark_as_modified)
        
        if self._w_gpu_choice:
            self._w_gpu_choice.currentIndexChanged.connect(self._mark_as_modified)
        
        # QSpinBox / QDoubleSpinBox
        for widget_name in ['_w_minsup', '_w_itemset_min', '_w_seuil_early', '_w_seuil_banalite',
                             '_w_gap_min', '_w_gap_max', '_w_threads']:
            widget = getattr(self, widget_name, None)
            if widget:
                widget.valueChanged.connect(self._mark_as_modified)
        
        # QCheckBox
        for widget_name in ['_w_Lemma', '_w_Pos', '_w_Dep', '_w_Form', '_w_Feats',
                             '_w_earlySelection', '_w_filter_specifs', '_w_user_input_list',
                             '_w_internal_clustering', '_w_specifs']:
            widget = getattr(self, widget_name, None)
            if widget:
                widget.stateChanged.connect(self._mark_as_modified)    
    # ========================================================
    # Styles
    # ========================================================
    
    def _group_style(self, enabled: bool = True) -> str:
        group_color = "#111827" if enabled else "#9ca3af"
        border_color = "#d4d7e3" if enabled else "#e5e7eb"
        background_color = "#ffffff" if enabled else "#f3f4f6"
        input_background = "#ffffff" if enabled else "#f9fafb"
        input_color = "#111827" if enabled else "#9ca3af"
        input_border = "#c7ccda" if enabled else "#e5e7eb"
        checkbox_color = "#1f2937" if enabled else "#9ca3af"
        indicator_border = "#6b7280" if enabled else "#d1d5db"
        indicator_background = "#ffffff" if enabled else "#f3f4f6"
        label_color = "#1f2937" if enabled else "#9ca3af"

        return f"""
            QGroupBox {{
                color: {group_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                margin-top: 8px;
                padding: 10px;
                font-weight: bold;
                background: {background_color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {input_background};
                color: {input_color};
                border: 1px solid {input_border};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
                background: #f3f4f6;
                color: #9ca3af;
                border: 1px solid #d1d5db;
            }}
            QCheckBox {{ color: {checkbox_color}; background: transparent; }}
            QCheckBox:disabled {{ color: #9ca3af; }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {indicator_border};
                border-radius: 3px;
                background: {indicator_background};
            }}
            QCheckBox::indicator:disabled {{
                border: 1px solid #d1d5db;
                background: #f3f4f6;
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid #2563eb;
                background: #2563eb;
                image: url(__CHECK_ICON__);
            }}
            QLabel {{ color: {label_color}; background: transparent; }}
            QLabel:disabled {{ color: #9ca3af; }}
        """.replace("__CHECK_ICON__", self._check_icon_path)

    def _page_style(self) -> str:
        return """
            QWidget {
                background: #f7f8fc;
                color: #1f2937;
            }
            QToolTip {
                background-color: #fffbe6;
                color: #1f2937;
                border: 1px solid #c9b458;
                padding: 6px;
                font-size: 12px;
            }
        """
