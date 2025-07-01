import os
import shutil
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import QObject, pyqtSignal, QEventLoop, Qt
from PyQt6.QtWidgets import QApplication

from .exceptions import empty_from_e, rollback_e

class seam_worker(QObject):
    # Сигнал для запуска обработки (аргументы: from_dir, to_dir, search_text)
    start_processing = pyqtSignal(str, str, str)
    continue_answer = pyqtSignal(bool)
    continue_answer_str = pyqtSignal(str)

    # Сигналы для gui
    user_confirm = pyqtSignal(str, str) # Statement, Question
    user_multi_choice = pyqtSignal(str, str, list) # Title, Question, Option list
    user_rename_choice = pyqtSignal (str, str, str) # Title, Question, base name
    fatal_error = pyqtSignal (str, str) # Error head, Error body
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.user_command = None
        self.continue_allowed = True
        self.start_processing.connect(self.data_processor)

    def data_processor(self, p_from_path, p_to_path, p_search_text):
        try:
            l_file_list = self.file_list(p_from_path)
        # Если путь пуст
        except empty_from_e as e:
            self.fatal_error.emit(
                "Внимание! Пустой путь!",
                "Указанный исходный путь пуст."
            )

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents() # Не блокируем интерфейс

            # Обработка отказа
            #if not self.continue_allowed:
            #   self.log_signal.emit("Пустой исходный путь. Выполнение прервано.")
            return
            exit()
        # Если некорректно передан путь
        except FileNotFoundError as wrong_path_exception:
            self.fatal_error.emit(
                "Внимание! Некорректный путь!",
                "Указанный исходный путь не может быть найден вашей ОС. Обратитесь к разработчику."
            )
            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс

            if not self.continue_allowed:
                self.log_signal.emit("Некорректный исходный путь. Выполнение прервано.")
            exit()
        #print(l_file_list)
        if not l_file_list:
            self.fatal_error.emit(
                "Внимание! Файлы не найдены!",
                "Указанный исходный путь не содержит подходящих файлов."
            )

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс

            if not self.continue_allowed:
                self.log_signal.emit("Нет подходящих файлов. Выполнение прервано.")
            exit()
            return

        try:
            l_processed_list = self.process_iterator(l_file_list, p_search_text)
        except Exception as e:
            self.fatal_error.emit(
                "Критическая ошибка!",
                f"{e}"
            )

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс

            if not self.continue_allowed:
                self.log_signal.emit(f"{e}")
            exit()
            return

        if not l_processed_list:
            self.fatal_error.emit(
                "Внимание! Файлы не найдены!",
                "Поиск по данному запросу не принёс результатов."
            )

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс

            if not self.continue_allowed:
                self.log_signal.emit("Поиск по запросу не принёс результатов.")
            exit()
            return

        try:
            self.forklift_operator(l_processed_list, p_to_path)
        except rollback_e as e:
            self.fatal_error.emit(
                "Отмена операции",
                f"{e}"
            )

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс

            if not self.continue_allowed:
                self.log_signal.emit(f"{e}")
            return
        except Exception as e:
            self.fatal_error.emit(
                "Критическая ошибка!",
                f"{e}"
            )

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс

            if not self.continue_allowed:
                self.log_signal.emit(f"{e}")
            return

    # Функция проверки наличия xml файлов в папке поиска и их сбор в список
    def file_list(self, from_path:os.PathLike[str]) -> list[os.PathLike[str] | str] | Exception:
        # Генератор путей для файлов
        l_file_list = [
            os.path.join(from_path, xml_file)
            for xml_file in os.listdir(from_path)
            if xml_file.endswith('.xml')
        ]
        # Если нет ни одного подходящего файла
        if not l_file_list:
            raise empty_from_e('Path is empty')
        else:
            return l_file_list

    # Вспомогательная функция поиска текста внутри xml файла
    def _xml_process(self, xml_file_path: os.PathLike[str], search_text: str) -> str | None | Exception:
        try:
            tree = ET.parse(xml_file_path)
            xml_text = ET.tostring(tree.getroot(), encoding='unicode')
            return xml_file_path if search_text.lower() in xml_text.lower() else None
        except Exception as e:
            raise Exception(f"Function '_xml_process' failed: {e}")

    # Функция-итератор запуска поиска внутри файла - если нужен более сложный/умный поиск, то дорабатывать нужно её или вложенную
    # Текущий поиск может искать вхождения без учёта регистра (самый простой вариант)
    def process_iterator(self, l_file_list: list, search_text: str) -> list[str] | Exception:
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(
                    lambda f: self._xml_process(f, search_text), l_file_list
                ))
            return [r for r in results if r is not None]
        except Exception as e:
            raise Exception("Function 'process_iterator' failed")

    # Функция для копирования найденных файлов в выбранную папку
    def forklift_operator(self, file_list: list, destination_path: str | os.PathLike[str], l_inner_call: str = '',
                          l_new_name: str = None) -> str | None | Exception:
        # Проверки для внешнего вызова
        if l_inner_call == '':
            # Проверка, что путь корректный
            if not destination_path:
                raise ValueError('Введён некорректный путь копирования (куда)')

            # Проверка, что путь пустой
            if os.listdir(destination_path):
                # Создаем event loop для ожидания ответа
                Q_loop = QEventLoop()
                self.continue_answer.connect(Q_loop.quit,
                                             Qt.ConnectionType.QueuedConnection)  # Выход из loop при ответе
                # Запрашиваем подтверждение в главном потоке
                self.user_confirm.emit(
                    "Выбранный путь копирования не пустой",
                    "Продолжить?"
                )
                Q_loop.exec()  # Блокируем выполнение Worker до ответа
                self.continue_answer.disconnect(Q_loop.quit)

                # Проверяем ответ
                if not self.continue_allowed:
                    self.log_signal.emit("Отменено пользователем")
                    raise Exception("Отменено пользователем")

        # Перемещение
        try:
            for f in file_list:
                # Определение базовых параметров для внешнего вызова
                if l_inner_call == '':
                    file_name = os.path.basename(f)
                    file_noext_name, file_ext = os.path.splitext(file_name)
                    desti_name = os.path.join(destination_path, file_name)
                # Определение базовых параметров для внутреннего вызова
                else:
                    file_name = l_new_name
                    file_noext_name, file_ext = os.path.splitext(file_name)
                    desti_name = os.path.join(destination_path, file_name)

                    print(f'inner: f is {f}, {desti_name}\n')

                # Проверка, что файла с таким названием нет
                if not os.path.exists(desti_name):
                    shutil.copy2(f, desti_name)
                else:
                    # Если файл с таким названием уже есть
                    # Создаем event loop для ожидания ответа
                    Q_loop = QEventLoop()
                    self.continue_answer.connect(Q_loop.quit,
                                                 Qt.ConnectionType.QueuedConnection)  # Выход из loop при ответе
                    # Запрашиваем подтверждение в главном потоке
                    self.user_multi_choice.emit(
                        "Внимание!",
                        f"Файл {file_name} уже есть в {destination_path}",
                        ["Пропустить", "Перезаписать", "Переименовать", "Отмена"]
                    )
                    Q_loop.exec()  # Блокируем выполнение Worker до ответа
                    self.continue_answer.disconnect(Q_loop.quit)

                    # Проверяем ответ
                    match self.continue_allowed:
                        # Пропуск итерации
                        case 0:
                            print('continue')
                            continue
                        # Перезапись
                        case 1:
                            shutil.copy2(f, destination_path)
                            print('copy2')
                            continue
                        # Переименование
                        case 2:
                            print('rename sequence')
                            # Создаем event loop для ожидания ответа
                            Q_loop = QEventLoop()
                            self.continue_answer.connect(Q_loop.quit,
                                                         Qt.ConnectionType.QueuedConnection)  # Выход из loop при ответе
                            # Запрашиваем подтверждение в главном потоке
                            print("ффф")
                            self.user_rename_choice.emit(
                                "Введите новое имя",
                                "Введите новое имя файла", #или оставьте поле пустым для автоинкремента",
                                f'{file_name}'
                            )

                            Q_loop.exec() # Блокируем выполнение Worker до ответа
                            self.continue_answer.disconnect(Q_loop.quit)
                            # Проверяем ответ
                            print(f'aaaa{self.continue_allowed}')
                            if self.continue_allowed == "User_cancel_01":
                                self.log_signal.emit("Отменено пользователем")
                                raise Exception("Отменено пользователем")
                            else:
                                new_desti_name = f'{self.continue_allowed}{file_ext}'
                                print(f"Final file directory will be {new_desti_name}\n")
                                self.forklift_operator([f], destination_path, '[Inner] ', new_desti_name)
                                continue
                        # Выход
                        case 3:
                            print('User cancel')
                            raise rollback_e('User cancel')
                        # Проблема между стулом и клавиатурой
                        case _:
                            print('Write 1, 2 or 3.\n')
                            continue
        except rollback_e as e:
            raise Exception(e)
        except Exception as e:
            if l_inner_call is None:
                raise Exception(f"Function 'forklift_operator' failed: {e}")
            else:
                raise Exception(f"Inner function 'forklift_operator' failed: {e}")

        return (result := f'Операция завершена успешно.'
                          f'Скопировано {len(file_list)} файлов в папку {destination_path}')

    # Метод для установки ответа (вызывается из главного потока)
    def _set_user_answer(self, allowed):
        self.continue_allowed = allowed
        if allowed is not None:
            self.continue_answer.emit(1)
        else:
            raise Exception('Вернулся пустой ответ на вопрос. Пожалуйста, обратитесь к разработчику.')