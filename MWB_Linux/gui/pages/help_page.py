"""
Page d'aide de l'application.
Structure en quatre onglets : aide rapide, tutoriels, FAQ et manuel.
@jcharlesDS (2026)
"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QTabWidget,
    QTextBrowser,
    QSizePolicy,
)
from PyQt6.QtGui import QFont

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, TEXT_SECONDARY


class HelpPage(BasePage):
    """Page d'aide structurée avec onglets et lecture du manuel Markdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._manual_path = self._project_root / "docs" / "user_manual.md"
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

        layout.addWidget(self.make_title(
            "Aide",
            "Repères rapides, tutoriels, réponses aux questions fréquentes et manuel complet."
        ))

        intro = QLabel(
            "Cette page rassemble l'essentiel pour prendre en main MotifWorkBench, "
            "résoudre les questions courantes et lire le manuel directement dans l'application."
        )
        intro.setWordWrap(True)
        intro.setFont(QFont("Segoe UI", 10))
        intro.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent;")
        layout.addWidget(intro)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setMinimumHeight(620)
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #e5e7eb;
                background: #ffffff;
                border-radius: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: #f3f4f6;
                color: {TEXT_PRIMARY};
                padding: 10px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: #ffffff;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background: #e5e7eb;
            }}
        """)

        tabs.addTab(self._build_rich_text_tab(self._quick_help_markdown()), "Aide rapide")
        tabs.addTab(self._build_rich_text_tab(self._tutorials_markdown()), "Tutoriels")
        tabs.addTab(self._build_rich_text_tab(self._faq_markdown()), "FAQ")
        tabs.addTab(self._build_manual_tab(), "Manuel")

        layout.addWidget(tabs, 1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _make_text_browser(self) -> QTextBrowser:
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setReadOnly(True)
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: #ffffff;
                color: {TEXT_PRIMARY};
                border: none;
                padding: 12px;
                font-size: 10pt;
                line-height: 1.45;
            }}
        """)
        return browser

    def _build_rich_text_tab(self, markdown_text: str) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        browser = self._make_text_browser()
        browser.setMarkdown(markdown_text)
        layout.addWidget(browser, 1)
        return tab

    def _build_manual_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        info = QLabel(f"Source : {self._manual_path}")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent; font-size: 9pt; font-style: italic;")
        layout.addWidget(info)

        browser = self._make_text_browser()
        browser.setMarkdown(self._load_manual_markdown())
        layout.addWidget(browser, 1)
        return tab

    def _load_manual_markdown(self) -> str:
        if not self._manual_path.exists():
            return (
                "# Manuel introuvable\n\n"
                "Le fichier `docs/user_manual.md` n'a pas été trouvé dans le projet."
            )

        try:
            return self._manual_path.read_text(encoding="utf-8")
        except Exception as exc:
            return (
                "# Erreur de lecture\n\n"
                "Impossible de charger `docs/user_manual.md`.\n\n"
                f"Détail : `{exc}`"
            )

    def _quick_help_markdown(self) -> str:
        return """
# Aide rapide

## Parcours conseillé

1. Ouvrir **Réglages**.
2. Choisir le **corpus** et vérifier les **métadonnées**.
3. Garder des paramètres simples pour un premier essai.
4. Aller dans **Analyse** et lancer un test.
5. Consulter **Résultats**, **Concordancier** et **Historique**.

## Premier test recommandé

- un corpus de petite taille ;
- un `minsup` modéré ;
- peu d'attributs linguistiques activés ;
- pas trop d'options avancées en même temps.

## Où regarder en cas de doute

- **Analyse** : progression et logs ;
- **Historique** : résumé des exécutions ;
- **Paramètres** : dossiers, logs, cache des modèles ;
- **Aide** : tutoriels, FAQ et manuel.

## À retenir

- commencez simple ;
- comparez plusieurs profils ;
- relisez toujours les motifs en contexte.
"""

    def _tutorials_markdown(self) -> str:
        return """
# Tutoriels

## 1. Lancer une première analyse

1. Ouvrir **Réglages**.
2. Sélectionner un dossier de corpus.
3. Vérifier la présence de `metadata.tsv`.
4. Choisir la langue et l'outil d'annotation.
5. Garder un `minsup`, un `gap min`, un `gap max` et un `itemset min` prudents.
6. Cliquer sur **Appliquer la configuration**.
7. Aller dans **Analyse** puis lancer.

## 2. Utiliser le concordancier

1. Ouvrir la page **Concordancier**.
2. Choisir le mode :
   - **Recherche libre**
   - **Motifs enregistrés**
   - **CQP**
3. Lancer la recherche.
4. Filtrer les résultats avec les métadonnées si nécessaire.
5. Exporter en CSV si vous voulez conserver la table.

## 3. Lire les spécificités dans Shiny

1. Activer **Calculer les spécificités** dans les réglages.
2. Lancer l'analyse jusqu'au bout.
3. Ouvrir **Résultats** puis lancer Shiny.
4. Aller dans l'onglet **Specifs**.
5. Choisir la métadonnée et le TSV à afficher.

## 4. Réutiliser des données préparées

Dans **Réglages > Corpus et métadonnées**, vous pouvez choisir un autre type d'entrée :

- **Corpus brut (.txt)** ;
- **Corpus déjà annoté (.conllu)** ;
- **Archive préparée (.zip)**.

Cela permet d'éviter de refaire certaines étapes coûteuses.
"""

    def _faq_markdown(self) -> str:
        return """
# FAQ

## Je n'ai aucun résultat. Que vérifier ?

- le corpus sélectionné ;
- les paramètres de motifs ;
- les attributs linguistiques activés ;
- les logs dans la page **Analyse**.

## Le GPU n'apparaît pas.

L'application masque le GPU si elle ne le détecte pas. Vérifiez :

- l'installation de `torch` compatible ;
- les pilotes CUDA ;
- la mémoire réellement disponible.

## Où sont les fichiers produits ?

En général dans :

- `Data/analyses/...`
- `Patterns_results`
- `Clustering_results`
- `logs`

## Pourquoi relancer la même analyse peut aller plus vite ?

Parce que certaines sorties peuvent être réutilisées :

- fichiers annotés ;
- `underscore_fix` ;
- résultats déjà calculés selon la configuration.

## Je ne comprends pas un motif.

Passez par le **Concordancier** :

1. sélectionnez le motif ;
2. choisissez le mode d'affichage ;
3. relisez plusieurs occurrences dans leur contexte.

## Les spécificités ne s'affichent pas.

Vérifiez que :

- l'option est activée dans les réglages ;
- une métadonnée contrastive existe ;
- les TSV de spécificités ont bien été générés.
"""
