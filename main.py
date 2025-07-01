import os

from PyQt6.QtWidgets import QApplication
import sys

from handlers.gui import seam_gui

if __name__ == '__main__':
    app = QApplication(sys.argv)
    common_path = os.getcwd()
    window = seam_gui(common_path)
    window.show()
    sys.exit(app.exec())

    # try:
    #     example = res_search('C:\\Users\\Me\\Desktop\\tmp','C:\\LH\\Portfolio\\SeaM\\output', 'Мартьянов')
    # except Exception as e:
    #     print(e)
# TO_DO: Shutil умеет в архивы. Сделать обработку по архивам сразу.
