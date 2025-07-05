import os
import shutil
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

from .exceptions import empty_from_e, rollback_e


class res_search():
    # Конструктор
    def __init__(self, p_from_path, p_to_path, p_search_text):
        l_file_list = self.file_list(p_from_path)

        if not l_file_list:
            l_result = 'No files found'
            print(l_result)
            return
        # elif isinstance(l_file_list, Exception):
        #     print(f'Exception occured: {l_file_list}')
        #     l_result = l_file_list
        #     return

        l_processed_list = self.process_iterator(l_file_list, p_search_text)
        if not l_processed_list:
            l_result = 'No files match your text'
            print(l_result)
            return
        # elif isinstance(l_processed_list, Exception):
        #     print(f'Exception occured: {l_processed_list}')
        #     l_result = l_processed_list
        #     return

        self.forklift_operator(l_processed_list, p_to_path)
        # if isinstance(l_cursor, Exception):
        #     print(f'Exception occured: {l_cursor}')
        #     l_result = l_cursor
        #     #self.result_messenger(l_cursor)
        #     return

    # Функция проверки наличия xml файлов в папке поиска и их сбор в список
    def file_list(self, from_path: os.PathLike[str]) -> list[os.PathLike[str] | str] | Exception:
        # try:
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
        # except empty_from_e as e:
        #     print(e)
        #     return e
        # Если некорректно передан путь
        # except FileNotFoundError as wrong_path_exception:
        #     print(f'Path does not exist. {wrong_path_exception}')
        #     return wrong_path_exception

    # Вспомогательная функция поиска текста внутри xml файла
    def _xml_process(self, xml_file_path: os.PathLike[str], search_text: str) -> str | None | Exception:
        # try:
        tree = ET.parse(xml_file_path)
        xml_text = ET.tostring(tree.getroot(), encoding='unicode')
        return xml_file_path if search_text.lower() in xml_text.lower() else None
        # except Exception as e:
        #     print(f"Function '_xml_process' failed: {e}")
        #     return e

    # Функция-итератор запуска поиска внутри файла - если нужен более сложный/умный поиск, то дорабатывать нужно её или вложенную
    # Текущий поиск может искать вхождения без учёта регистра (самый простой вариант)
    def process_iterator(self, l_file_list: list, search_text: str) -> list[str] | Exception:
        # try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(
                lambda f: self._xml_process(f, search_text), l_file_list
            ))
        return [r for r in results if r is not None]
        # except Exception as e:
        #     print("Function 'process_iterator' failed")
        #     return e

    # Функция для копирования найденных файлов в выбранную папку
    def forklift_operator(self, file_list: list, destination_path: str | os.PathLike[str], l_inner_call: str = '',
                          l_new_name: str = None) -> str | None | Exception:
        # Проверки для внешнего вызова
        if l_inner_call == '':
            # Проверка, что путь корректный
            if not destination_path:
                raise ValueError('Destination path is empty')
            # Проверка, что путь пустой
            if os.listdir(destination_path):
                while True:
                    q1 = input(f"Directory {destination_path} is not empty\n"
                               "Are u sure? 'y/n'\n")
                    # Отмена операции
                    if q1.lower() == 'n':
                        # print('User cancel')
                        return (result := 'User cancel')
                    # Запуск обработки
                    elif q1.lower() == 'y':
                        break
                    # Проблема между стулом и клавиатурой
                    else:
                        print('Type y or n.\n')

        # Перемещение
        # try:
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
                while True:
                    q1 = input(f"{l_inner_call}Warning!\n"
                               f"File {file_name} already exists at {destination_path}\n"
                               "What do you want to do?\n"
                               "1) Skip\n"
                               "2) Rewrite\n"
                               "3) Rename\n"
                               "4) Exit from operation\n")
                    match q1:
                        # Пропуск итерации
                        case '1':
                            continue
                        # Перезапись
                        case '2':
                            shutil.copy2(f, destination_path)
                            continue
                        # Переименование
                        case '3':
                            q2 = input("Please, enter new filename or type 1 to autofill\n")
                            if q2 == '1':
                                new_desti_name = f'{file_noext_name} - copy{file_ext}'
                            else:
                                new_desti_name = f'{q2}{file_ext}'
                            print(f"Final file directory will be {new_desti_name}\n")
                            self.forklift_operator([f], destination_path, '[Inner] ', new_desti_name)
                            break
                        # Выход
                        case '4':
                            print('User cancel')
                            raise rollback_e('User cancel')
                        # Проблема между стулом и клавиатурой
                        case _:
                            print('Write 1, 2 or 3.\n')
                            continue

        # except rollback_e as e:
        #     print(e)
        #     return e
        # except Exception as e:
        #     if l_inner_call is None:
        #         print(f"Function 'forklift_operator' failed: {e}")
        #         return e
        #     else:
        #         print(f"Inner function 'forklift_operator' failed: {e}")
        #         return e

        return (result := f'Операция завершена успешно.'
                          f'Скопировано {len(file_list)} файлов в папку {destination_path}')
