import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDialog, QDialogButtonBox, QTabWidget,
    QPushButton, QTextEdit
)
from PySide6.QtGui import QPixmap, QCursor, QIcon
from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView

class LightboxWindow(QDialog):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Lightbox")
        self.resize(768, 768)
        layout = QVBoxLayout()
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)
        self.setLayout(layout)

class LoraImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LORAS")
        self.resize(600, 800)

        self.target_size = 150
        # Используем относительный путь на директорию выше
        self.lora_relative_path = os.path.normpath(os.path.join("..", "ComfyUI", "models", "Loras"))
        self.checkpoint_relative_path = os.path.normpath(os.path.join("..", "ComfyUI", "models", "Checkpoints"))
        self.lora_absolute_path = os.path.abspath(self.lora_relative_path)
        self.checkpoint_absolute_path = os.path.abspath(self.checkpoint_relative_path)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_lora_tab(), "Loras")
        self.tabs.addTab(self.create_checkpoints_tab(), "Checkpoints")
        self.tabs.addTab(self.create_contacts_tab(), "Stabledif.ru")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_lora_tab(self):
        lora_tab = QWidget()
        layout = QVBoxLayout()
        title = QLabel("LORAS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        self.lora_table = QTableWidget()
        self.lora_table.setColumnCount(3)
        self.lora_table.setHorizontalHeaderLabels(["Name", "Image", "Keyword"])
        self.lora_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.lora_table.setColumnWidth(0, 200)
        self.lora_table.setColumnWidth(1, 170)
        self.lora_table.setColumnWidth(2, 170)
        self.lora_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        layout.addWidget(self.lora_table)

        self.save_button = QPushButton("Save changes")
        self.save_button.clicked.connect(self.save_lora_changes)
        layout.addWidget(self.save_button)

        self.link_label = QLabel(self.lora_relative_path)
        self.link_label.setAlignment(Qt.AlignCenter)
        self.link_label.setStyleSheet("font-size: 10px; color: white; text-decoration: underline;")
        self.link_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.link_label.mousePressEvent = self.open_folder
        layout.addWidget(self.link_label)

        lora_tab.setLayout(layout)
        self.load_lora_images()
        return lora_tab

    def create_checkpoints_tab(self):
        checkpoint_tab = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Checkpoints")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        self.checkpoint_table = QTableWidget()
        self.checkpoint_table.setColumnCount(3)
        self.checkpoint_table.setHorizontalHeaderLabels(["Name", "Image", "Keyword"])
        self.checkpoint_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.checkpoint_table.setColumnWidth(0, 200)
        self.checkpoint_table.setColumnWidth(1, 170)
        self.checkpoint_table.setColumnWidth(2, 170)
        self.checkpoint_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        layout.addWidget(self.checkpoint_table)

        self.save_checkpoint_button = QPushButton("Save changes")
        self.save_checkpoint_button.clicked.connect(self.save_checkpoint_changes)
        layout.addWidget(self.save_checkpoint_button)

        self.checkpoint_link_label = QLabel(self.checkpoint_relative_path)
        self.checkpoint_link_label.setAlignment(Qt.AlignCenter)
        self.checkpoint_link_label.setStyleSheet("font-size: 10px; color: white; text-decoration: underline;")
        self.checkpoint_link_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.checkpoint_link_label.mousePressEvent = self.open_checkpoint_folder
        layout.addWidget(self.checkpoint_link_label)

        checkpoint_tab.setLayout(layout)
        self.load_checkpoint_images()
        return checkpoint_tab

    def create_contacts_tab(self):
        contact_tab = QWidget()
        layout = QVBoxLayout()
        webview = QWebEngineView()
        webview.setUrl("https://stabledif.ru/lending")
        layout.addWidget(webview)
        contact_tab.setLayout(layout)
        return contact_tab

    def crop_and_resize(self, pixmap: QPixmap) -> QPixmap:
        img = pixmap.toImage()
        width = img.width()
        height = img.height()
        side = min(width, height)
        x = (width - side) // 2
        y = (height - side) // 2
        square_image = img.copy(x, y, side, side)
        square_pixmap = QPixmap.fromImage(square_image)
        return square_pixmap.scaled(self.target_size, self.target_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def load_keywords(self, file_path):
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {item['file_name']: item.get('keyword', '').replace("\\n", "\n") for item in data}

    def load_lora_images(self):
        keywords = self.load_keywords('loras-config.json')
        groups = {}
        for entry in os.scandir(self.lora_relative_path):
            if entry.is_dir():
                group_name = entry.name
                images = [os.path.join(root, file)
                        for root, _, files in os.walk(entry.path)
                        for file in files if file.lower().endswith(".png")]
                if images:
                    groups[group_name] = images
        row = 0
        total_rows = sum(len(images) + 1 for images in groups.values())
        self.lora_table.setRowCount(total_rows)
        for group, images in groups.items():
            header_label = QLabel(f"\U0001F4C1 {group}")
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setStyleSheet("font-size: 14px; color: white; text-decoration: underline;")
            header_label.setCursor(QCursor(Qt.PointingHandCursor))
            header_label.mousePressEvent = lambda event, group_path=group: self.open_group_folder(event, group_path, 'lora')
            self.lora_table.setCellWidget(row, 0, header_label)
            self.lora_table.setSpan(row, 0, 1, 3)
            self.lora_table.setRowHeight(row, 30)
            row += 1
            for path in images:
                name = os.path.splitext(os.path.basename(path))[0]
                name_item = QTableWidgetItem(name)
                name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.lora_table.setItem(row, 0, name_item)

                pixmap = QPixmap(path)
                cropped_pixmap = self.crop_and_resize(pixmap) if not pixmap.isNull() else QPixmap(self.target_size, self.target_size)
                label = QLabel()
                label.setPixmap(cropped_pixmap)
                label.setAlignment(Qt.AlignCenter)
                label.mousePressEvent = lambda event, path=path: self.open_lightbox(event, path)
                self.lora_table.setCellWidget(row, 1, label)

                keyword = keywords.get(name, "")
                keyword_text_edit = QTextEdit()
                keyword_text_edit.setPlainText(keyword)  # Устанавливаем текст с учетом переноса строк
                keyword_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Добавляем вертикальную прокрутку
                keyword_text_edit.setTextInteractionFlags(Qt.TextEditorInteraction)
                self.lora_table.setCellWidget(row, 2, keyword_text_edit)

                self.lora_table.setRowHeight(row, self.target_size)
                row += 1

    def load_checkpoint_images(self):
        keywords = self.load_keywords('checkpoints-config.json')
        groups = {}
        for entry in os.scandir(self.checkpoint_relative_path):
            if entry.is_dir():
                group_name = entry.name
                images = [os.path.join(root, file)
                        for root, _, files in os.walk(entry.path)
                        for file in files if file.lower().endswith(".png")]
                if images:
                    groups[group_name] = images
        row = 0
        total_rows = sum(len(images) + 1 for images in groups.values())
        self.checkpoint_table.setRowCount(total_rows)
        for group, images in groups.items():
            header_label = QLabel(f"\U0001F4C1 {group}")
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setStyleSheet("font-size: 14px; color: white; text-decoration: underline;")
            header_label.setCursor(QCursor(Qt.PointingHandCursor))
            header_label.mousePressEvent = lambda event, group_path=group: self.open_group_folder(event, group_path, 'checkpoint')
            self.checkpoint_table.setCellWidget(row, 0, header_label)
            self.checkpoint_table.setSpan(row, 0, 1, 3)
            self.checkpoint_table.setRowHeight(row, 30)
            row += 1
            for path in images:
                name = os.path.splitext(os.path.basename(path))[0]
                name_item = QTableWidgetItem(name)
                name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.checkpoint_table.setItem(row, 0, name_item)

                pixmap = QPixmap(path)
                cropped_pixmap = self.crop_and_resize(pixmap) if not pixmap.isNull() else QPixmap(self.target_size, self.target_size)
                label = QLabel()
                label.setPixmap(cropped_pixmap)
                label.setAlignment(Qt.AlignCenter)
                label.mousePressEvent = lambda event, path=path: self.open_lightbox(event, path)
                self.checkpoint_table.setCellWidget(row, 1, label)

                keyword = keywords.get(name, "")
                keyword_text_edit = QTextEdit()
                keyword_text_edit.setPlainText(keyword)  # Устанавливаем текст с учетом переноса строк
                keyword_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Добавляем вертикальную прокрутку
                keyword_text_edit.setTextInteractionFlags(Qt.TextEditorInteraction)
                self.checkpoint_table.setCellWidget(row, 2, keyword_text_edit)

                self.checkpoint_table.setRowHeight(row, self.target_size)
                row += 1

    def save_lora_changes(self):
        self.save_changes(self.lora_table, 'loras-config.json')

    def save_checkpoint_changes(self):
        self.save_changes(self.checkpoint_table, 'checkpoints-config.json')

    def save_changes(self, table, file_path):
        data = []
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item:
                name = item.text()
                keyword_text_edit = table.cellWidget(row, 2)
                keyword = keyword_text_edit.toPlainText()
                data.append({
                    "file_name": name,
                    "keyword": keyword
                })
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def open_lightbox(self, event, path):
        pixmap = QPixmap(path)
        window = LightboxWindow(pixmap)
        window.exec()

    def open_group_folder(self, event, group_path, type_):
        path = os.path.join(self.lora_absolute_path if type_ == 'lora' else self.checkpoint_absolute_path, group_path)
        os.startfile(path)

    def open_folder(self, event):
        os.startfile(self.lora_absolute_path)

    def open_checkpoint_folder(self, event):
        os.startfile(self.checkpoint_absolute_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = LoraImageViewer()
    viewer.show()
    sys.exit(app.exec())
