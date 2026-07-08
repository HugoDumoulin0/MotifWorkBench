"""
Page de configuration de l'analyse.
Paramètres simple: paramètres essentiels
Paramètres avancé: tous les paramètres
@jcharlesDS (2026)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QComboBox, QGroupBox,
    QScrollArea, QMessageBox, QInputDialog, QFrame, QDialog, QStyle, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
import os
import sys
import datetime

# Importer les annotateurs
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from annotators import ANNOTATORS

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
    
    config_applied = pyqtSignal(dict, str)  # config, nom d'affichage
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._corpus_root = self._project_root / "Data" / "Corpus"
        self._available_corpora: dict[str, Path] = {}
        
        # Flags de gestion de l'état
        self._loading = True  # True pendant le chargement initial pour ignorer les signaux
        self._config_applied = False  # True si la config actuelle a été appliquée
        
        # Charger le premier profil disponible ou DEFAULT_CONFIG
        try:
            profiles = list_profiles()
            if profiles:
                self._config = load_profile(profiles[0])
            else:
                self._config = dict(DEFAULT_CONFIG)
        except Exception:
            self._config = dict(DEFAULT_CONFIG)
        
        self._check_icon_path = (Path(__file__).resolve().parent.parent / "assets" / "checkmark.svg").as_posix()
        # Détection GPU au démarrage
        self._gpu_available, self._gpu_description = detect_gpu()
        if not self._gpu_available:
            self._config["use_gpu"] = False
        self._setup_ui()
        self._load_config_into_ui(self._config)
        
        # Connecter les signaux de changement après le chargement initial
        self._connect_change_signals()
        
        # Marquer la configuration initiale comme appliquée
        self._loading = False
        self._mark_config_applied()
    
    # =================================
    # Construction de l'UI
    # =================================
    
    def _setup_ui(self):
        self.setStyleSheet(self._page_style())

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        
        # Titre
        title = QLabel("Réglages de l'analyse")
        title.setFont(QFont("Helvetica Neue", 17, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2937; background: transparent;")
        root.addWidget(title)
        
        # Barre GPU
        self._gpu_label = QLabel()
        self._gpu_label.setStyleSheet("color: #4b5563; font-size: 13px; background: transparent;")
        self._refresh_gpu_label()
        root.addWidget(self._gpu_label)
        
        # Indicateur d'état de la configuration
        self._config_indicator = QLabel()
        self._config_indicator.setStyleSheet("font-size: 12px; font-weight: bold; background: transparent; padding: 4px 0px;")
        root.addWidget(self._config_indicator)
        
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

    # ================================
    # Panneau de configuration simple
    # ================================

    def _build_simple_panel(self):
        self._simple_panel = QWidget()
        layout = QVBoxLayout(self._simple_panel)
        layout.setSpacing(12)
        
        # Corpus + métadonnées
        grp_corpus = QGroupBox("Corpus et métadonnées")
        grp_corpus.setStyleSheet(self._group_style())
        form_corpus = QFormLayout(grp_corpus)

        corpus_select_row = QWidget()
        corpus_select_layout = QHBoxLayout(corpus_select_row)
        corpus_select_layout.setContentsMargins(0, 0, 0, 0)
        corpus_select_layout.setSpacing(8)

        self._w_selected_corpus = QComboBox()
        self._w_selected_corpus.setToolTip("Sélectionne un dossier de corpus dans Data/Corpus.")
        self._w_selected_corpus.currentTextChanged.connect(self._on_selected_corpus_changed)
        corpus_select_layout.addWidget(self._w_selected_corpus, 1)

        self._btn_refresh_corpora = QPushButton()
        self._btn_refresh_corpora.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self._btn_refresh_corpora.setFixedSize(32, 32)
        self._btn_refresh_corpora.setToolTip("Rafraîchir la liste des corpus")
        self._btn_refresh_corpora.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_refresh_corpora.setStyleSheet("""
            QPushButton {
                background: #2a2a3a;
                border: 1px solid #3a3a5a;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #3a3a5a;
                border-color: #4a4a6a;
            }
            QPushButton:pressed {
                background: #1a1a2a;
            }
        """)
        self._btn_refresh_corpora.clicked.connect(self._on_refresh_corpora)
        corpus_select_layout.addWidget(self._btn_refresh_corpora)

        form_corpus.addRow(_tooltip_label("Corpus à analyser :", "Dossier contenant les textes .txt et metadata.tsv."), corpus_select_row)

        self._w_corpus_summary = QLabel("Aucun corpus sélectionné.")
        self._w_corpus_summary.setStyleSheet("color: #4b5563; background: transparent; font-style: italic;")
        self._w_corpus_summary.setWordWrap(True)
        form_corpus.addRow("", self._w_corpus_summary)

        self._w_input_type = QComboBox()
        self._w_input_type.addItem("Corpus brut (.txt)", "raw_txt")
        self._w_input_type.addItem("Corpus annoté (.conllu)", "annotated_conllu")
        self._w_input_type.addItem("Archive préparée (.zip)", "prepared_zip")
        self._w_input_type.setToolTip("Choisissez la nature des données en entrée de l'analyse.")
        self._w_input_type.currentIndexChanged.connect(self._update_input_type_ui)
        form_corpus.addRow(
            _tooltip_label("Type d'entrée :", "Corpus brut, corpus déjà annoté ou archive préparée."),
            self._w_input_type,
        )

        input_source_row = QWidget()
        input_source_layout = QHBoxLayout(input_source_row)
        input_source_layout.setContentsMargins(0, 0, 0, 0)
        input_source_layout.setSpacing(8)

        self._w_input_source_path = QLineEdit()
        self._w_input_source_path.setPlaceholderText("Sélectionnez un dossier .conllu ou une archive .zip")
        self._w_input_source_path.setToolTip("Chemin vers le dossier importé ou l'archive préparée.")
        input_source_layout.addWidget(self._w_input_source_path, 1)

        self._btn_browse_input_source = QPushButton("Parcourir…")
        self._btn_browse_input_source.setMinimumHeight(32)
        self._btn_browse_input_source.setStyleSheet(
            "background:#2a2a3a; color:#ffffff; border:none; border-radius:6px; padding:4px 14px;"
        )
        self._btn_browse_input_source.clicked.connect(self._browse_input_source)
        input_source_layout.addWidget(self._btn_browse_input_source)

        form_corpus.addRow(
            _tooltip_label("Source importée :", "Dossier de .conllu ou archive .zip, selon le type d'entrée."),
            input_source_row,
        )

        self._w_input_type_help = QLabel()
        self._w_input_type_help.setWordWrap(True)
        self._w_input_type_help.setStyleSheet("color: #4b5563; background: transparent; font-style: italic;")
        form_corpus.addRow("", self._w_input_type_help)

        # Widgets internes (non affichés) pour compatibilité
        self._w_metadata_corpus_dir = QLineEdit()
        self._w_metadata_corpus_dir.hide()

        self._w_path_metadata = QLineEdit()
        self._w_path_metadata.setPlaceholderText("./Data/Corpus/MonCorpus/metadata.tsv")
        self._w_path_metadata.setToolTip("Chemin vers le fichier metadata.tsv du corpus sélectionné.")
        self._w_path_metadata.hide()

        self._w_list_metadata = QLineEdit()
        self._w_list_metadata.setPlaceholderText("id, genre, word_count, sentence_count…")
        self._w_list_metadata.setToolTip("Colonnes du metadata.tsv à utiliser pour les analyses. Séparées par des virgules.")
        form_corpus.addRow(_tooltip_label("Partitions :", "Colonnes à utiliser pour regrouper les textes."), self._w_list_metadata)

        self._btn_metadata_wizard = QPushButton("Ouvrir l'assistant de métadonnées")
        self._btn_metadata_wizard.setMinimumHeight(34)
        self._btn_metadata_wizard.setStyleSheet(
            "background:#2a2a3a; color:#ffffff; border:none; border-radius:6px; padding:4px 14px;"
        )
        self._btn_metadata_wizard.clicked.connect(self._open_metadata_wizard)
        form_corpus.addRow("", self._btn_metadata_wizard)
        layout.addWidget(grp_corpus)
        
        # Langue et Annotation
        grp_lang = QGroupBox("Langue et annotation")
        grp_lang.setStyleSheet(self._group_style())
        form_lang = QFormLayout(grp_lang)
        
        self._w_language = QComboBox()
        self._w_language.setEditable(True)
        self._w_language.addItems(["fr", "en"])
        self._w_language.setToolTip("Code ISO de la langue du corpus pour l'annotation (ex: fr, en, es, de, it).")
        form_lang.addRow(_tooltip_label("Langue :", "Langue du corpus."), self._w_language)
        
        # Outil d'annotation
        self._w_annotator = QComboBox()
        for annotator_key, annotator in ANNOTATORS.items():
            self._w_annotator.addItem(annotator.get_display_name(), annotator_key)
        self._w_annotator.setToolTip("Outil utilisé pour l'annotation linguistique.")
        self._w_annotator.currentIndexChanged.connect(self._on_annotator_changed)
        form_lang.addRow(_tooltip_label("Outil d'annotation :", "Sélectionnez l'outil d'annotation."), self._w_annotator)

        # Option GPU : affichage adaptatif selon disponibilité et selon l'outil
        if self._gpu_available:
            # GPU détecté : proposer un choix
            self._w_gpu_choice = QComboBox()
            self._w_gpu_choice.addItems(["GPU", "CPU"])
            self._w_gpu_choice.setToolTip(f"GPU détecté : {self._gpu_description}")
            form_lang.addRow(_tooltip_label("Accélération :", "GPU ou CPU pour l'annotation."), self._w_gpu_choice)

            self._gpu_warning_label = QLabel(
                "Note: sur macOS, le GPU peut être plus lent que le CPU selon "
                "l'annotateur, le modèle utilisé et la taille du corpus."
            )
            self._gpu_warning_label.setWordWrap(True)
            self._gpu_warning_label.setStyleSheet(
                "color: #92400e; background: transparent; font-size: 12px; font-style: italic;"
            )
            form_lang.addRow("", self._gpu_warning_label)
        else:
            # Pas de GPU : CPU uniquement
            self._w_gpu_choice = None
            self._gpu_info_label = QLabel(f"CPU uniquement ({self._gpu_description})")
            self._gpu_info_label.setStyleSheet("color: #6b7280; font-style: italic;")
            form_lang.addRow(_tooltip_label("Accélération :", "Aucun GPU détecté."), self._gpu_info_label)
        
        layout.addWidget(grp_lang)

        # Motifs
        grp_motifs = QGroupBox("Paramètres des motifs (CloSPEC)")
        grp_motifs.setStyleSheet(self._group_style())
        form_motifs = QFormLayout(grp_motifs)

        self._w_minsup = QDoubleSpinBox()
        self._w_minsup.setRange(0.1, 100.0)
        self._w_minsup.setDecimals(1)
        self._w_minsup.setSingleStep(0.1)
        self._w_minsup.setSuffix(" %")
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

        # Early selection
        grp_early = QGroupBox("Early Selection (pré-filtrage des lemmes)")
        grp_early.setStyleSheet(self._group_style())
        form_early = QFormLayout(grp_early)

        self._w_earlySelection = QCheckBox("Activer l'early selection")
        self._w_earlySelection.setToolTip("Restreint les lemmes candidats avant la fouille pour accélérer l'extraction.")
        form_early.addRow("", self._w_earlySelection)

        self._w_seuil_early = QSpinBox()
        self._w_seuil_early.setRange(1, 10000)
        self._w_seuil_early.setToolTip("Nombre maximum de lemmes retenus pour l'early selection.")
        form_early.addRow(_tooltip_label("Seuil early selection :", "Top-N lemmes les plus fréquents à conserver."), self._w_seuil_early)

        self._w_filter_specifs = QCheckBox("Filtrer par spécificités")
        self._w_filter_specifs.setToolTip("Restreindre l'early selection aux lemmes spécifiques d'une partition.")
        form_early.addRow("", self._w_filter_specifs)

        self._w_partition_cible = QLineEdit()
        self._w_partition_cible.setToolTip("Nom de la colonne de métadonnées utilisée pour regrouper les textes (ex. genre, periode, source).")
        form_early.addRow(_tooltip_label("Colonne de partition :", "Nom de la colonne metadata utilisée pour calculer les spécificités."), self._w_partition_cible)

        self._w_seuil_banalite = QSpinBox()
        self._w_seuil_banalite.setRange(0, 100)
        self._w_seuil_banalite.setToolTip("Seuil de banalité : lemmes présents dans plus de N partitions sont exclus.")
        form_early.addRow(_tooltip_label("Seuil de banalité :", "Exclure les lemmes trop banals (présents dans trop de partitions)."), self._w_seuil_banalite)

        self._w_early_pos4lemma = QLineEdit()
        self._w_early_pos4lemma.setToolTip("Filtrer les lemmes par POS (ex: ADJ|NOUN|VERB). Laisser vide pour tout.")
        form_early.addRow(_tooltip_label("POS pour early sel. :", "Restreindre l'early selection à ces POS."), self._w_early_pos4lemma)

        self._w_user_input_list = QCheckBox("Utiliser une liste de lemmes manuelle")
        self._w_user_input_list.setToolTip("Utiliser une liste de lemmes fournie manuellement, avec ou sans early selection.")
        form_early.addRow("", self._w_user_input_list)

        self._w_liste_earlyselection = QLineEdit()
        self._w_liste_earlyselection.setPlaceholderText("président, comité, formation…")
        self._w_liste_earlyselection.setToolTip("Liste de lemmes à utiliser (séparés par des virgules).")
        form_early.addRow(_tooltip_label("Lemmes :", "Liste manuelle de lemmes à cibler."), self._w_liste_earlyselection)

        self._w_earlySelection.stateChanged.connect(self._update_early_selection_ui)
        self._w_user_input_list.stateChanged.connect(self._update_manual_lemma_ui)
        self._update_early_selection_ui()
        self._update_manual_lemma_ui()

        layout.addWidget(grp_early)

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
        form_motifs_adv.addRow(_tooltip_label("Gap min :", " Imposer une discontinuité dans le motif."), self._w_gap_min)

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
    
    # ========================================================
    # Chargement et lecture de la configuration dans l'UI
    # ========================================================
    
    def _load_config_into_ui(self, cfg: dict):
        """Remplit tous les widgets avec les valeurs de configuration."""
        # Bloquer les signaux pendant le chargement
        self._loading = True
        if not self._gpu_available:
            cfg["use_gpu"] = False
        
        self._refresh_corpus_list(preferred=cfg.get("selected_corpus", ""))

        # Simple
        lang = cfg.get("language", "fr")
        idx = self._w_language.findText(lang)
        if idx >= 0:
            self._w_language.setCurrentIndex(idx)
        else:
            self._w_language.setEditText(lang)
        
        # Annotateur
        annotator_key = cfg.get("annotator", "stanza")
        annotator_idx = self._w_annotator.findData(annotator_key)
        if annotator_idx >= 0:
            self._w_annotator.setCurrentIndex(annotator_idx)
        else:
            self._w_annotator.setCurrentIndex(0)  # Par défaut : premier dans la liste
        
        # GPU : adapter selon disponibilité
        if self._gpu_available and self._w_gpu_choice is not None:
            use_gpu = cfg.get("use_gpu", True)  # Par défaut GPU si disponible
            self._w_gpu_choice.setCurrentText("GPU" if use_gpu else "CPU")
        # Si pas de GPU disponible, pas besoin de charger la valeur
        self._w_minsup.setValue(float(cfg.get("list_minsup_percent", [25])[0]))
        self._w_itemset_min.setValue(cfg.get("list_itemset_min", [3])[0])
        self._w_Lemma.setChecked(cfg.get("Lemma", True))
        self._w_Pos.setChecked(cfg.get("Pos", True))
        self._w_Dep.setChecked(cfg.get("Dep", True))
        self._w_Form.setChecked(cfg.get("Form", False))
        self._w_Feats.setChecked(cfg.get("Feats", False))
        metadata_corpus_dir = cfg.get("metadata_corpus_dir", "./Data/Corpus/Textes_raw")
        path_metadata = cfg.get("path_metadata", str(Path(metadata_corpus_dir) / "metadata.tsv"))
        self._w_metadata_corpus_dir.setText(metadata_corpus_dir)
        self._w_path_metadata.setText(path_metadata)

        selected_corpus = cfg.get("selected_corpus", "")
        if not selected_corpus:
            maybe_name = Path(metadata_corpus_dir).name
            if maybe_name in self._available_corpora:
                selected_corpus = maybe_name
        if selected_corpus and self._w_selected_corpus.findText(selected_corpus) >= 0:
            self._w_selected_corpus.setCurrentText(selected_corpus)
        self._w_list_metadata.setText(", ".join(cfg.get("list_metadata", ["id"])))
        input_type = cfg.get("input_type", "raw_txt")
        input_type_index = self._w_input_type.findData(input_type)
        self._w_input_type.setCurrentIndex(input_type_index if input_type_index >= 0 else 0)
        self._w_input_source_path.setText(cfg.get("input_source_path", ""))
        self._update_input_type_ui()

        # Avancé
        # Note: download option removed (automatic detection)
        self._w_earlySelection.setChecked(cfg.get("earlySelection", False))
        self._w_seuil_early.setValue(cfg.get("seuil_early_selection", 200))
        self._w_filter_specifs.setChecked(cfg.get("filter_specifs", False))
        self._w_partition_cible.setText(cfg.get("partition_cible", "test"))
        self._w_seuil_banalite.setValue(cfg.get("seuil_banalité", 2))
        self._w_early_pos4lemma.setText(cfg.get("early_pos4lemma", "ADJ|NOUN|VERB"))
        self._w_user_input_list.setChecked(cfg.get("user_input_list", False))
        self._w_liste_earlyselection.setText(", ".join(cfg.get("liste_earlyselection_lemma", [])))
        self._w_internal_clustering.setChecked(cfg.get("internal_clustering", True))
        self._w_gap_min.setValue(cfg.get("list_gap_min", [0])[0])
        self._w_gap_max.setValue(cfg.get("list_gap_max", [0])[0])
        self._w_threads.setValue(cfg.get("threads", 4))
        self._w_specifs.setChecked(cfg.get("specifs", False))
        self._w_liste_seuils_lemma.setText(", ".join(str(s) for s in cfg.get("liste_seuils_lemma", [100, 200])))
        self._w_downhill_pos4lemma.setText(cfg.get("downhill_pos4lemma", "ADJ|ADV|NOUN|VERB"))
        self._w_liste_seuils_bigrams.setText(", ".join(str(s) for s in cfg.get("liste_seuils_bigrams", [100])))
        
        # Réactiver les signaux après le chargement
        self._loading = False

    def _read_config_from_ui(self) -> dict:
        """Lit tous les widgets et retourne un dict de configuration."""
        def parse_int_list(text: str) -> list[int]:
            try:
                return [int(x.strip()) for x in text.split(",") if x.strip()]
            except ValueError:
                return []

        def parse_str_list(text: str) -> list[str]:
            return [x.strip() for x in text.split(",") if x.strip()]

        # Déduire le chemin du corpus depuis le dropdown au lieu de lire un widget
        selected_corpus = self._w_selected_corpus.currentText().strip()
        if selected_corpus and selected_corpus in self._available_corpora:
            metadata_corpus_dir = str(self._available_corpora[selected_corpus])
        else:
            metadata_corpus_dir = "./Data/Corpus/Textes_raw"
        path_metadata = str(Path(metadata_corpus_dir) / "metadata.tsv")
        input_type = self._w_input_type.currentData() or "raw_txt"
        input_source_path = self._w_input_source_path.text().strip()

        return {
            # Simple
            "analysis_group_name": self._build_analysis_group_name(selected_corpus),
            "selected_corpus": selected_corpus,
            "input_type": input_type,
            "input_source_path": input_source_path,
            "language": self._w_language.currentText().strip().lower(),
            "annotator": self._w_annotator.currentData(),  # stanza ou spacy
            "use_gpu": self._w_gpu_choice.currentText() == "GPU" if (self._gpu_available and self._w_gpu_choice) else False,
            "list_minsup_percent": [round(float(self._w_minsup.value()), 1)],
            "list_itemset_min": [self._w_itemset_min.value()],
            "Lemma": self._w_Lemma.isChecked(),
            "Pos": self._w_Pos.isChecked(),
            "Dep": self._w_Dep.isChecked(),
            "Form": self._w_Form.isChecked(),
            "Feats": self._w_Feats.isChecked(),
            "metadata_corpus_dir": metadata_corpus_dir,
            "path_metadata": path_metadata,
            "list_metadata": parse_str_list(self._w_list_metadata.text()),
            # Avancé
            # download option removed (automatic detection)
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

    def _build_analysis_group_name(self, selected_corpus: str) -> str:
        """Construit automatiquement le nom du dossier d'analyses pour un corpus."""
        corpus_label = selected_corpus.strip()
        if not corpus_label:
            return "analyse_corpus_sans_nom"
        return f"analyse_{corpus_label}"

    def _refresh_corpus_list(self, preferred: str = ""):
        self._available_corpora.clear()
        if self._corpus_root.exists():
            for child in sorted(self._corpus_root.iterdir()):
                if not child.is_dir() or child.name.startswith("."):
                    continue
                has_txt = any(child.glob("*.txt"))
                has_metadata = (child / "metadata.tsv").exists()
                if has_txt or has_metadata:
                    self._available_corpora[child.name] = child

        self._w_selected_corpus.blockSignals(True)
        self._w_selected_corpus.clear()
        self._w_selected_corpus.addItems(self._available_corpora.keys())
        self._w_selected_corpus.blockSignals(False)

        if preferred and preferred in self._available_corpora:
            self._w_selected_corpus.setCurrentText(preferred)
        elif self._w_selected_corpus.count() > 0:
            self._w_selected_corpus.setCurrentIndex(0)
        else:
            self._w_corpus_summary.setText("Aucun corpus détecté dans Data/Corpus.")
            return

        current = self._w_selected_corpus.currentText().strip()
        if current:
            self._apply_selected_corpus_paths(current)

    def _apply_selected_corpus_paths(self, selected_corpus_name: str):
        corpus_path = self._available_corpora.get(selected_corpus_name)
        if not corpus_path:
            return
        self._w_metadata_corpus_dir.setText(str(corpus_path))
        self._w_path_metadata.setText(str(corpus_path / "metadata.tsv"))
        self._update_corpus_summary(corpus_path)

    def _update_corpus_summary(self, corpus_path: Path):
        txt_files = sorted(corpus_path.glob("*.txt"))
        metadata_path = corpus_path / "metadata.tsv"
        metadata_status = "présent" if metadata_path.exists() else "absent"

        latest_mtime = 0.0
        for file_path in txt_files:
            latest_mtime = max(latest_mtime, file_path.stat().st_mtime)
        if metadata_path.exists():
            latest_mtime = max(latest_mtime, metadata_path.stat().st_mtime)

        if latest_mtime:
            dt = datetime.datetime.fromtimestamp(latest_mtime).strftime("%d/%m/%Y %H:%M")
            modified_text = f"Dernière modification: {dt}"
        else:
            modified_text = "Dernière modification: n/a"

        self._w_corpus_summary.setText(
            f"{len(txt_files)} fichier(s) .txt | metadata.tsv {metadata_status} | {modified_text}"
        )

    def _on_selected_corpus_changed(self, selected_corpus_name: str):
        if selected_corpus_name:
            self._apply_selected_corpus_paths(selected_corpus_name)

    def _on_refresh_corpora(self):
        previous = self._w_selected_corpus.currentText()
        self._refresh_corpus_list(preferred=previous)
        if self._w_selected_corpus.count() == 0:
            QMessageBox.information(
                self,
                "Aucun corpus détecté",
                "Aucun dossier corpus détecté dans Data/Corpus.\n"
                "Créez un dossier de corpus contenant des fichiers .txt (et idéalement metadata.tsv)."
            )
    
    def _on_annotator_changed(self, index: int):
        """Adapter l'option GPU selon l'annotateur sélectionné."""
        if not self._gpu_available:
            return  # Pas de GPU, rien à adapter
        
        annotator_key = self._w_annotator.currentData()
        if annotator_key not in ANNOTATORS:
            return
        
        annotator = ANNOTATORS[annotator_key]
        supports_gpu = annotator.supports_gpu()
        
        if self._w_gpu_choice:
            if not supports_gpu:
                # Désactiver et forcer CPU
                self._w_gpu_choice.setEnabled(False)
                self._w_gpu_choice.setCurrentIndex(1)  # CPU
                self._w_gpu_choice.setToolTip(f"{annotator.get_name()} ne supporte pas le GPU")
            else:
                # Réactiver
                self._w_gpu_choice.setEnabled(True)
                tooltip = annotator.get_tooltip()
                if annotator_key == "spacy":
                    tooltip += "\nGPU: modèles Transformers | CPU: modèles Large"
                self._w_gpu_choice.setToolTip(tooltip)

    def _update_input_type_ui(self):
        """Adapte l'UI selon le type d'entrée choisi."""
        input_type = self._w_input_type.currentData() or "raw_txt"
        imported = input_type != "raw_txt"
        self._w_input_source_path.setEnabled(imported)
        self._btn_browse_input_source.setEnabled(imported)

        if input_type == "raw_txt":
            self._w_input_source_path.setPlaceholderText("Aucune source supplémentaire requise")
            self._w_input_type_help.setText(
                "Le corpus sélectionné dans Data/Corpus est utilisé comme corpus brut en .txt, puis annoté par l'application."
            )
        elif input_type == "annotated_conllu":
            self._w_input_source_path.setPlaceholderText("Sélectionnez un dossier contenant des fichiers .conllu")
            self._w_input_type_help.setText(
                "Importe un dossier de fichiers .conllu déjà annotés. L'étape d'annotation est sautée, puis underscore_fix est appliqué."
            )
        else:
            self._w_input_source_path.setPlaceholderText("Sélectionnez une archive .zip préparée")
            self._w_input_type_help.setText(
                "Importe une archive .zip contenant Textes_tagged et/ou underscore_fix. Si underscore_fix est présent, l'annotation et la correction sont entièrement sautées."
            )

    def _browse_input_source(self):
        """Choisit un dossier ou une archive selon le type d'entrée."""
        input_type = self._w_input_type.currentData() or "raw_txt"
        if input_type == "raw_txt":
            return

        current_path = self._w_input_source_path.text().strip()
        start_path = current_path or str(self._project_root)

        if input_type == "annotated_conllu":
            selected = QFileDialog.getExistingDirectory(
                self,
                "Choisir un dossier de fichiers .conllu",
                start_path,
            )
            if selected:
                self._w_input_source_path.setText(selected)
            return

        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir une archive préparée",
            start_path,
            "Archives ZIP (*.zip)",
        )
        if selected:
            self._w_input_source_path.setText(selected)

    def _update_early_selection_ui(self):
        """Grise les options de pré-filtrage quand l'early selection est désactivée."""
        enabled = self._w_earlySelection.isChecked()
        for widget in (
            self._w_seuil_early,
            self._w_filter_specifs,
            self._w_partition_cible,
            self._w_seuil_banalite,
            self._w_early_pos4lemma,
        ):
            widget.setEnabled(enabled)
        self._update_manual_lemma_ui()

    def _update_manual_lemma_ui(self):
        """La liste manuelle est pilotée par sa propre case, indépendamment de l'early selection."""
        self._w_user_input_list.setEnabled(True)
        self._w_liste_earlyselection.setEnabled(self._w_user_input_list.isChecked())

    def get_config(self) -> dict:
        """Retourne la configuration actuellement appliquée."""
        return dict(self._config)
    
    # ===============================
    # Actions
    # ===============================
    
    def _open_metadata_wizard(self):
        selected_corpus = self._w_selected_corpus.currentText().strip()
        if selected_corpus and selected_corpus in self._available_corpora:
            self._apply_selected_corpus_paths(selected_corpus)

        current_cfg = self._read_config_from_ui()
        dialog = MetadataWizardDialog(current_cfg, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            result_cfg = dialog.get_result_config()
            self._w_metadata_corpus_dir.setText(result_cfg["metadata_corpus_dir"])
            self._w_path_metadata.setText(result_cfg["path_metadata"])
            self._w_list_metadata.setText(", ".join(result_cfg["list_metadata"]))

            corpus_dir_name = Path(result_cfg["metadata_corpus_dir"]).name
            if self._w_selected_corpus.findText(corpus_dir_name) >= 0:
                self._w_selected_corpus.setCurrentText(corpus_dir_name)

    def get_current_config(self) -> dict:
        """Retourne la configuration actuelle lue depuis l'UI (sans persister)."""
        return self._read_config_from_ui()

    def has_unapplied_changes(self) -> bool:
        """Indique si l'UI contient des modifications non encore appliquées."""
        return not self._config_applied

    def apply_current_config_silently(self, profile_label: str = "Configuration appliquée") -> dict:
        """Applique la configuration courante sans afficher de message bloquant."""
        self._config = self._read_config_from_ui()
        self.config_applied.emit(self._config, profile_label)
        self._mark_config_applied()
        return dict(self._config)
    
    def _on_apply(self, _checked: bool = False):
        self.apply_current_config_silently("Configuration appliquée")
        QMessageBox.information(
            self,
            "Configuration appliquée",
            "Les paramètres ont été mis à jour et seront utilisés lors de la prochaine analyse."
        )

    def _on_save_profile(self):
        name, ok = QInputDialog.getText(self, "Sauvegarder le profil", "Nom du profil :")
        if ok and name.strip():
            save_profile(name.strip(), self._read_config_from_ui())
            self._refresh_profile_list()

    def _on_load_profile(self):
        name = self._profile_combo.currentText()
        if not name:
            return
        cfg = load_profile(name)
        self._load_config_into_ui(cfg)
        self._config = cfg
        
        # Appliquer automatiquement la configuration
        self.config_applied.emit(self._config, name)
        self._mark_config_applied()
        
        # Message simplifié
        QMessageBox.information(
            self,
            "Profil chargé et appliqué",
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
        self._gpu_label.setStyleSheet(f"color: {color}; font-size: 13px; background: transparent;")
        self._gpu_label.setText(f"{gpu_msg}")
    
    # ========================================================
    # Gestion de l'état de la configuration
    # ========================================================
    
    def _update_config_indicator(self):
        """Met à jour l'indicateur visuel de l'état de la configuration."""
        if self._config_applied:
            self._config_indicator.setText("✓ Configuration appliquée")
            self._config_indicator.setStyleSheet(
                "color: #2e7d32; font-size: 12px; font-weight: bold; background: transparent; padding: 4px 0px;"
            )
        else:
            self._config_indicator.setText("⚠ Modifications non appliquées")
            self._config_indicator.setStyleSheet(
                "color: #f59e0b; font-size: 12px; font-weight: bold; background: transparent; padding: 4px 0px;"
            )
    
    def _mark_config_applied(self):
        """Marque la configuration comme appliquée."""
        self._config_applied = True
        self._update_config_indicator()
    
    def _mark_config_modified(self):
        """Marque la configuration comme modifiée (appelé lors des changements manuels)."""
        if not self._loading:  # Ignorer pendant le chargement
            self._config_applied = False
            self._update_config_indicator()
    
    def _connect_change_signals(self):
        """Connecte tous les widgets aux détecteurs de changement."""
        # Mode simple
        self._w_selected_corpus.currentTextChanged.connect(self._mark_config_modified)
        self._w_input_type.currentIndexChanged.connect(self._mark_config_modified)
        self._w_input_source_path.textChanged.connect(self._mark_config_modified)
        self._w_language.currentTextChanged.connect(self._mark_config_modified)
        self._w_annotator.currentIndexChanged.connect(self._mark_config_modified)
        if self._gpu_available and self._w_gpu_choice:
            self._w_gpu_choice.currentIndexChanged.connect(self._mark_config_modified)
        self._w_minsup.valueChanged.connect(self._mark_config_modified)
        self._w_itemset_min.valueChanged.connect(self._mark_config_modified)
        self._w_Lemma.stateChanged.connect(self._mark_config_modified)
        self._w_Pos.stateChanged.connect(self._mark_config_modified)
        self._w_Dep.stateChanged.connect(self._mark_config_modified)
        self._w_Form.stateChanged.connect(self._mark_config_modified)
        self._w_Feats.stateChanged.connect(self._mark_config_modified)
        self._w_list_metadata.textChanged.connect(self._mark_config_modified)
        
        # Mode avancé
        self._w_earlySelection.stateChanged.connect(self._mark_config_modified)
        self._w_seuil_early.valueChanged.connect(self._mark_config_modified)
        self._w_filter_specifs.stateChanged.connect(self._mark_config_modified)
        self._w_partition_cible.textChanged.connect(self._mark_config_modified)
        self._w_seuil_banalite.valueChanged.connect(self._mark_config_modified)
        self._w_early_pos4lemma.textChanged.connect(self._mark_config_modified)
        self._w_user_input_list.stateChanged.connect(self._mark_config_modified)
        self._w_liste_earlyselection.textChanged.connect(self._mark_config_modified)
        self._w_internal_clustering.stateChanged.connect(self._mark_config_modified)
        self._w_gap_min.valueChanged.connect(self._mark_config_modified)
        self._w_gap_max.valueChanged.connect(self._mark_config_modified)
        self._w_threads.valueChanged.connect(self._mark_config_modified)
        self._w_specifs.stateChanged.connect(self._mark_config_modified)
        self._w_liste_seuils_lemma.textChanged.connect(self._mark_config_modified)
        self._w_downhill_pos4lemma.textChanged.connect(self._mark_config_modified)
        self._w_liste_seuils_bigrams.textChanged.connect(self._mark_config_modified)
    
    # ========================================================
    # Styles
    # ========================================================
    
    def _group_style(self) -> str:
        return """
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
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background: #ffffff;
                color: #111827;
                border: 1px solid #c7ccda;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {
                background: #e5e7eb;
                color: #9ca3af;
                border: 1px solid #d1d5db;
            }
            QCheckBox { color: #1f2937; background: transparent; }
            QCheckBox:disabled { color: #9ca3af; }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #6b7280;
                border-radius: 3px;
                background: #ffffff;
            }
            QCheckBox::indicator:disabled {
                border: 1px solid #cbd5e1;
                background: #e5e7eb;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #2563eb;
                background: #2563eb;
                image: url(__CHECK_ICON__);
            }
            QLabel { color: #1f2937; background: transparent; }
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
                font-size: 13px;
            }
        """
