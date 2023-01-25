#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import logging

from pdf_tool import PDF_Tool

from form import *
from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import Qt, QObject, QEvent
from PySide2.QtGui import QIcon, QMouseEvent

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TestListView(QListWidget):
    fileDropped = Signal(list)

    def __init__(self, parent=None):
        super(TestListView, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setIconSize(QSize(72, 72))
        self.file_paths = []
        self.files = []

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()

            self.files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()[-4:] == '.pdf']
            difference = list(set(self.files) - set(self.file_paths))
            if difference:
                self.fileDropped.emit(difference)
                self.file_paths.extend(difference)
        else:
            event.ignore()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.old_position = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.header.installEventFilter(self)
        self.ui.view.installEventFilter(self)
        self.setWindowIcon(QIcon('icons/pdf.ico'))

        # frameless window
        flags = Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowMaximizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(flags)

        # button click events
        self.ui.maximize_button.clicked.connect(self.window_full_screen)
        self.ui.exit_button.clicked.connect(self.close)
        self.ui.minimize_button.clicked.connect(self.showMinimized)
        self.ui.search_button.clicked.connect(self.get_files)
        self.ui.word_button.clicked.connect(self.extract_to_docx)
        self.ui.image_button.clicked.connect(self.extract_images)
        self.ui.text_botton.clicked.connect(self.extract_text)
        self.ui.view.fileDropped.connect(self.picture_dropped)
        self.ui.split_button.clicked.connect(self.split_files)
        self.ui.merge_button.clicked.connect(self.merge_files)

    # event filter
    def eventFilter(self, object: QObject, event: QMouseEvent) -> bool:
        if object.objectName() == 'header':
            if event.type() == QEvent.MouseButtonDblClick:
                self.window_full_screen()
                return True

            if event.type() == QEvent.MouseButtonPress:
                self.old_position = event.globalPos()
                return True

            if event.type() == QEvent.MouseMove:
                delta = QPoint(event.globalPos() - self.old_position)
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.old_position = event.globalPos()
                return True
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Backspace or key == Qt.Key_Delete:
                self.delete_from_list()
                return True

        return QMainWindow.eventFilter(self, object, event)

    def window_full_screen(self):
        self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)

    def get_files(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFiles)
        dlg.setNameFilters(["Pdf files (*.pdf)"])

        if dlg.exec_():
            self.ui.view.files = dlg.selectedFiles()
            difference = list(set(self.ui.view.files) - set(self.ui.view.file_paths))
            if difference:
                self.ui.view.fileDropped.emit(difference)
                self.ui.view.file_paths.extend(difference)

    def extract_to_docx(self):
        error = False
        if self.ui.view.file_paths:
            for index, file in enumerate(self.ui.view.file_paths):
                path = Path(file)
                output_path = '{}/{}-output/'.format(path.parent, path.stem)

                if not os.path.exists(output_path):
                    os.makedirs(output_path)

                docx_file = '{}{}.docx'.format(output_path, path.stem)
                try:
                    PDF_Tool.convert_to_docx(file, docx_file)
                except Exception as e:
                    logger.error(e)
                    error = True
                    QMessageBox.critical(self, 'Fehler!', 'Es ist ein Fehler aufgetreten')

            if not error:
                error = False
                QMessageBox.information(self, 'Info', "Alles erfolgreich erstellt")
        else:
            QMessageBox.warning(
                self,
                "Fehler!",
                "Es ist kein Pfad ausgewählt",
                defaultButton=QMessageBox.Ok,
            )

    def extract_images(self):
        error = False
        if self.ui.view.file_paths:
            for index, file in enumerate(self.ui.view.file_paths):
                path = Path(file)
                output_path = '{}/{}-output/images'.format(path.parent, path.stem)

                if not os.path.exists(output_path):
                    os.makedirs(output_path)

                try:
                    PDF_Tool.extract_images(file, output_path)
                except Exception as e:
                    logger.error(e)
                    error = True
                    QMessageBox.critical(self, 'Fehler!', 'Es ist ein Fehler aufgetreten')
            if not error:
                error = False
                QMessageBox.information(self, 'Info', "Alles erfolgreich erstellt")
        else:
            QMessageBox.warning(
                self,
                "Fehler!",
                "Es ist kein Pfad ausgewählt",
                defaultButton=QMessageBox.Ok,
            )

    def extract_text(self):
        error = False
        if self.ui.view.file_paths:
            for index, file in enumerate(self.ui.view.file_paths):
                path = Path(file)
                output_path = '{}/{}-output/'.format(path.parent, path.stem)

                text_file = '{}{}.txt'.format(output_path, path.stem)
                if os.path.exists(text_file):
                    os.remove(text_file)

                try:
                    PDF_Tool.convert_to_txt(file, text_file)
                except Exception as e:
                    error = True
                    logger.error(e)
                    QMessageBox.critical(self, 'Fehler!', 'Es ist ein Fehler aufgetreten')
            if not error:
                error = False
                QMessageBox.information(self, 'Info', "Alles erfolgreich erstellt")
        else:
            QMessageBox.warning(
                self,
                "Fehler!",
                "Es ist kein Pfad ausgewählt",
                defaultButton=QMessageBox.Ok,
            )

    def split_files(self):
        error = False
        if self.ui.view.file_paths:
            for index, file in enumerate(self.ui.view.file_paths):
                output_path = Path(file)
                output_path = '{}/{}-output/einzelne-seiten'.format(output_path.parent, output_path.stem)
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                try:
                    PDF_Tool.split_files(file, output_path)

                except Exception as e:
                    error = True
                    logger.error(e)
                    QMessageBox.critical(self, 'Fehler!', 'Es ist ein Fehler aufgetreten')

            if not error:
                error = False
                QMessageBox.information(self, 'Info', "Alles erfolgreich erstellt")

        else:
            QMessageBox.warning(
                self,
                "Fehler!",
                "Es ist kein Pfad ausgewählt",
                defaultButton=QMessageBox.Ok,
            )

    def merge_files(self):

        if self.ui.view.file_paths:
            path = Path(self.ui.view.file_paths[0])
            text, ok = QInputDialog.getText(self, 'Pdf-Files vereinen', 'Name eingeben')
            if ok:
                try:
                    output_path = '{}/{}.pdf'.format(str(path.parent), text)
                    PDF_Tool.merge_files(self.ui.view.file_paths, output_path)
                    QMessageBox.information(self, 'Info', "Alles erfolgreich erstellt")
                except Exception as e:
                    logger.error(e)
                    QMessageBox.critical(self, 'Fehler!', 'Es ist ein Fehler aufgetreten')

        else:
            QMessageBox.warning(
                self,
                "Fehler!",
                "Es ist kein Pfad ausgewählt",
                defaultButton=QMessageBox.Ok,
            )

    def delete_from_list(self):
        items = self.ui.view.selectedItems()
        if items:
            for index, item in reversed(list(enumerate(items))):
                item_text = str(self.ui.view.selectedItems()[index].text())
                list_index = self.ui.view.file_paths.index(item_text)
                self.ui.view.takeItem(list_index)
                self.ui.view.file_paths.remove(item_text)
        print(self.ui.view.file_paths)

    def picture_dropped(self, files):

        for url in files:
            if os.path.exists(url):
                icon = QIcon(url)
                pixmap = icon.pixmap(72, 72)
                icon = QIcon(pixmap)
                item = QListWidgetItem(url, self.ui.view)
                item.setIcon(icon)
                item.setStatusTip(url)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
