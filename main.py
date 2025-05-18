import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QRectF, Slot
from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QDockWidget, QLabel, QMessageBox, QFileDialog, \
    QTreeView

from vcd_loader import VCDLoader


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.scene.addRect(QRectF(0, 0, 100, 100))
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.create_actions()
        self.create_menus()
        self.create_dock_windows()

        self.setWindowTitle("wavedbg")

    @Slot()
    def open_file(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Open file")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("VCD file (*.vcd)")
        if dialog.exec():
            file_name = dialog.selectedFiles()[0]
            metadata, hier_model = VCDLoader.load(file_name)
            self._hierview.setModel(hier_model)

    @Slot()
    def about(self):
        QMessageBox.about(self, "About wavedbg", "wavedbg 0.0.1")

    def create_actions(self):
        self._open_action = QAction("&Open", self, shortcut="Ctrl+O",
                                    statusTip="Open", triggered=self.open_file)
        self._quit_action = QAction("&Quit", self, shortcut="Ctrl+Q",
                                    statusTip="Quit the application", triggered=self.close)
        self._about_action = QAction("&About", self, triggered=self.about)

    def create_menus(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self._open_action)
        self._file_menu.addAction(self._quit_action)
        self._edit_menu = self.menuBar().addMenu("&Edit")
        self._help_menu = self.menuBar().addMenu("&Help")
        self._help_menu.addAction(self._about_action)

    def create_dock_windows(self):
        dock = QDockWidget("Hierarchy", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._hierview = QTreeView()
        dock.setWidget(self._hierview)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        dock = QDockWidget("Signals", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        dock.setWidget(QLabel("Dock 2"))
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
