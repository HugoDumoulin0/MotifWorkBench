"""
Page Shiny intégrée.
@jcharlesDS (2026)
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, ACCENT
from gui.core.shiny_runner import (
    shiny_url, stop_shiny, is_shiny_running, wait_for_shiny,
    launch_shiny_embedded, last_results_json_path
)

class ShinyPage(BasePage):
    """
    Page affichant l'interface Shiny intégrée.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._shiny_host = "127.0.0.1"
        self._shiny_port = 3838
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
            "Visualisations",
            "Interface interactive embarquée"
        ))
        
        controls = self.make_group("Contrôles")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setSpacing(8)
        
        self._btn_launch = self._action_btn("Lancer")
        self._btn_launch.clicked.connect(self._launch_shiny_server)
        controls_layout.addWidget(self._btn_launch)
        
        self._btn_reload = self._action_btn("Recharger")
        self._btn_reload.clicked.connect(self._reload_view)
        controls_layout.addWidget(self._btn_reload)
        
        self._btn_stop = self._action_btn("Arrêter")
        self._btn_stop.clicked.connect(self._stop_shiny_server)
        controls_layout.addWidget(self._btn_stop)
        
        self._btn_external = self._action_btn("Ouvrir dans le navigateur")
        self._btn_external.clicked.connect(self._open_external)
        controls_layout.addWidget(self._btn_external)
        
        controls_layout.addStretch()
        layout.addWidget(controls)
        
        self._status = QLabel("Shiny non démarré.")
        self._status.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        self._status.setFont(QFont("Helvetica Neue", 11))
        layout.addWidget(self._status)
        
        viewer_group = self.make_group("Vue embarquée")
        viewer_layout = QVBoxLayout(viewer_group)
        
        if QWebEngineView is None:
            self._view = None
            lbl = QLabel("PyQt6 WebEngine non disponible.\nL'affichage embarqué est désactivé.")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: #b91c1c; background-color: transparent;")
            viewer_layout.addWidget(lbl)
        else:
            self._view = QWebEngineView()
            self._view.setMinimumHeight(750)
            # Corriger le style du menu contextuel pour qu'il soit lisible
            self._view.setStyleSheet("""
                QMenu {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    padding: 4px;
                }
                QMenu::item {
                    background-color: transparent;
                    color: #000000;
                    padding: 6px 24px 6px 8px;
                }
                QMenu::item:selected {
                    background-color: #0078d4;
                    color: #ffffff;
                }
                QMenu::item:disabled {
                    color: #999999;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #e0e0e0;
                    margin: 4px 0px;
                }
            """)
            viewer_layout.addWidget(self._view)
            
        layout.addWidget(viewer_group)
        layout.addStretch()
        
        scroll.setWidget(content)
        outer.addWidget(scroll)
    
    def _action_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Helvetica Neue", 11))
        btn.setStyleSheet(f"""
            QPushButton {{
                color: #ffffff;
                background-color: {ACCENT};
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:pressed {{
                background-color: #2a2a4a;
            }}
        """)
        return btn
    
    def shiny_url(self) -> str:
        return shiny_url(self._shiny_host, self._shiny_port)
    
    def _launch_shiny_server(self):
        """Lance le serveur Shiny et affiche la vue."""
        json_path = last_results_json_path()
        if not json_path.exists():
            QMessageBox.warning(
                self,
                "Données manquantes",
                "Aucun JSON Shiny détecté. Lance d'abord une analyse terminée avec succès."
            )
            return
        
        try:
            self._status.setText("Lancement de Shiny en cours...")
            launch_shiny_embedded(
                json_path, self._shiny_host, self._shiny_port
            )
            ready = wait_for_shiny(self._shiny_host, self._shiny_port, timeout_s=12.0)
            if ready:
                self._status.setText("Shiny actif. Vue chargée.")
                if self._view is not None:
                    self._view.setUrl(QUrl(self.shiny_url()))
            else:
                self._status.setText("Shiny en cours de démarrage...")
                if self._view is not None:
                    self._view.setUrl(QUrl(self.shiny_url()))
        except Exception as exc:
            self._status.setText("Erreur lors du lancement de Shiny.")
            QMessageBox.critical(self, "Erreur Shiny", f"Impossible de lancer Shiny:\n{exc}")
    
    def _reload_view(self):
        try:
            if self._view is None:
                QMessageBox.warning(self, "WebEngine non disponible", "L'affichage embarqué n'est pas disponible car PyQt6 WebEngine n'est pas installé.")
                return
            self._view.setUrl(QUrl(self.shiny_url()))
            self._status.setText("Vue Shiny rechargée.")
        except Exception as e:
            self._status.setText("Erreur lors du rechargement.")
            QMessageBox.warning(self, "Erreur", f"Erreur lors du rechargement de la vue:\n{str(e)}")
    
    def _stop_shiny_server(self):
        try:
            if not is_shiny_running(self._shiny_host, self._shiny_port):
                self._status.setText("Shiny n'est pas en cours d'exécution.")
                QMessageBox.information(self, "Shiny", "Le serveur Shiny n'est pas en cours d'exécution.")
                return
            
            stop_shiny(self._shiny_host, self._shiny_port)
            self._status.setText("Shiny arrêté.")
            if self._view is not None:
                self._view.setHtml("<html><body style='background-color: #13131f; color: #ffffff; font-family: Helvetica Neue; text-align: center; padding-top: 100px;'><h2>Serveur Shiny arrêté</h2><p>Cliquez sur 'Lancer' à nouveau pour le redémarrer.</p></body></html>")
            QMessageBox.information(self, "Shiny", "Le serveur Shiny a été arrêté avec succès.")
        except Exception as e:
            self._status.setText("Erreur lors de l'arrêt de Shiny.")
            QMessageBox.warning(self, "Erreur", f"Une erreur s'est produite lors de l'arrêt du serveur Shiny:\n{str(e)}")
    
    def _open_external(self):
        QDesktopServices.openUrl(QUrl(self.shiny_url()))
    
    def sync_status(self):
        if is_shiny_running(self._shiny_host, self._shiny_port):
            self._status.setText("Shiny en cours d'exécution.")
        else:
            self._status.setText("Shiny non démarré.")

    def refresh_from_latest_analysis(self, _results: dict | None = None):
        """Met à jour la page Résultats après une nouvelle analyse."""
        try:
            if is_shiny_running(self._shiny_host, self._shiny_port):
                if self._view is not None:
                    self._view.reload()
                self._status.setText("Nouveaux résultats détectés. Vue Shiny actualisée.")
            else:
                self._status.setText("Nouvelle analyse disponible. Lancez Shiny pour afficher les derniers résultats.")
        except Exception as exc:
            self._status.setText(f"Erreur lors de l'actualisation de Shiny : {exc}")

    def load_shiny_url(self):
        """Charge automatiquement l'URL Shiny dans la vue embarquée si le serveur est actif."""
        try:
            if self._view is None:
                return
            
            # Attendre un peu que le serveur soit prêt si nécessaire
            if not is_shiny_running(self._shiny_host, self._shiny_port):
                self._status.setText("Attente du serveur Shiny...")
                # Attendre jusqu'à 5 secondes que le serveur réponde
                if not wait_for_shiny(self._shiny_host, self._shiny_port, timeout_s=5.0):
                    self._status.setText("Le serveur Shiny ne répond pas encore.")
                    return
            
            # Charger l'URL
            self._view.setUrl(QUrl(self.shiny_url()))
            self._status.setText("Shiny actif - vue chargée.")
        except Exception as e:
            self._status.setText("Erreur lors du chargement de Shiny.")
            print(f"Erreur dans load_shiny_url: {e}")
