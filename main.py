import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QRectF, Slot
from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QDockWidget, QMessageBox, QFileDialog, \
    QTreeView, QListView

from vcd_loader import VCDLoader, VCDVarsListModel


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
            self._hierview.selectionModel().currentChanged.connect(self.select_hier)

    @Slot()
    def select_hier(self, current, previous):
        if current.isValid():
            var_model = VCDVarsListModel(current.internalPointer().vars)
            self._signalview.setModel(var_model)
            self._signalview.selectionModel().currentChanged.connect(self.select_signal)
        else:
            self._signalview.setModel(None)

    @Slot()
    def select_signal(self, current, previous):
        if current.isValid():
            var = current.internalPointer()
            print(var)

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
        self._hierview.setHeaderHidden(True)
        dock.setWidget(self._hierview)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        dock = QDockWidget("Signals", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._signalview = QListView()
        dock.setWidget(self._signalview)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
