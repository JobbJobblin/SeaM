import os
import shutil
import xml.etree.ElementTree as ET

from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Callable, Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal, QEventLoop, Qt
from PyQt6.QtWidgets import QApplication

from .exceptions import empty_from_e, rollback_e


class seam_worker(QObject):
    # Сигналы для gui
    start_processing = pyqtSignal(str, str, str, dict)  # Служебный сигнал для запуска обработки (Args: from_dir, to_dir, search_text, toggle_options) (Передаётся из главного потока)
    continue_answer = pyqtSignal(bool)  # Служебный сигнал для закрытия петли (QEventLoop) (Args: bool)
    user_confirm = pyqtSignal(str, str)  # Сигнал-шаблон для вопроса с двумя ответами (Args: Statement, Question)
    user_multi_choice = pyqtSignal(str, str, list)  # Сигнал-шаблон для вопроса со списком ответов (Args:  Title, Question, Option list)
    user_rename_choice = pyqtSignal(str, str, str)  # Сигнал для вопроса переименования (Args: Title, Question, base name)
    end_dual_signal = pyqtSignal(str, str) #Конечный служебный сигнал с двумя аргументами (Args: msg header, msg body)

    log_signal = pyqtSignal(str)  # Служебный сигнал для логов (Args: Log Message)

    # Конструктор
    def __init__(self) -> None:
        super().__init__()
        self.user_command = None
        self.continue_allowed = True
        self.start_processing.connect(self.data_processor)

    # Главная функция обработки запроса поиска
    def data_processor(self, p_from_path: os.PathLike[str] | str, p_to_path: os.PathLike[str] | str,
                       p_search_text: os.PathLike[str] | str, p_search_options: dict) -> None:

        # сбор списка файлов директории
        try:
            l_file_list = self.file_list(p_from_path)
        # Если путь пуст
        except empty_from_e as e:
            self.end_dual_signal.emit(
                "Внимание! Пустой путь!",
                "Указанный исходный путь пуст."
            )
            # self.log_signal.emit("Пустой исходный путь. Выполнение прервано.")  # logmsg

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс
            return
        # Если некорректно передан путь
        except FileNotFoundError as wrong_path_exception:
            self.end_dual_signal.emit(
                "Внимание! Некорректный путь!",
                f"Указанный исходный путь не может быть найден. \nТекст ошибки: {wrong_path_exception}"
            )
            # self.log_signal.emit("Некорректный исходный путь. Выполнение прервано.")  # logmsg

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс
            return
        # Есои папка есть, но в ней нет подходящих по формату файлов
        if not l_file_list:
            self.end_dual_signal.emit(
                "Внимание! Файлы не найдены!",
                "Указанный исходный путь не содержит подходящих файлов."
            )
            # self.log_signal.emit("Нет подходящих файлов. Выполнение прервано.") # logmsg

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс
            return
        try:
            l_processed_list = self.process_iterator(l_file_list, p_search_text, p_search_options)
        except Exception as e:
            self.end_dual_signal.emit(
                "Критическая ошибка!",
                f"{e}"
            )
            # self.log_signal.emit(f"Произошла непредвиденная ошибка: {e}")#logmsg

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс
            return
        if not l_processed_list:
            self.end_dual_signal.emit(
                "Внимание! Файлы не найдены!",
                "Поиск по данному запросу не принёс результатов."
            )
            # self.log_signal.emit("Поиск по запросу не принёс результатов.") #logmsg

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс
            return

        # Проверка пути перемещения
        try:
            self.target_check(l_processed_list, p_to_path)
        except Exception as e:
            self.end_dual_signal.emit(
                "Критическая ошибка!",
                f"{e}"
            )
            # self.log_signal.emit(f"Произошла непредвиденная ошибка: {e}")  # logmsg

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс
            return

        try:
            self.forklift_operator(l_processed_list, p_to_path)
        except rollback_e as e:
            self.end_dual_signal.emit(
                "Отмена операции",
                f"{e}"
            )
            # self.log_signal.emit(f"Произошла непредвиденная ошибка: {e}")  # logmsg

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс
            return
        except Exception as e:
            self.end_dual_signal.emit(
                "Критическая ошибка!",
                f"{e}"
            )
            # self.log_signal.emit(f"Произошла непредвиденная ошибка: {e}")  # logmsg

            # Ожидание ответа через флаг
            while not hasattr(self, 'continue_allowed'):
                QApplication.processEvents()  # Не блокируем интерфейс
            return

    # Функция проверки наличия xml файлов в папке поиска и их сбор в список
    def file_list(self, from_path: os.PathLike[str] | str) -> list[os.PathLike[str] | str] | Exception:
        # Генератор путей для файлов
        l_file_list = [
            os.path.join(from_path, xml_file)
            for xml_file in os.listdir(from_path)
            if xml_file.endswith('.xml')
        ]
        # Если нет ни одного подходящего файла
        if not l_file_list:
            raise empty_from_e('Пустой путь.')
        else:
            return l_file_list

    # Вспомогательная функция поиска текста внутри xml файла
    def _xml_process(self, xml_file_path: os.PathLike[str], search_text: str, options: dict) -> str | None | Exception:
        try:
            tree = ET.parse(xml_file_path)
            xml_text = ET.tostring(tree.getroot(), encoding='unicode')
            if options['register']:
                return xml_file_path if search_text in xml_text else None
            else:
                return xml_file_path if search_text.lower() in xml_text.lower() else None
        except Exception as e:
            raise Exception(f"Function '_xml_process' failed: {e}")

    # Функция-итератор запуска поиска внутри файла - если нужен более сложный/умный поиск, то дорабатывать нужно её или вложенную
    # Текущий поиск может искать вхождения без учёта регистра (самый простой вариант)
    def process_iterator(self, l_file_list: list, search_text: str, options: dict) -> list[str] | Exception:
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(
                    lambda f: self._xml_process(f, search_text, options), l_file_list
                ))
            return [r for r in results if r is not None]
        except Exception as e:
            raise Exception("Function 'process_iterator' failed")

    # Проверка папки перемещения
    def target_check(self, l_file_list: list,destination_path: str | os.PathLike[str]):
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
            if self.continue_allowed == 65536:  # Код QMessageBox.StandardButton.No
                # self.log_signal.emit("Отменено пользователем")
                raise Exception("Отменено пользователем")

        # Предупреждение о количестве файлов
        # Создаем event loop для ожидания ответа
        Q_loop = QEventLoop()
        self.continue_answer.connect(Q_loop.quit,
                                     Qt.ConnectionType.QueuedConnection)  # Выход из loop при ответе
        # Запрашиваем подтверждение в главном потоке
        self.user_confirm.emit(
            "Внимание!",
            f"Вы собираетесь переместить {len(l_file_list)} файлов.\n"
            "Продолжить?"
        )
        Q_loop.exec()  # Блокируем выполнение Worker до ответа
        self.continue_answer.disconnect(Q_loop.quit)

        # Проверяем ответ
        if self.continue_allowed == 65536:  # Код QMessageBox.StandardButton.No
            # self.log_signal.emit("Отменено пользователем")
            raise Exception("Отменено пользователем")

    # Фабрика декораторов. Принимает параметр по имени сигнала PyQT (Если будут ещё подобные эмиты)
    def fd_emit_on_outer_call(target_signal: str) -> Callable:
        # Функция декоратор
        def dec_inner_handler(method: Callable):
            # Передача метаданных функции-декоратору
            @wraps(method)
            # Основная логика
            def inner_wrapper(self: Any, *args: Any, **kwargs: Any):
                # Проверка на внутренний вызов
                is_inner_call = kwargs.get("l_inner_call", "") != ""
                # Вызов метода
                result = method(self, *args, **kwargs)
                # Если внешний закрывается, то отдаём сигнал
                if not is_inner_call and hasattr(self, target_signal):

                    file_list = args[0] if args else kwargs.get("file_list", [])
                    destination_path = args[1] if len(args) > 1 else kwargs.get("destination_path", "")
                    print("DEBUG: Emitting signal!")

                    emit_msg_head = ('Успех!')
                    emit_msg_body = (
                        f'Операция завершена успешно.\n'
                               f'Скопировано {len(file_list)} файлов в папку \n{destination_path}')
                    getattr(self, target_signal).emit(emit_msg_head, emit_msg_body)
                return  result
            return inner_wrapper
        return dec_inner_handler

    # Функция для копирования найденных файлов в выбранную папку
    @fd_emit_on_outer_call(target_signal = 'end_dual_signal')
    def forklift_operator(self, file_list: list, destination_path: str | os.PathLike[str], l_new_name: str = None,
                          l_inner_call: str = '', l_user_toggle: bool = False) -> None:
        # Параметр "Для всех"
        self.user_options = l_user_toggle
        print('out',self.user_options)

        # Перемещение
        try:

            for i, f in enumerate(file_list):
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

                # Проверка, что файла с таким названием нет
                if not os.path.exists(desti_name):
                    shutil.copy2(f, desti_name)
                else:
                    # Если выбрана опция "Для всех"
                    if self.user_options:
                        print('aaaaa',self.user_options)
                        match self.continue_allowed:
                            # Пропуск итерации
                            case 1:
                                print(i)
                                # self.log_signal.emit(f"[{i}] Итерация пропущена")
                                continue
                            # Перезапись файла
                            case 2:
                                # self.log_signal.emit(f"[{i}] Перезапись файла с названием '{f}'")
                                shutil.copy2(f, destination_path)
                                continue
                            # Переименование
                            case 3:
                                new_desti_name = f'{file_noext_name} - copy{file_ext}'
                                # self.log_signal.emit(f"[{i}] (AUTO) Новый путь: {new_desti_name}")
                                self.forklift_operator([f], destination_path, new_desti_name, l_inner_call='[Inner] ', l_user_toggle = self.user_options)
                                continue
                    # Если файл с таким названием уже есть
                    # Создаем event loop для ожидания ответа
                    print('fall')
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
                        case 1:
                            # self.log_signal.emit(f"[{i}] Итерация пропущена")
                            continue
                        # Перезапись
                        case 2:
                            # self.log_signal.emit(f"[{i}] Перезапись файла с названием '{f}'")
                            shutil.copy2(f, destination_path)
                            continue
                        # Переименование
                        case 3:
                            # Проверка на опцию "Для всех"
                            if not self.user_options:
                                # self.log_signal.emit(f"[{i}] Переименование...")
                                # Создаем event loop для ожидания ответа
                                Q_loop = QEventLoop()
                                self.continue_answer.connect(Q_loop.quit,
                                                             Qt.ConnectionType.QueuedConnection)  # Выход из loop при ответе
                                # Запрашиваем подтверждение в главном потоке
                                self.user_rename_choice.emit(
                                    "Введите новое имя",
                                    "Введите новое имя файла",  # или оставьте поле пустым для автоинкремента",
                                    f'{file_noext_name}'
                                )

                                Q_loop.exec()  # Блокируем выполнение Worker до ответа
                                self.continue_answer.disconnect(Q_loop.quit)
                            # Проверяем ответ
                            if self.continue_allowed == "User_cancel_01":
                                # self.log_signal.emit(f"[{i}] Отменено пользователем")
                                raise Exception("Отменено пользователем")
                            elif self.continue_allowed == 'User_autoincrement_choice_01':
                                new_desti_name = f'{file_noext_name} - copy{file_ext}'
                                # self.log_signal.emit(f"[{i}] (AUTO) Новый путь: {new_desti_name}")
                                print('before auto', self.user_options)
                                self.forklift_operator([f], destination_path, new_desti_name, l_inner_call ='[Inner] ', l_user_toggle = self.user_options)
                                continue
                            else:
                                new_desti_name = f'{self.continue_allowed}{file_ext}'
                                # self.log_signal.emit(f"[{i}] Новый путь: {new_desti_name}")
                                self.forklift_operator([f], destination_path, new_desti_name, l_inner_call ='[Inner] ', l_user_toggle = self.user_options)
                                continue
                        # Выход
                        case 4:
                            # self.log_signal.emit(f"[{i}] Отменено пользователем")
                            raise rollback_e('Отменено пользователем')
        except rollback_e as e:
            raise Exception(e)
        except Exception as e:
            if l_inner_call is None:
                raise Exception(f"Function 'forklift_operator' failed: {e}")
            else:
                raise Exception(f"[INNER] function 'forklift_operator' failed: {e}")

    # Метод для установки ответа (вызывается из главного потока)
    def _set_user_answer(self, allowed: str|int, options: bool = None) -> None:
        try:
            if allowed:
                print(allowed)
                print(options)
                self.continue_allowed = allowed
                if options:
                    self.user_options = options
                self.continue_answer.emit(1)
            else:
                raise Exception('Вернулся пустой ответ на вопрос. Пожалуйста, обратитесь к разработчику.')
        except Exception as e:
            self.end_dual_signal.emit(
                "Критическая ошибка!",
                f"Method '_set_user_answer' failed to execute: {e}"
            )