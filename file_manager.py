import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget,
    QPushButton, QListWidget, QMenu, QAction, QMessageBox, QLineEdit, QInputDialog
)
from PyQt5.QtCore import Qt

class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Python File Manager')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText("Enter directory path or click 'Open Directory'")

        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.open_context_menu)
        self.list_widget.itemDoubleClicked.connect(self.navigate)

        open_btn = QPushButton('Open Directory')
        open_btn.clicked.connect(self.open_directory)

        copy_btn = QPushButton('Copy Selected')
        copy_btn.clicked.connect(self.copy_selected)

        delete_btn = QPushButton('Delete Selected')
        delete_btn.clicked.connect(self.delete_selected)

        rename_btn = QPushButton('Rename Selected')
        rename_btn.clicked.connect(self.rename_selected)

        layout.addWidget(self.path_input)
        layout.addWidget(open_btn)
        layout.addWidget(copy_btn)
        layout.addWidget(delete_btn)
        layout.addWidget(rename_btn)
        layout.addWidget(self.list_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.copied_file = None
        self.cut_file = None

        self.history = []

        self.show_drives()

    def show_drives(self):
        """Display all drives in the system."""
        self.list_widget.clear()
        drives = [f"{d}:/" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:/")]
        for drive in drives:
            self.list_widget.addItem(drive)
        self.path_input.clear()
        self.history = []

    def navigate(self, item):
        """Navigate into a directory or drive."""
        path = item.text()
        if os.path.isdir(path):
            current_path = self.path_input.text()
            if current_path:
                self.history.append(current_path)
            self.path_input.setText(path)
            self.list_files(path)

    def open_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if directory:
            current_path = self.path_input.text()
            if current_path:
                self.history.append(current_path)
            self.path_input.setText(directory)
            self.list_files(directory)

    def list_files(self, directory):
        self.list_widget.clear()
        try:
            self.list_widget.addItem("...")
            for filename in os.listdir(directory):
                self.list_widget.addItem(os.path.join(directory, filename))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list files: {e}")

    def open_context_menu(self, position):
        menu = QMenu()
        copy_action = QAction('Copy', self)
        cut_action = QAction('Cut', self)
        paste_action = QAction('Paste', self)
        delete_action = QAction('Delete', self)
        rename_action = QAction('Rename', self)

        copy_action.triggered.connect(self.copy_selected)
        cut_action.triggered.connect(self.cut_selected)
        paste_action.triggered.connect(self.paste_selected)
        delete_action.triggered.connect(self.delete_selected)
        rename_action.triggered.connect(self.rename_selected)

        menu.addAction(copy_action)
        menu.addAction(cut_action)
        menu.addAction(paste_action)
        menu.addAction(delete_action)
        menu.addAction(rename_action)

        menu.exec_(self.list_widget.viewport().mapToGlobal(position))

    def get_selected_path(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            return selected_items[0].text()
        return None

    def copy_selected(self):
        self.copied_file = self.get_selected_path()
        self.cut_file = None
        if self.copied_file:
            QMessageBox.information(self, "Copied", f"Copied: {self.copied_file}")

    def cut_selected(self):
        self.cut_file = self.get_selected_path()
        self.copied_file = None
        if self.cut_file:
            QMessageBox.information(self, "Cut", f"Cut: {self.cut_file}")

    def paste_selected(self):
        dest_directory = self.path_input.text()
        if self.copied_file:
            dest_path = os.path.join(dest_directory, os.path.basename(self.copied_file))
            try:
                shutil.copy(self.copied_file, dest_path)
                self.list_files(dest_directory)
                QMessageBox.information(self, "Pasted", f"Pasted: {self.copied_file} to {dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to paste file: {e}")
        elif self.cut_file:
            dest_path = os.path.join(dest_directory, os.path.basename(self.cut_file))
            try:
                shutil.move(self.cut_file, dest_path)
                self.list_files(dest_directory)
                self.cut_file = None
                QMessageBox.information(self, "Moved", f"Moved: {self.cut_file} to {dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to move file: {e}")
        else:
            QMessageBox.information(self, "No File", "No file to paste")

    def delete_selected(self):
        filepath = self.get_selected_path()
        if filepath:
            reply = QMessageBox.question(
                self, "Delete File", f"Are you sure you want to delete {filepath}?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    os.remove(filepath)
                    self.list_files(self.path_input.text())
                    QMessageBox.information(self, "Success", "File deleted successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete file: {e}")

    def rename_selected(self):
        filepath = self.get_selected_path()
        if filepath:
            new_name, ok = QInputDialog.getText(self, "Rename File", "Enter new file name:")
            if ok and new_name:
                new_path = os.path.join(os.path.dirname(filepath), new_name)
                try:
                    os.rename(filepath, new_path)
                    self.list_files(self.path_input.text())
                    QMessageBox.information(self, "Success", "File renamed successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to rename file: {e}")

    def navigate(self, item):
        """Navigate into a directory or drive, or go back if the three-dot button is clicked."""
        path = item.text()
        if path == "...":
            self.go_back()
        elif os.path.isdir(path):
            current_path = self.path_input.text()
            if current_path:
                self.history.append(current_path)
            self.path_input.setText(path)
            self.list_files(path)

    def go_back(self):
        """Go back to the previous directory."""
        if self.history:
            previous_path = self.history.pop()
            self.path_input.setText(previous_path)
            self.list_files(previous_path)
        else:
            self.show_drives()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileManager()
    window.show()
    sys.exit(app.exec_())
