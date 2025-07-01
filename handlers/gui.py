import os.path
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QPushButton, QFileDialog, QLineEdit, QMessageBox, QInputDialog,
                             QDialog, QHBoxLayout, QDialogButtonBox)
from PyQt6.QtCore import QDir, Qt, QThread
from PyQt6.QtGui import QIcon, QPixmap

from .search_move import res_search
from .worker_seam import seam_worker

class seam_gui(QWidget):

    def __init__(self, common_path):
        super().__init__()

        self.processor = seam_worker()
        self.processor_thread = QThread()
        self.processor.moveToThread(self.processor_thread)
        self.processor_thread.start()

        self.init_ui(common_path)
        self.connect_signals()

    def init_ui(self, common_path):
        # Общая информация
        self.setWindowTitle("SeaMs Reasonable")
        self.setFixedSize(300, 370)
        self.common_path = common_path
        self.icon_path = os.path.join(self.common_path, 'images', 'mainicon.png')
        self.error_icon_path = os.path.join(self.common_path, 'images', 'erricon.png')
        self.success_icon_path = os.path.join(self.common_path, 'images', 'sucicon.png')

        # Icons
        Icon = QIcon('icon.png')
        Error_Icon = QIcon('erricon.png')

        self.setWindowIcon(Icon)

        layout = QVBoxLayout()

        # Значения по умолчанию
        self.start_dir = QDir.currentPath()

        # Виджеты
        # From directory
        self.From_Dir_label = QLabel(f"From directory: ")
        self.From_Dir_label_2 = QLabel(f"{self.start_dir}")
        self.From_Dir_button = QPushButton('Choose directory...')
        self.From_Dir_button.clicked.connect(lambda: self.choose_directory_dialog(self.From_Dir_label_2))

        # To directory
        self.To_Dir_label = QLabel(f"To directory: ")
        self.To_Dir_label_2 = QLabel(f"{self.start_dir}")
        self.To_Dir_button = QPushButton('Choose directory...')
        self.To_Dir_button.clicked.connect(lambda: self.choose_directory_dialog(self.To_Dir_label_2))

        # Search Text
        self.Search_Text_label = QLabel('You are searching for: ')
        self.Search_Text_line = QLineEdit("Мартья")#('Some happiness in this foul world')

        # Search starter
        self.Search_Starter_btn = QPushButton("START")

        """
        # Nogui option
        self.Search_Starter_btn.clicked.connect(lambda: self.search_starter(self.From_Dir_label_2, self.To_Dir_label_2, self.Search_Text_line))
        """

        # Dividers
        self.divider_1 = QLabel('******************************************************')
        self.divider_2 = QLabel('******************************************************')
        self.divider_3 = QLabel('******************************************************')

        # Размещение виджетов

        # From directory
        layout.addWidget(self.From_Dir_label)
        layout.addWidget(self.From_Dir_label_2)
        layout.addWidget(self.From_Dir_button)
        layout.addWidget(self.divider_1)

        # To directory
        layout.addWidget(self.To_Dir_label)
        layout.addWidget(self.To_Dir_label_2)
        layout.addWidget(self.To_Dir_button)
        layout.addWidget(self.divider_2)

        # Search Text
        layout.addWidget(self.Search_Text_label)
        layout.addWidget(self.Search_Text_line)
        layout.addWidget(self.divider_3)

        # Search Starter
        layout.addWidget(self.Search_Starter_btn)

        self.setLayout(layout)

    def choose_directory_dialog(self, label: QLabel):
        # Вызываем диалог выбора директории
        directory = QFileDialog.getExistingDirectory(
            self,
            "Choose directory",
            label.text(),  # Начальная директория
            QFileDialog.Option.ShowDirsOnly  # Показывать только директории
        )

        if directory:  # Если пользователь выбрал директорию (не нажал "Отмена")
            label.setText(f"{directory}")

    """
    # Nogui option
    def search_starter(self, from_dir, to_dir, search_text):
        print(from_dir.text(), to_dir.text(), search_text.text())
        try:
            res_search(from_dir.text(), to_dir.text(), search_text.text())
        except Exception as e:
            print(e)
    """

    def connect_signals(self):
        self.Search_Starter_btn.clicked.connect(self.search_starter)

        self.processor.user_confirm.connect(self.show_confirmation)
        self.processor.user_multi_choice.connect(self.show_mult_choice)
        self.processor.user_rename_choice.connect(self.show_input_dialog)

        self.processor.fatal_error.connect(self.show_error)

        #self.processor.log_signal.connect(self.log_label.setText)

    def search_starter(self):
        #self.Search_Starter_btn.setEnabled(False)

        from_dir = self.From_Dir_label_2.text()
        to_dir = self.To_Dir_label_2.text()
        search_text = self.Search_Text_line.text()
        try:
            self.processor.start_processing.emit(from_dir, to_dir, search_text)
        except Exception as e:
            print(e)
    def show_confirmation(self, title, question):
        reply = QMessageBox.question(
            self, title, question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        self.processor._set_user_answer(reply == QMessageBox.StandardButton.Yes)

    def show_mult_choice(self, title, question, buttons):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(question)

        for i, btn_text in enumerate(buttons):
            button = msg_box.addButton(btn_text, QMessageBox.ButtonRole.ActionRole)
            if i == 0:  # Первая кнопка - по умолчанию
                msg_box.setDefaultButton(button)

        msg_box.exec()
        self.processor._set_user_answer(msg_box.buttons().index(msg_box.clickedButton()))
        # Возвращаем индекс нажатой кнопки (0-3)
        #return msg_box.buttons().index(msg_box.clickedButton())

    def show_input_dialog(self, title, question, base_name):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Основные элементы
        label = QLabel(question)
        line_edit = QLineEdit(base_name)
        error_label = QLabel("Имя должно отличаться от исходного!")
        error_label.setStyleSheet("color: red; font: italic;")
        error_label.setVisible(False)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)

        # Компоновка
        layout.addWidget(label)
        layout.addWidget(error_label)
        layout.addWidget(line_edit)
        layout.addWidget(button_box)

        # Валидация
        def validate_text():
            new_text = line_edit.text()
            is_valid = new_text.strip() != "" and new_text != base_name
            error_label.setVisible(not is_valid)
            ok_button.setEnabled(is_valid)

        line_edit.textChanged.connect(validate_text)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        line_edit.selectAll()
        validate_text()

        # Обработка
        result = ""
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = line_edit.text()
            if result == base_name:
                result = ""
        else:  # Если нажата кнопка Cancel
            result = "User_cancel_01"

        self.processor._set_user_answer(result)

    def show_error(self, Title: str, e: Exception):
        """Функция поп-апов (ошибки и окно "успеха")"""
        dialog = QDialog()
        dialog.setWindowTitle(Title)

        icon_label = QLabel()
        pixmap = QPixmap(self.error_icon_path) #Указан тип строки или пути, если захочется потом поменять иконку или добавить возможность пользователю кастомизировать её
        icon_label.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))

        text_label = QLabel(e)
        text_label.setWordWrap(True)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)

        hbox = QHBoxLayout()
        hbox.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignLeft)
        hbox.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignRight)

        dialog.setLayout(vbox)
        dialog.exec()
        return dialog

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = seam_gui()
#     window.show()
#     sys.exit(app.exec())