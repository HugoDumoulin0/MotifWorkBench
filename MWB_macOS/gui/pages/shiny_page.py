"""
Page Shiny intégrée.
@jcharlesDS (2026)
"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QDesktopServices

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, ACCENT
from gui.core.shiny_runner import (
    shiny_url, stop_shiny, is_shiny_running, wait_for_shiny,
    launch_shiny_embedded, latest_analysis_root,
    list_available_shiny_analyses, prepare_analysis_for_shiny
)

class ShinyOperation(QThread):
    ready = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, analysis_root, host, port, stop=False, parent=None):
        super().__init__(parent)
        self.analysis_root = analysis_root
        self.host = host
        self.port = port
        self.stop = stop

    def run(self):
        try:
            if self.stop:
                stop_shiny(self.host, self.port)
                self.ready.emit("")
                return
            root = Path(self.analysis_root)
            json_path = prepare_analysis_for_shiny(root)
            launch_shiny_embedded(json_path, self.host, self.port, analysis_root=root)
            if not wait_for_shiny(self.host, self.port, should_stop=self.isInterruptionRequested):
                stop_shiny(self.host, self.port)
                if self.isInterruptionRequested():
                    return
                raise RuntimeError(f"Shiny n'a pas démarré. Consultez {root / 'shiny.log'}.")
            self.ready.emit(str(root))
        except Exception as exc:
            self.failed.emit(str(exc))


class ShinyPage(BasePage):
    """
    Page affichant l'interface Shiny intégrée.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._shiny_host = "127.0.0.1"
        self._shiny_port = 3838
        self._operation = None
        self._pending_root = None
        self._displayed_root = None
        self._build_ui()
        self._refresh_analyses(preferred_root=latest_analysis_root())
    
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
        
        selection = self.make_group("Analyse à visualiser")
        selection_layout = QHBoxLayout(selection)
        self._analysis_select = QComboBox()
        self._analysis_select.setMinimumWidth(350)
        self._analysis_select.currentIndexChanged.connect(self._selection_changed)
        selection_layout.addWidget(self._analysis_select, 1)
        self._btn_refresh = QPushButton("Actualiser")
        self._btn_refresh.clicked.connect(lambda: self._refresh_analyses())
        selection_layout.addWidget(self._btn_refresh)
        layout.addWidget(selection)

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
    
    def _selected_root(self):
        value = self._analysis_select.currentData()
        return Path(value) if value else None

    def _refresh_analyses(self, preferred_root=None):
        selected = preferred_root or self._selected_root()
        selected = str(Path(selected).resolve()) if selected else None
        self._analysis_select.blockSignals(True)
        self._analysis_select.clear()
        try:
            for entry in list_available_shiny_analyses():
                label = f"{entry['analysis_group_name']} — {entry['config_id']}"
                self._analysis_select.addItem(label, entry["analysis_root"])
            index = self._analysis_select.findData(selected)
            if index >= 0:
                self._analysis_select.setCurrentIndex(index)
        finally:
            self._analysis_select.blockSignals(False)
        self._btn_launch.setEnabled(self._analysis_select.count() > 0 and self._operation is None)
        if self._displayed_root != self._selected_root():
            self._displayed_root = None
            self._btn_external.setEnabled(False)
            if self._view is not None:
                self._view.setHtml("")
        if not self._analysis_select.count():
            self._status.setText("Aucun tableau de résultats disponible.")

    def _selection_changed(self):
        root = self._selected_root()
        if root is None:
            return
        if is_shiny_running(self._shiny_host, self._shiny_port):
            self._launch_shiny_server()
        else:
            self._displayed_root = None
            self._btn_external.setEnabled(False)
            self._status.setText(f"Analyse sélectionnée — {root.name}")
            if self._view is not None:
                self._view.setHtml("")

    def open_analysis(self, analysis_root):
        """Sélectionne les résultats demandés depuis l'historique."""
        root = Path(analysis_root).resolve()
        if self._operation is not None:
            self._pending_root = root
            return
        self._refresh_analyses(preferred_root=root)
        if self._selected_root() != root:
            QMessageBox.warning(self, "Résultats indisponibles",
                                "Les tableaux de cette analyse sont introuvables.")
            return
        self._launch_shiny_server()

    def _set_busy(self, busy):
        for control in (self._analysis_select, self._btn_refresh, self._btn_launch,
                        self._btn_reload, self._btn_stop, self._btn_external):
            control.setEnabled(not busy)
        if not busy:
            self._btn_launch.setEnabled(self._analysis_select.count() > 0)
            self._btn_external.setEnabled(self._displayed_root == self._selected_root()
                                          and self._displayed_root is not None)

    def _launch_shiny_server(self):
        root = self._selected_root()
        if root is None or self._operation is not None:
            return
        self._displayed_root = None
        self._status.setText(f"Ouverture de {root.name} dans Shiny…")
        if self._view is not None:
            self._view.setHtml("")
        self._start_operation(root)

    def _start_operation(self, root=None, stop=False):
        self._set_busy(True)
        self._operation = ShinyOperation(root, self._shiny_host, self._shiny_port,
                                         stop=stop, parent=self)
        self._operation.ready.connect(self._operation_ready)
        self._operation.failed.connect(self._operation_failed)
        self._operation.finished.connect(self._operation_finished)
        self._operation.start()

    def _operation_ready(self, analysis_root):
        if not analysis_root:
            self._displayed_root = None
            self._status.setText("Shiny arrêté.")
            if self._view is not None:
                self._view.setHtml("")
            return
        self._displayed_root = Path(analysis_root)
        self._status.setText(f"Analyse affichée — {Path(analysis_root).name}")
        if self._view is not None:
            self._view.setUrl(QUrl(self.shiny_url()))

    def _operation_failed(self, message):
        self._status.setText("Erreur lors de l'ouverture des résultats.")
        QMessageBox.critical(self, "Erreur Shiny", message)

    def _operation_finished(self):
        operation = self._operation
        self._operation = None
        operation.deleteLater()
        self._set_busy(False)
        if self._pending_root is not None:
            root = self._pending_root
            self._pending_root = None
            self.open_analysis(root)

    def _reload_view(self):
        self._launch_shiny_server()

    def _stop_shiny_server(self):
        if self._operation is None:
            self._status.setText("Arrêt de Shiny…")
            self._start_operation(stop=True)

    def _open_external(self):
        if self._displayed_root == self._selected_root() and self._displayed_root is not None:
            QDesktopServices.openUrl(QUrl(self.shiny_url()))

    def sync_status(self):
        if self._operation is None and not is_shiny_running():
            self._status.setText("Shiny non démarré.")

    def refresh_from_latest_analysis(self, _results=None):
        root = latest_analysis_root()
        if root is None:
            return
        if self._operation is not None:
            self._pending_root = root
            return
        was_running = is_shiny_running()
        self._refresh_analyses(preferred_root=root)
        if was_running:
            self._launch_shiny_server()
        else:
            self._status.setText(f"Nouvelle analyse disponible — {root.name}")

    def load_shiny_url(self):
        self._refresh_analyses()
        if is_shiny_running() and self._operation is None:
            self._launch_shiny_server()

    def showEvent(self, event):
        super().showEvent(event)
        if self._operation is None:
            self._refresh_analyses()

    def shutdown(self):
        if self._operation is not None:
            self._operation.requestInterruption()
            self._operation.wait(7000)
        stop_shiny(self._shiny_host, self._shiny_port)
