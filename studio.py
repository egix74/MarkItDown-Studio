import os
import sys
from pathlib import Path

from markitdown import MarkItDown
from PySide6.QtCore import QSettings, QThread, Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QListWidget, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)


def save_markdown(source, directory, content):
    payload = content.encode("utf-8")
    index = 1
    while True:
        suffix = "" if index == 1 else f" ({index})"
        target = directory / f"{source.stem}{suffix}.md"
        try:
            stream = target.open("xb")
        except FileExistsError:
            index += 1
            continue
        try:
            with stream:
                stream.write(payload)
        except OSError:
            target.unlink(missing_ok=True)
            raise
        return target


class Conversion(QThread):
    progress = Signal(int, int)
    report = Signal(str)
    result = Signal(str)

    def __init__(self, paths, recursive, destination):
        super().__init__()
        self.paths = paths
        self.recursive = recursive
        self.destination = destination
        self.scan_errors = 0

    def scan_error(self, error):
        self.scan_errors += 1
        self.report.emit(f"Errore di lettura · {error}")

    def scan(self):
        found = {}
        for path in self.paths:
            try:
                if path.is_dir():
                    for folder, folders, files in os.walk(path, onerror=self.scan_error):
                        if not self.recursive:
                            folders.clear()
                        for name in sorted(files):
                            candidate = Path(folder) / name
                            found.setdefault(os.path.normcase(str(candidate.resolve())), candidate)
                elif path.is_file():
                    found.setdefault(os.path.normcase(str(path.resolve())), path)
                else:
                    raise FileNotFoundError(str(path))
            except (OSError, RuntimeError) as error:
                self.scan_error(error)
        return list(found.values())

    def run(self):
        try:
            files = self.scan()
            self.progress.emit(0, max(1, len(files)))
            if not files:
                self.result.emit(f"Nessun file trovato. Errori di lettura: {self.scan_errors}.")
                return
            converter = MarkItDown(enable_plugins=False)
            converted = 0
            for index, source in enumerate(files, 1):
                try:
                    content = converter.convert_local(str(source)).text_content
                    target = save_markdown(source, self.destination or source.parent, content)
                    converted += 1
                    self.report.emit(f"Salvato · {source} → {target}")
                except Exception as error:
                    self.report.emit(f"Errore · {source} · {error}")
                self.progress.emit(index, len(files))
            self.result.emit(
                f"Convertiti {converted} di {len(files)} · "
                f"Errori di conversione: {len(files) - converted} · "
                f"Errori di lettura: {self.scan_errors}"
            )
        except Exception as error:
            self.result.emit(f"Conversione interrotta · {error}")


class Studio(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MarkItDown Studio")
        self.resize(850, 640)
        self.setAcceptDrops(True)
        self.settings = QSettings("MarkItDown Studio", "MarkItDown Studio")
        self.destination = self.settings.value("destination", "", type=str)
        self.worker = None
        self.light_palette = QApplication.palette()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("File e cartelle da convertire (puoi trascinarli qui)"))
        self.queue = QListWidget()
        self.queue.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.queue, 2)
        actions = QHBoxLayout()
        for label, callback in (
            ("Aggiungi file…", self.choose_files),
            ("Aggiungi cartella…", self.choose_folder),
            ("Rimuovi selezionati", self.remove_selected),
            ("Svuota", self.queue.clear),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.recursive = QCheckBox("Includi sottocartelle")
        self.recursive.setChecked(self.settings.value("recursive", False, type=bool))
        self.recursive.toggled.connect(lambda value: self.settings.setValue("recursive", value))
        layout.addWidget(self.recursive)

        options = QHBoxLayout()
        self.beside = QCheckBox("Salva accanto agli originali")
        self.beside.setChecked(self.settings.value("beside", True, type=bool))
        self.beside.toggled.connect(self.update_destination)
        options.addWidget(self.beside)
        self.destination_button = QPushButton("Scegli destinazione…")
        self.destination_button.clicked.connect(self.choose_destination)
        options.addWidget(self.destination_button)
        options.addStretch()
        options.addWidget(QLabel("Tema"))
        theme = QComboBox()
        theme.addItems(["Chiaro", "Scuro"])
        theme.setCurrentText(self.settings.value("theme", "Chiaro", type=str))
        theme.currentTextChanged.connect(self.apply_theme)
        options.addWidget(theme)
        layout.addLayout(options)
        self.destination_label = QLabel()
        self.destination_label.setWordWrap(True)
        self.destination_label.setTextFormat(Qt.TextFormat.PlainText)
        self.destination_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.destination_label)

        self.start_button = QPushButton("Converti in Markdown")
        self.start_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.start_button)
        self.bar = QProgressBar()
        self.bar.setFormat("%v / %m")
        layout.addWidget(self.bar)
        self.status = QLabel("Pronto")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Risultati ed errori per file")
        layout.addWidget(self.log, 1)
        self.apply_theme(theme.currentText())
        self.update_destination(self.beside.isChecked())

    def apply_theme(self, theme):
        self.settings.setValue("theme", theme)
        palette = QPalette(self.light_palette)
        if theme == "Scuro":
            for role, color in (
                ("Window", "#20242b"), ("Base", "#171a20"),
                ("AlternateBase", "#282e37"), ("Button", "#303743"),
                ("WindowText", "#edf0f5"), ("Text", "#edf0f5"),
                ("ButtonText", "#edf0f5"), ("Highlight", "#365fa0"),
                ("HighlightedText", "#ffffff"), ("PlaceholderText", "#aab4c3"),
            ):
                palette.setColor(getattr(QPalette.ColorRole, role), QColor(color))
            for role in ("WindowText", "Text", "ButtonText"):
                palette.setColor(QPalette.ColorGroup.Disabled,
                                 getattr(QPalette.ColorRole, role), QColor("#9299a5"))
        QApplication.setPalette(palette)

    def add_paths(self, paths):
        known = {os.path.normcase(self.queue.item(index).text())
                 for index in range(self.queue.count())}
        for value in paths:
            path = os.path.abspath(value)
            key = os.path.normcase(path)
            if key not in known:
                self.queue.addItem(path)
                known.add(key)

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Scegli file", self.settings.value("input", "", type=str), "Tutti i file (*)"
        )
        if files:
            self.settings.setValue("input", str(Path(files[0]).parent))
            self.add_paths(files)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Scegli cartella", self.settings.value("input", "", type=str)
        )
        if folder:
            self.settings.setValue("input", folder)
            self.add_paths([folder])

    def remove_selected(self):
        for item in self.queue.selectedItems():
            self.queue.takeItem(self.queue.row(item))

    def choose_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Scegli destinazione", self.destination)
        if folder:
            self.destination = folder
            self.settings.setValue("destination", folder)
            self.update_destination(False)

    def update_destination(self, beside):
        self.settings.setValue("beside", beside)
        self.destination_button.setEnabled(not beside)
        self.destination_label.setText(
            "" if beside else self.destination or "Seleziona una cartella di destinazione."
        )

    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_paths(url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile())
        event.acceptProposedAction()

    def start_conversion(self):
        paths = [Path(self.queue.item(index).text()) for index in range(self.queue.count())]
        if not paths:
            QMessageBox.information(self, self.windowTitle(), "Aggiungi almeno un file o una cartella.")
            return
        destination = None
        if not self.beside.isChecked():
            if not self.destination or not Path(self.destination).is_dir():
                QMessageBox.warning(self, self.windowTitle(), "Seleziona una destinazione esistente.")
                return
            destination = Path(self.destination)
        self.start_button.setEnabled(False)
        self.log.clear()
        self.status.setText("Ricerca dei file…")
        self.bar.setRange(0, 0)
        self.worker = Conversion(paths, self.recursive.isChecked(), destination)
        self.worker.report.connect(self.log.appendPlainText)
        self.worker.progress.connect(self.update_progress)
        self.worker.result.connect(self.status.setText)
        self.worker.finished.connect(self.finish_conversion)
        self.worker.start()

    def update_progress(self, done, total):
        self.bar.setRange(0, total)
        self.bar.setValue(done)
        self.status.setText(f"File elaborati: {done} di {total}")

    def finish_conversion(self):
        if self.bar.maximum() == 0:
            self.bar.setRange(0, 1)
            self.bar.setValue(0)
        self.worker.deleteLater()
        self.worker = None
        self.start_button.setEnabled(True)

    def closeEvent(self, event):
        if self.worker is not None:
            event.ignore()
            QMessageBox.information(self, self.windowTitle(), "Attendi la fine della conversione.")
        else:
            self.settings.sync()
            event.accept()


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--convert-local":
        source, destination = map(Path, sys.argv[2:])
        converter = MarkItDown(enable_plugins=False)
        content = converter.convert_local(str(source)).text_content
        save_markdown(source, destination, content)
        return 0
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    studio = Studio()
    studio.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
