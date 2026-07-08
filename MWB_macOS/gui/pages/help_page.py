"""
Page d'aide : centre d'aide structuré avec onglets.
@jcharlesDS (2026)
"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel, QWidget, QTabWidget, QTextBrowser
)
from PyQt6.QtGui import QFont

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, TEXT_SECONDARY


class HelpPage(BasePage):
    """Page d'aide avec accès rapide, tutoriels, FAQ et manuel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 24)
        outer.setSpacing(18)

        outer.addWidget(self.make_title(
            "Aide",
            "Retrouvez une aide rapide, des tutoriels, une FAQ et le manuel utilisateur."
        ))

        intro = QLabel(
            "Cette page centralise les informations utiles pour prendre en main "
            "MotifWorkBench, résoudre les questions fréquentes et lire le manuel sans quitter l'application."
        )
        intro.setWordWrap(True)
        intro.setFont(QFont("Helvetica Neue", 11))
        intro.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent;")
        outer.addWidget(intro)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d5db;
                border-radius: 10px;
                background: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background: #eef2f7;
                color: #374151;
                border: 1px solid #d1d5db;
                padding: 10px 16px;
                min-width: 130px;
                font-size: 11pt;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #111827;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #f8fafc;
            }
        """)

        tabs.addTab(self._build_rich_text_tab(self._quick_help_html()), "Aide rapide")
        tabs.addTab(self._build_rich_text_tab(self._tutorials_html()), "Tutoriels")
        tabs.addTab(self._build_rich_text_tab(self._faq_html()), "FAQ")
        tabs.addTab(self._build_manual_tab(), "Manuel")

        outer.addWidget(tabs, 1)

    def _build_rich_text_tab(self, html: str) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        browser = self._make_browser()
        browser.setHtml(html)
        layout.addWidget(browser)
        return tab

    def _build_manual_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info = QLabel(
            "Le contenu ci-dessous est chargé directement depuis `docs/user_manual.md`."
        )
        info.setWordWrap(True)
        info.setFont(QFont("Helvetica Neue", 10))
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent; font-style: italic;")
        layout.addWidget(info)

        browser = self._make_browser()
        manual_path = self._project_root / "docs" / "user_manual.md"
        if manual_path.exists():
            try:
                browser.setMarkdown(manual_path.read_text(encoding="utf-8"))
            except Exception as exc:
                browser.setPlainText(
                    f"Impossible de lire le manuel : {exc}\n\n"
                    f"Fichier attendu : {manual_path}"
                )
        else:
            browser.setPlainText(f"Fichier manuel introuvable : {manual_path}")

        layout.addWidget(browser)
        return tab

    def _make_browser(self) -> QTextBrowser:
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setReadOnly(True)
        browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: #ffffff;
                color: {TEXT_PRIMARY};
                border: none;
                padding: 10px;
                font-size: 11pt;
                line-height: 1.45;
            }}
        """)
        return browser

    def _quick_help_html(self) -> str:
        return """
        <h2 style="color:#111827;">Aide rapide</h2>
        <p style="color:#4b5563;">
        Cette vue sert à retrouver rapidement le parcours conseillé sans lire toute la documentation.
        </p>

        <h3 style="color:#1f2937;">Parcours recommandé</h3>
        <ol>
          <li>Ouvrez <b>Réglages</b> pour choisir le corpus et les paramètres d'analyse.</li>
          <li>Vérifiez les métadonnées avec l'assistant si nécessaire.</li>
          <li>Appliquez la configuration, puis lancez l'analyse dans <b>Analyse</b>.</li>
          <li>Consultez <b>Résultats</b> pour les tableaux et visualisations Shiny.</li>
          <li>Utilisez le <b>Concordancier</b> pour relire les motifs en contexte.</li>
          <li>Contrôlez <b>Historique</b> pour suivre les exécutions récentes.</li>
        </ol>

        <h3 style="color:#1f2937;">Avant un premier test</h3>
        <ul>
          <li>Commencez avec un petit corpus ou un sous-corpus.</li>
          <li>Gardez des paramètres simples : peu d'attributs, un minsup modéré, peu d'options avancées.</li>
          <li>Vérifiez que le corpus et les métadonnées sont cohérents avant de lancer une analyse longue.</li>
        </ul>

        <h3 style="color:#1f2937;">Repères utiles</h3>
        <ul>
          <li><b>Réglages</b> : préparation du corpus et configuration de l'analyse.</li>
          <li><b>Analyse</b> : exécution et suivi des logs.</li>
          <li><b>Résultats</b> : tableaux, AFC, clustering, spécificités.</li>
          <li><b>Concordancier</b> : vérification qualitative des occurrences.</li>
        </ul>
        """

    def _tutorials_html(self) -> str:
        return """
        <h2 style="color:#111827;">Tutoriels</h2>
        <p style="color:#4b5563;">
        Ces mini-guides décrivent des usages typiques de l'application.
        </p>

        <h3 style="color:#1f2937;">Tutoriel 1 : lancer une première analyse</h3>
        <ol>
          <li>Allez dans <b>Réglages</b>.</li>
          <li>Sélectionnez un corpus brut ou préparé.</li>
          <li>Choisissez un outil d'annotation et gardez des paramètres simples.</li>
          <li>Appliquez la configuration.</li>
          <li>Ouvrez <b>Analyse</b> puis cliquez sur <b>Lancer</b>.</li>
          <li>Attendez la fin complète avant d'ouvrir les résultats.</li>
        </ol>

        <h3 style="color:#1f2937;">Tutoriel 2 : ajouter ou corriger des métadonnées</h3>
        <ol>
          <li>Dans <b>Réglages</b>, ouvrez l'assistant de métadonnées.</li>
          <li>Choisissez le corpus concerné.</li>
          <li>Ajoutez les colonnes utiles.</li>
          <li>Utilisez le remplissage par lot ou la copie depuis la ligne précédente si besoin.</li>
          <li>Vérifiez la validation finale avant d'enregistrer.</li>
        </ol>

        <h3 style="color:#1f2937;">Tutoriel 3 : explorer un motif dans le concordancier</h3>
        <ol>
          <li>Terminez une analyse contenant des motifs.</li>
          <li>Ouvrez le <b>Concordancier</b>.</li>
          <li>Passez en mode <b>Motifs enregistrés</b>.</li>
          <li>Sélectionnez un motif dans la liste, puis lancez la recherche.</li>
          <li>Changez l'affichage entre <b>Motifs</b> et <b>Mots correspondants</b> selon votre besoin.</li>
        </ol>

        <h3 style="color:#1f2937;">Tutoriel 4 : lire les spécificités</h3>
        <ol>
          <li>Activez les spécificités dans les réglages d'analyse.</li>
          <li>Choisissez une métadonnée contrastive pertinente, par exemple <code>genre</code>.</li>
          <li>Lancez l'analyse.</li>
          <li>Dans <b>Résultats</b>, ouvrez l'onglet <b>Specifs</b>.</li>
          <li>Basculez entre les tables disponibles pour comparer les partitions.</li>
        </ol>
        """

    def _faq_html(self) -> str:
        return """
        <h2 style="color:#111827;">FAQ</h2>

        <h3 style="color:#1f2937;">Je n'obtiens aucun résultat, que vérifier ?</h3>
        <p>
        Vérifiez d'abord le <code>minsup</code>, les gaps, les attributs activés, le corpus choisi et la cohérence des fichiers d'entrée.
        </p>

        <h3 style="color:#1f2937;">Le GPU n'est pas détecté ou semble plus lent que prévu.</h3>
        <p>
        Vérifiez la disponibilité réelle du GPU, la compatibilité des bibliothèques installées et comparez les temps sur un corpus test avant de généraliser.
        </p>

        <h3 style="color:#1f2937;">Où retrouver les sorties d'une analyse ?</h3>
        <p>
        Les éléments importants se trouvent surtout dans <code>Data/analyses</code>, les dossiers <code>Patterns_results</code>, et les fichiers du dossier <code>logs</code>.
        </p>

        <h3 style="color:#1f2937;">Pourquoi le concordancier n'affiche pas ce que j'attends ?</h3>
        <p>
        Vérifiez le mode de recherche, le registry utilisé, le motif sélectionné et le type d'affichage choisi dans la page du concordancier.
        </p>

        <h3 style="color:#1f2937;">Pourquoi Shiny n'affiche rien ?</h3>
        <p>
        Vérifiez que l'analyse est terminée, que les TSV existent bien et que le dernier jeu de résultats chargé correspond à l'analyse attendue.
        </p>

        <h3 style="color:#1f2937;">À quoi sert le clustering interne ?</h3>
        <p>
        Il sert à fusionner des motifs proches pour réduire la redondance et rendre les tableaux plus lisibles.
        </p>

        <h3 style="color:#1f2937;">Puis-je travailler avec un corpus déjà annoté ?</h3>
        <p>
        Oui, selon le type d'entrée choisi dans les paramètres de l'application, vous pouvez utiliser des fichiers <code>.conllu</code> ou une archive préparée.
        </p>
        """
