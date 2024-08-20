import sys
import os
import shutil
import subprocess
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

        # Directory path input
        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText("Enter directory path or click 'Open Directory'")

        # List widget to display files and folders
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.open_context_menu)
        self.list_widget.itemDoubleClicked.connect(self.navigate)

        # Buttons
        open_btn = QPushButton('Open Directory')
        open_btn.clicked.connect(self.open_directory)

        # Add widgets to layout
        layout.addWidget(self.path_input)
        layout.addWidget(open_btn)
        layout.addWidget(self.list_widget)

        # Set the main layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Variables to hold copied/cut file paths
        self.copied_file = None
        self.cut_file = None

        # Stack to store navigation history
        self.history = []

        # Show drives on startup
        self.show_drives()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_F2:
            self.rename_selected()
        elif event.key() == Qt.Key_Delete:
            if event.modifiers() == Qt.ShiftModifier:
                self.permanently_delete_selected()
            else:
                self.delete_selected()
        super().keyPressEvent(event)

    def show_drives(self):
        """Display all drives in the system."""
        self.list_widget.clear()
        drives = [f"{d}:/" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:/")]
        for drive in drives:
            self.list_widget.addItem(drive)
        self.path_input.clear()
        self.history = []  # Clear history when showing drives

    def navigate(self, item):
        """Navigate into a directory or drive, or go back if the three-dot button is clicked."""
        path = item.text()
        if path == "...":
            self.go_back()
        elif os.path.isdir(path):
            current_path = self.path_input.text()
            if current_path:
                self.history.append(current_path)  # Add current path to history before navigating
            self.path_input.setText(path)
            self.list_files(path)
        else:
            self.open_file(path)

    def open_file(self, filepath):
        """Open the selected file with the default application."""
        try:
            subprocess.Popen([filepath], shell=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def open_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if directory:
            current_path = self.path_input.text()
            if current_path:
                self.history.append(current_path)  # Add current path to history before opening new directory
            self.path_input.setText(directory)
            self.list_files(directory)

    def list_files(self, directory):
        self.list_widget.clear()
        try:
            # Add a three-dot item to go back to the previous directory
            self.list_widget.addItem("...")
            for filename in os.listdir(directory):
                self.list_widget.addItem(os.path.join(directory, filename))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list files: {e}")

    def open_context_menu(self, position):
        menu = QMenu()
        open_action = QAction('Open', self)
        copy_action = QAction('Copy', self)
        cut_action = QAction('Cut', self)
        paste_action = QAction('Paste', self)
        delete_action = QAction('Delete', self)
        rename_action = QAction('Rename', self)
        create_file_action = QAction('Create New File', self)

        open_action.triggered.connect(self.open_selected)
        copy_action.triggered.connect(self.copy_selected)
        cut_action.triggered.connect(self.cut_selected)
        paste_action.triggered.connect(self.paste_selected)
        delete_action.triggered.connect(self.delete_selected)
        rename_action.triggered.connect(self.rename_selected)
        create_file_action.triggered.connect(self.create_new_file)

        menu.addAction(open_action)
        menu.addAction(copy_action)
        menu.addAction(cut_action)
        menu.addAction(paste_action)
        menu.addAction(delete_action)
        menu.addAction(rename_action)
        menu.addAction(create_file_action)

        menu.exec_(self.list_widget.viewport().mapToGlobal(position))

    def get_selected_path(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            return selected_items[0].text()
        return None

    def open_selected(self):
        filepath = self.get_selected_path()
        if filepath:
            self.open_file(filepath)

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

    def permanently_delete_selected(self):
        filepath = self.get_selected_path()
        if filepath:
            reply = QMessageBox.question(
                self, "Permanently Delete File", f"Are you sure you want to permanently delete {filepath}?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    os.remove(filepath)
                    self.list_files(self.path_input.text())
                    QMessageBox.information(self, "Success", "File permanently deleted")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to permanently delete file: {e}")

    def rename_selected(self):
        filepath = self.get_selected_path()
        if filepath:
            # Extract the original file extension
            file_dir = os.path.dirname(filepath)
            file_name, file_extension = os.path.splitext(os.path.basename(filepath))
            
            # Prompt the user for the new name without the extension
            new_name, ok = QInputDialog.getText(self, "Rename File", "Enter new file name (without extension):", text=file_name)
            
            if ok and new_name:
                new_path = os.path.join(file_dir, new_name + file_extension)  # Add the original extension back
                try:
                    os.rename(filepath, new_path)
                    self.list_files(self.path_input.text())
                    QMessageBox.information(self, "Success", "File renamed successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to rename file: {e}")

    def create_new_file(self):
        """Create a new file with a specified format."""
        file_formats = ['.txt', '.csv', '.md', '.py', '.html', '.json', '.xml', '.yaml', '.java', '.cpp', '.c', '.sh', '.bat']
        new_file_name, ok = QInputDialog.getText(self, "Create New File", "Enter new file name (without extension):")
        if ok and new_file_name:
            file_format, ok = QInputDialog.getItem(self, "Select File Format", "Choose file format:", file_formats, 0, False)
            if ok:
                directory = self.path_input.text()
                file_path = os.path.join(directory, new_file_name + file_format)
                try:
                    with open(file_path, 'w') as f:
                        pass  # Create an empty file
                    self.list_files(directory)
                    QMessageBox.information(self, "Success", f"File created successfully: {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create file: {e}")

    def go_back(self):
        """Go back to the previous directory in history."""
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
