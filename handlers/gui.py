import os.path

from PyQt6.QtCore import QDir, Qt, QThread
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QCheckBox,
                             QPushButton, QFileDialog, QLineEdit, QMessageBox, QDialog, QHBoxLayout, QDialogButtonBox)

from .worker_seam import seam_worker


# Класс главного потока интерфейса
class seam_gui(QWidget):

    # Конструктор
    def __init__(self) -> None:
        super().__init__()

        self.processor = seam_worker()
        self.processor_thread = QThread()
        self.processor.moveToThread(self.processor_thread)
        self.processor_thread.start()

        self.init_ui()
        self.connect_signals()

    # Функция инициализации интерфейса
    def init_ui(self) -> None:
        # Общая информация
        self.setWindowTitle("SeaMs Reasonable")
        self.setFixedSize(300, 370)
        self.common_path = QDir.currentPath()

        # Иконки
        self.icon_path = QIcon(os.path.join(self.common_path, 'images', 'mainicon.png'))
        self.setWindowIcon(self.icon_path)

        self.error_icon_path = os.path.join(self.common_path, 'images', 'erricon.png')
        self.success_icon_path = os.path.join(self.common_path, 'images', 'sucicon.png')

        layout = QVBoxLayout()

        # Виджеты
        # Откуда
        self.From_Dir_label = QLabel(f"From directory: ")
        self.From_Dir_label_2 = QLabel(f"{self.common_path}")
        self.From_Dir_button = QPushButton('Choose directory...')
        self.From_Dir_button.clicked.connect(lambda: self.choose_directory_dialog(self.From_Dir_label_2))

        # Куда
        self.To_Dir_label = QLabel(f"To directory: ")
        self.To_Dir_label_2 = QLabel(f"{self.common_path}")
        self.To_Dir_button = QPushButton('Choose directory...')
        self.To_Dir_button.clicked.connect(lambda: self.choose_directory_dialog(self.To_Dir_label_2))

        # Что ищем
        self.Search_Text_label = QLabel('You are searching for: ')
        self.Search_Text_line = QLineEdit("Мартья")  # ('Some happiness in this foul world')

        # Кнопка инициализации поиска
        self.Search_Starter_btn = QPushButton("START")

        """
        # Nogui option
        self.Search_Starter_btn.clicked.connect(lambda: self.search_starter(self.From_Dir_label_2, self.To_Dir_label_2, self.Search_Text_line))
        """

        # Разделители
        self.divider_1 = QLabel('******************************************************')
        self.divider_2 = QLabel('******************************************************')
        self.divider_3 = QLabel('******************************************************')

        # Размещение виджетов

        # Откуда
        layout.addWidget(self.From_Dir_label)
        layout.addWidget(self.From_Dir_label_2)
        layout.addWidget(self.From_Dir_button)
        layout.addWidget(self.divider_1)

        # Куда
        layout.addWidget(self.To_Dir_label)
        layout.addWidget(self.To_Dir_label_2)
        layout.addWidget(self.To_Dir_button)
        layout.addWidget(self.divider_2)

        # Что ищем
        layout.addWidget(self.Search_Text_label)
        layout.addWidget(self.Search_Text_line)
        layout.addWidget(self.divider_3)

        # Кнопка инициализации поиска
        layout.addWidget(self.Search_Starter_btn)

        # Сбор макета
        self.setLayout(layout)

    # Вызов окна выбора директории
    def choose_directory_dialog(self, label: QLabel) -> None:
        # Вызываем диалог выбора директории
        directory = QFileDialog.getExistingDirectory(
            self,
            "Здесь могла бы быть ваша реклама: 8 800 *** .. --",
            label.text(),  # Директория для поиска
            QFileDialog.Option.ShowDirsOnly  # Показывать только директории
        )

        if directory:  # Если пользователь выбрал директорию (не нажал "Отмена")
            label.setText(directory)

    """
    # Nogui option
    def search_starter(self, from_dir, to_dir, search_text):
        print(from_dir.text(), to_dir.text(), search_text.text())
        try:
            res_search(from_dir.text(), to_dir.text(), search_text.text())
        except Exception as e:
            print(e)
    """

    # Функция для подключения сигналов
    def connect_signals(self) -> None:
        # Инициализатор
        self.Search_Starter_btn.clicked.connect(self.search_starter)

        # Диалоги
        self.processor.user_confirm.connect(self.show_confirmation)
        self.processor.user_multi_choice.connect(self.show_mult_choice)
        self.processor.user_rename_choice.connect(self.show_input_dialog)

        # Конечные сообщения
        self.processor.end_dual_signal.connect(self.show_err_or_succ)

        # Логирование
        # self.processor.log_signal.connect(self.log_label.setText)

    # Функция, инициализирующая поиск
    def search_starter(self) -> None:
        from_dir = self.From_Dir_label_2.text()
        to_dir = self.To_Dir_label_2.text()
        search_text = self.Search_Text_line.text()
        try:
            self.processor.start_processing.emit(from_dir, to_dir, search_text)
        except Exception as e:
            print(e)

    # Функция отображения диалогового окна "Да\Нет"
    def show_confirmation(self, title: str, question: str) -> None:
        reply = QMessageBox.question(
            self, title, question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        self.processor._set_user_answer(reply)

    # Функция отображения диалогового с несколькими настраиваемыми вариантами ответа
    def show_mult_choice(self, title: str, question: str, buttons: list) -> None:
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(question)

        # Чекбокс с опцией "для всех"
        self.checkbox = QCheckBox("Для всех (выбор опции 'переименовать' выполнит автопереименование)")  # Сохраняем как атрибут, если нужно будет проверить состояние
        msg_box.setCheckBox(self.checkbox)

        for i, btn_text in enumerate(buttons):
            button = msg_box.addButton(btn_text, QMessageBox.ButtonRole.ActionRole)
            if i == 0:  # Первая кнопка - по умолчанию
                msg_box.setDefaultButton(button)

        msg_box.exec()

        # Возвращаем индекс нажатой кнопки (1-4) + значение чекбокса
        self.processor._set_user_answer(msg_box.buttons().index(msg_box.clickedButton())+1, msg_box.checkBox().isChecked()) # +1 чтобы не передавать 0

    # Функция отображения диалогового окна с вводом текста
    def show_input_dialog(self, title: str, question: str, base_name: str) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Основные элементы
        label = QLabel(question)
        line_edit = QLineEdit(base_name)
        error_label = QLabel()  # ("Имя должно отличаться от исходного!")
        error_label.setStyleSheet("color: red; font: italic;")
        error_label.setVisible(False)

        hint_label = QLabel('Для автоматического переименования сделайте поле пустым')
        hint_label.setStyleSheet('color: green; font: bald;')

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)

        # Добавление виджетов
        layout.addWidget(label)
        layout.addWidget(error_label)
        layout.addWidget(line_edit)
        layout.addWidget(button_box)
        layout.addWidget(hint_label)

        # Внутренная функция валидации текста
        def _validate_text():
            new_text = line_edit.text()
            error_hint_text = ''
            # Убрана проверка на непустое название для автоинкремента
            error_hint_text = error_hint_text + (
                "Имя должно отличаться от исходного!") if not new_text != base_name else error_hint_text  # and new_text.strip() != ""

            # Расширенная логика валидации 03072025
            # Проверка на запрещённые символы
            forbidden_chars = set('<>:"/\\|?*')
            forbidden_chars.update(chr(i) for i in range(32))
            forbidden_chars.add(chr(127))
            print(error_hint_text)
            error_hint_text = error_hint_text + ("\nЗапрещённые символы в имени!") if any(
                char in forbidden_chars for char in new_text) else error_hint_text

            # Проверка на зарезервированные имена
            reserved_names = {
                "CON", "PRN", "AUX", "NUL",
                *[f"COM{i}" for i in range(1, 10)],
                *[f"LPT{i}" for i in range(1, 10)]
            }
            name_without_ext = new_text.split('.')[0].upper()
            error_hint_text = error_hint_text + (
                "\nЗарезервированнное имя Windows!") if name_without_ext in reserved_names else error_hint_text

            # Проверка на завершающие точку/пробел
            error_hint_text = error_hint_text + ("\nНе может заканчиваться на точку или пробел!") if new_text.endswith(
                ('.', ' ')) else error_hint_text

            error_label.setText(error_hint_text)
            error_label.setVisible(not error_hint_text == '')
            ok_button.setEnabled(error_hint_text == '')

        line_edit.textChanged.connect(_validate_text)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        line_edit.selectAll()
        _validate_text()

        # Обработка
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = line_edit.text()
            if result == '':
                result = 'User_autoincrement_choice_01'
        else:  # Если нажата кнопка Cancel
            result = "User_cancel_01"

        self.processor._set_user_answer(result)

    # Функция отображения конечного диалогового окна (успех\ошибка)
    def show_err_or_succ(self, Title: str, e: Exception|str) -> QDialog:
        """Функция поп-апов (ошибки и окно "успеха")"""
        dialog = QDialog()
        dialog.setWindowTitle(Title)

        icon_label = QLabel()
        if Title == 'Успех!':
            pixmap = QPixmap(
                self.success_icon_path)  # Указан тип строки или пути, если захочется потом поменять иконку или добавить возможность пользователю кастомизировать её
        else:
            pixmap = QPixmap(
                self.error_icon_path)  # Указан тип строки или пути, если захочется потом поменять иконку или добавить возможность пользователю кастомизировать её
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
