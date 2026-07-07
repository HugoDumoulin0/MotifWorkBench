"""
Page d'aide : guide d'utilisation structuré de l'application.
@jcharlesDS (2026)
"""

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT


class HelpPage(BasePage):
    """Page d'aide structurée avec guide rapide, tutoriels, FAQ et manuel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._manual_markdown_path = self._project_root / "docs" / "user_manual.md"
        self._build_ui()

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

        layout.addWidget(
            self.make_title(
                "Aide",
                "Repères rapides, tutoriels, FAQ et manuel d'utilisation pour travailler plus sereinement.",
            )
        )

        intro = QLabel(
            "Cette page rassemble l'essentiel pour prendre en main MWB :"
            " démarrage rapide, explications pas à pas, réponses aux questions fréquentes"
            " et manuel consultable directement dans l'application."
        )
        intro.setWordWrap(True)
        intro.setFont(QFont("Segoe UI", 10))
        intro.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        layout.addWidget(intro)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: #ffffff;
            }}
            QTabBar::tab {{
                background: #eef2ff;
                color: {TEXT_PRIMARY};
                padding: 10px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: #ffffff;
                color: {ACCENT};
                font-weight: bold;
            }}
            """
        )
        tabs.addTab(self._build_quickstart_tab(), "Aide rapide")
        tabs.addTab(self._build_tutorials_tab(), "Tutoriels")
        tabs.addTab(self._build_faq_tab(), "FAQ")
        tabs.addTab(self._build_manual_tab(), "Manuel")
        layout.addWidget(tabs)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _build_quickstart_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        steps_group = self.make_group("Commencer ici")
        steps_layout = QVBoxLayout(steps_group)
        for title, text in [
            (
                "1. Préparer le corpus",
                "Rassemblez les textes à analyser et vérifiez la cohérence des noms de fichiers, des langues et des métadonnées.",
            ),
            (
                "2. Régler l'analyse",
                "Choisissez les représentations linguistiques, les paramètres des motifs et les options statistiques adaptées à votre objectif.",
            ),
            (
                "3. Lancer le traitement",
                "Démarrez l'analyse depuis la page Analyse puis surveillez les logs, la progression et les sorties générées.",
            ),
            (
                "4. Explorer les résultats",
                "Consultez Shiny, le concordancier et l'historique pour interpréter les motifs, comparer les partitions et relancer plus vite.",
            ),
        ]:
            card = QLabel(f"<b>{title}</b><br>{text}")
            card.setWordWrap(True)
            card.setTextFormat(Qt.TextFormat.RichText)
            card.setStyleSheet(
                "background-color: #f8fafc; border: 1px solid #e5e7eb; "
                "border-radius: 8px; padding: 12px;"
            )
            steps_layout.addWidget(card)
        layout.addWidget(steps_group)

        workflow_group = self.make_group("Workflow conseillé")
        workflow_layout = QVBoxLayout(workflow_group)
        workflow = QLabel(
            "Import du corpus → vérification des métadonnées → choix des annotations → "
            "réglage des motifs / spécificités → lancement de l'analyse → exploration dans Shiny "
            "et le concordancier."
        )
        workflow.setWordWrap(True)
        workflow.setFont(QFont("Segoe UI", 10))
        workflow.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        workflow_layout.addWidget(workflow)
        layout.addWidget(workflow_group)

        tips_group = self.make_group("Bonnes pratiques")
        tips_layout = QVBoxLayout(tips_group)
        tips = QLabel(
            "• Commencez avec un corpus ou un sous-ensemble réduit pour valider vos réglages.\n"
            "• Sauvegardez plusieurs profils de configuration pour comparer facilement les analyses.\n"
            "• Utilisez les spécificités pour interpréter les écarts entre partitions.\n"
            "• Vérifiez les logs et l'historique après chaque run pour retrouver rapidement les sorties utiles."
        )
        tips.setWordWrap(True)
        tips.setFont(QFont("Segoe UI", 10))
        tips.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        tips_layout.addWidget(tips)
        layout.addWidget(tips_group)
        layout.addStretch()
        return tab

    def _build_tutorials_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        for title, text in [
            (
                "Première analyse simple",
                "Chargez un corpus, laissez les réglages de base, lancez l'analyse puis vérifiez que les tableaux et graphiques s'ouvrent correctement.",
            ),
            (
                "Analyse avec métadonnées",
                "Ajoutez des colonnes comme id, genre, période ou auteur, puis utilisez-les pour construire des contrastes et comparer les résultats.",
            ),
            (
                "Utiliser les spécificités",
                "Activez le calcul des spécificités pour identifier les motifs sur- ou sous-représentés selon chaque partition.",
            ),
            (
                "Explorer les motifs dans Shiny",
                "Passez d'un tableau à l'autre, filtrez les résultats, affichez les tables de spécificités et observez les dimensions principales.",
            ),
            (
                "Utiliser le concordancier",
                "Sélectionnez un motif, choisissez l'affichage motif ou mots trouvés, puis vérifiez ses occurrences réelles dans le corpus.",
            ),
        ]:
            group = self.make_group(title)
            group_layout = QVBoxLayout(group)
            label = QLabel(text)
            label.setWordWrap(True)
            label.setFont(QFont("Segoe UI", 10))
            label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
            group_layout.addWidget(label)
            layout.addWidget(group)

        layout.addStretch()
        return tab

    def _build_faq_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        faqs = [
            (
                "Pourquoi Shiny est vide ou incomplet ?",
                "Vérifiez qu'une analyse complète est terminée, que les fichiers TSV existent bien dans les résultats et que le dernier export Shiny pointe vers des chemins valides.",
            ),
            (
                "Pourquoi les spécificités ne s'affichent pas ?",
                "Assurez-vous d'avoir activé l'option de calcul des spécificités, puis vérifiez que les fichiers TSV ont bien été générés dans le dossier Specifs.",
            ),
            (
                "Que signifie minsup ?",
                "Le support minimal correspond au pourcentage minimal de séquences dans lesquelles un motif doit apparaître pour être retenu.",
            ),
            (
                "Motif ou mots trouvés : quelle différence ?",
                "Le motif est une représentation abstraite fondée sur les annotations ; les mots trouvés montrent les réalisations observées en contexte dans le concordancier.",
            ),
            (
                "Pourquoi le registry CWB est introuvable ?",
                "L'analyse doit avoir construit le corpus CWB. Si le chemin n'existe plus ou si le corpus a été déplacé, relancez une analyse complète.",
            ),
            (
                "Où se trouvent les résultats ?",
                "Les sorties sont principalement stockées dans les dossiers d'analyse, avec des sous-dossiers pour Patterns_results, Specifs, Clustering_results et logs.",
            ),
        ]

        for question, answer in faqs:
            group = self.make_group(question)
            group_layout = QVBoxLayout(group)
            label = QLabel(answer)
            label.setWordWrap(True)
            label.setFont(QFont("Segoe UI", 10))
            label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
            group_layout.addWidget(label)
            layout.addWidget(group)

        layout.addStretch()
        return tab

    def _build_manual_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        manual_group = self.make_group("Manuel d'utilisation")
        manual_layout = QVBoxLayout(manual_group)

        description = QLabel(
            "Le manuel est consultable directement ci-dessous. "
        )
        description.setWordWrap(True)
        description.setFont(QFont("Segoe UI", 10))
        description.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        manual_layout.addWidget(description)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        open_manual_btn = QPushButton("Ouvrir le fichier .md")
        open_manual_btn.clicked.connect(self._open_manual_resource)
        open_manual_btn.setStyleSheet(self._action_button_style())
        button_row.addWidget(open_manual_btn)

        open_docs_btn = QPushButton("Ouvrir le dossier docs")
        open_docs_btn.clicked.connect(self._open_docs_folder)
        open_docs_btn.setStyleSheet(self._secondary_button_style())
        button_row.addWidget(open_docs_btn)
        button_row.addStretch()
        manual_layout.addLayout(button_row)

        self._manual_status = QLabel()
        self._manual_status.setWordWrap(True)
        self._manual_status.setFont(QFont("Segoe UI", 9))
        self._manual_status.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background-color: transparent; font-style: italic;"
        )
        manual_layout.addWidget(self._manual_status)

        self._manual_browser = QTextBrowser()
        self._manual_browser.setOpenExternalLinks(True)
        self._manual_browser.setMinimumHeight(420)
        self._manual_browser.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: #ffffff;
                color: {TEXT_PRIMARY};
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                font-size: 10pt;
            }}
            """
        )
        manual_layout.addWidget(self._manual_browser)

        self._load_manual_content()

        layout.addWidget(manual_group)
        layout.addStretch()
        return tab

    def _load_manual_content(self):
        if self._manual_markdown_path.exists():
            content = self._manual_markdown_path.read_text(encoding="utf-8", errors="ignore")
            self._manual_browser.setMarkdown(content)
            self._manual_status.setText(
                f"Source affichée : {self._manual_markdown_path.name}"
            )
            return

        self._manual_browser.setPlainText(
            "Aucun manuel n'a encore été trouvé dans le dossier docs.\n\n"
            "Ajoutez un fichier `docs/user_manual.md` pour l'afficher ici."
        )
        self._manual_status.setText("Aucun manuel local détecté pour le moment.")

    def _open_manual_resource(self):
        target = self._manual_markdown_path
        if target.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _open_docs_folder(self):
        docs_dir = self._project_root / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(docs_dir)))

    def _action_button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
        """

    def _secondary_button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: #eef2ff;
                color: {TEXT_PRIMARY};
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 14px;
            }}
            QPushButton:hover {{
                background-color: #e0e7ff;
            }}
        """
