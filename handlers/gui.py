import os.path
import re

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QIcon, QPixmap

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QCheckBox, QMainWindow, QTextEdit, QTabWidget,
                             QPushButton, QFileDialog, QLineEdit, QMessageBox, QDialog, QHBoxLayout, QDialogButtonBox)

from .worker_seam import seam_worker

# Класс главного потока интерфейса
class seam_gui(QMainWindow):#QWidget):

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
        #self.setFixedSize(300, 550)
        self.setGeometry(550, 350, 300, 550)
        self.common_path = os.getcwd()

        # Иконки
        self.icon_path = QIcon(os.path.join(self.common_path, 'images', 'mainicon.png'))
        self.setWindowIcon(self.icon_path)

        self.error_icon_path = os.path.join(self.common_path, 'images', 'erricon.png')
        self.success_icon_path = os.path.join(self.common_path, 'images', 'sucicon.png')

        # Главный виджет и layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Создаем QTabWidget (контейнер вкладок)
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.main_tab_ui()
        self.extendet_settings_tab()

    # Функция построения интерфейса главной вкладки
    def main_tab_ui(self) -> None:
        # Главная вкладка
        main_tab = QWidget()
        layout = QVBoxLayout(main_tab)
        self.tab_widget.addTab(main_tab, "Главная")

        # Виджеты
        # Откуда
        self.From_Dir_label = QLabel(f"Откуда: ")
        self.From_Dir_label_2 = QLabel(f"{self.common_path}")
        self.From_Dir_button = QPushButton('Выберите директорию...')
        self.From_Dir_button.clicked.connect(lambda: self.choose_directory_dialog(self.From_Dir_label_2))

        # Куда
        self.To_Dir_label = QLabel(f"Куда: ")
        self.To_Dir_label_2 = QLabel(f"{self.common_path}")
        self.To_Dir_button = QPushButton('Выберите директорию...')
        self.To_Dir_button.clicked.connect(lambda: self.choose_directory_dialog(self.To_Dir_label_2))

        # Что ищем
        self.Search_Text_label = QLabel('Поисковой запрос: ')
        self.Search_Text_line = QLineEdit("Мартья")
        #self.Search_Text_line.setPlaceholderText('Some happiness in this foul world') - плейсхолдер

        self.Search_Node_label = QLabel('Ноды с учётом регистра\n(Используйте ; для разделителя):')
        self.Search_Node_line = QLineEdit("")

        # Опции
        #self.checkbox_nodes = QCheckBox('nodes (pending...)')
        self.checkbox_filenames = QCheckBox('files (pending...)')
        self.checkbox_insides = QCheckBox('insides (pending...)')
        self.checkbox_case = QCheckBox('Учитывать регистр')
        self.checkbox_partial = QCheckBox('partial (pending...)')
        self.checkbox_only = QCheckBox('only (pending...)')

        # Вспомогательные данные для валидации выбора опций
        self.option_dict = {}
        #self.option_dict['nodes'] = self.checkbox_nodes.isChecked()
        self.option_dict['filenames'] = self.checkbox_filenames.isChecked()
        self.option_dict['insides'] = self.checkbox_insides.isChecked()
        self.option_dict['case'] = self.checkbox_case.isChecked()
        self.option_dict['partial'] = self.checkbox_partial.isChecked()
        self.option_dict['only'] = self.checkbox_only.isChecked()

        # Кнопка инициализации поиска
        self.Search_Starter_btn = QPushButton("START")

        """
        # Nogui option
        self.Search_Starter_btn.clicked.connect(lambda: self.search_starter(self.From_Dir_label_2, self.To_Dir_label_2, self.Search_Text_line))
        """

        # Разделители
        self.divider_1 = QLabel('******')
        self.divider_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.divider_2 = QLabel('******')
        self.divider_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.divider_3 = QLabel('******')
        self.divider_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        layout.addWidget(self.Search_Node_label)
        layout.addWidget(self.Search_Node_line)
        layout.addWidget(self.divider_3)

        # Опции
        #layout.addWidget(self.checkbox_nodes)
        layout.addWidget(self.checkbox_filenames)
        layout.addWidget(self.checkbox_insides)
        layout.addWidget(self.checkbox_case)
        layout.addWidget(self.checkbox_partial)
        layout.addWidget(self.checkbox_only)

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

        # Опции
        #self.checkbox_nodes.stateChanged.connect(self._supp_options)
        self.checkbox_filenames.stateChanged.connect(self._supp_options)
        self.checkbox_insides.stateChanged.connect(self._supp_options)
        self.checkbox_case.stateChanged.connect(self._supp_options)
        self.checkbox_partial.stateChanged.connect(self._supp_options)
        self.checkbox_only.stateChanged.connect(self._supp_options)

        # Логирование
        # self.processor.log_signal.connect(self.log_label.setText)

    # Функция, инициализирующая поиск
    def search_starter(self) -> None:
        # сбор главных параметров
        from_dir = self.From_Dir_label_2.text()
        to_dir = self.To_Dir_label_2.text()
        search_text = self.Search_Text_line.text()

        # Регулярка для обработки текста нод в нижний регистр с игнорированием пустых
        search_nodes_pattern = r'\s*;\s*'
        search_nodes = [
            node.strip()# TODO: .lower() добавить к опции учёта регистра - разнести опцию учёта регистра на оба поисковых поля
            for node in re.split(search_nodes_pattern, self.Search_Node_line.text())
            if node.strip()
        ]

        try:
            self.processor.start_processing.emit(from_dir, to_dir, search_text, self.option_dict, search_nodes)
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

    # Вспомогательная функция для выбора опции поиска "Только"
    def _supp_options(self):
        try:
            # Перезапись значений
            #self.option_dict['nodes'] = self.checkbox_nodes.isChecked()
            self.option_dict['filenames'] = self.checkbox_filenames.isChecked()
            self.option_dict['insides'] = self.checkbox_insides.isChecked()
            self.option_dict['case'] = self.checkbox_case.isChecked()
            self.option_dict['partial'] = self.checkbox_partial.isChecked()
            self.option_dict['only'] = self.checkbox_only.isChecked()

            # Без list не будет списком - вернёт ошибку
            all_keys = list(self.option_dict.keys())
            variable_keys = all_keys[:-1]
            last_key = all_keys[-1]

            # Логика отключения кнопок
            # Если включена опция "только" и выбран один из вариантов
            if any(self.option_dict[k] for k in variable_keys) and self.option_dict[last_key]:
                #self.checkbox_nodes.setDisabled(True) if not self.checkbox_nodes.isChecked() else None
                self.checkbox_filenames.setDisabled(True) if not self.checkbox_filenames.isChecked() else None
                self.checkbox_insides.setDisabled(True) if not self.checkbox_insides.isChecked() else None
                self.checkbox_case.setDisabled(True) if not self.checkbox_case.isChecked() else None
                self.checkbox_partial.setDisabled(True) if not self.checkbox_partial.isChecked() else None
            # Если 2 и более выбрано
            elif sum(self.option_dict[k] for k in variable_keys) >= 2:
               self.checkbox_only.setDisabled(True)
            else:
                self.checkbox_only.setDisabled(False)
                #self.checkbox_nodes.setDisabled(False)
                self.checkbox_filenames.setDisabled(False)
                self.checkbox_insides.setDisabled(False)
                self.checkbox_case.setDisabled(False)
                self.checkbox_partial.setDisabled(False)
                self.checkbox_only.setDisabled(False)

        except Exception as e:
            print(e)

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

    # Функция построения интерфейса вкладки доп. настроек
    def extendet_settings_tab(self) -> None:
        # Вкладка расширенных настроек
        ext_settings = QWidget()
        ext_layout = QVBoxLayout(ext_settings)
        self.tab_widget.addTab(ext_settings, "Доп. настройки")

        self.namespaces_label = QLabel("Поле для указания имён пространств в xml")
        self.namespaces_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ext_layout.addWidget(self.namespaces_label)

        self.namespaces_text = QTextEdit()
        if os.path.exists(namesp_ath:=os.path.join(self.common_path, 'namespaces.txt')):
            with open(namesp_ath, 'r') as fp:
                text = fp.read()
                self.namespaces_text.setText(text)
        else:
            self.namespaces_text.setPlaceholderText("Введите текст здесь через ';'\n"
                                                   "Например:\n"
                                                   "soap: http://soap.org/soap/;\n"
                                                   "m: http://mem.org/\n")

        self.namespaces_confirm = QPushButton('Перезаписать')
        self.namespaces_confirm.clicked.connect(lambda: self.name_space_n_time())

        ext_layout.addWidget(self.namespaces_text)
        ext_layout.addWidget(self.namespaces_confirm)

    # Функция для работы с namespaces
    def name_space_n_time(self):
        # TODO: переписать show_confirmation для использования не только в работнике
        #self.show_confirmation('Перезапись namespaces', 'Вы уверены?')

        reply = QMessageBox.question(
            self, 'Перезапись namespaces', 'Вы уверены?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == 16384:
            try:
                namesp_ath = os.path.join(self.common_path, 'namespaces.txt')
                text = self.namespaces_text.toPlainText()
                with open(namesp_ath, 'w') as fp:
                    print(text)
                    fp.write(text)
            except Exception as e:
                print(f"Function 'name_spase_n_time' failed: {e}")