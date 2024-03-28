import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QCheckBox, QScrollArea, QLabel, QSpinBox, QMessageBox, QMainWindow, QMenu, QGridLayout
from PyQt6.QtGui import QAction
import pygetwindow as gw
import screeninfo
import math
import ctypes


class WindowDistributor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ignore_taskbar = False

        self.setWindowTitle("Window Distributor 1.0")
        self.resize(400, 500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QGridLayout(self.central_widget)

        self.window_list_widget = QWidget()
        self.window_list_layout = QVBoxLayout(self.window_list_widget)
        self.populate_window_list()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.window_list_widget)

        self.layout.addWidget(scroll_area)

        self.bottom = QGridLayout()
        self.layout.addLayout(self.bottom, 1, 0)

        self.update_button = QPushButton("Обновить список")
        self.update_button.clicked.connect(self.update_window_list)
        self.bottom.addWidget(self.update_button, 1, 0)

        self.num_rows_label = QLabel("Количество окон по вертикали:")
        self.bottom.addWidget(self.num_rows_label, 2, 0)

        self.num_rows_spinbox = QSpinBox()
        self.num_rows_spinbox.setMinimum(1)
        self.num_rows_spinbox.setMaximum(50)
        self.num_rows_spinbox.setValue(2)
        self.bottom.addWidget(self.num_rows_spinbox, 2, 1)

        self.distribute_button = QPushButton("Распределить")
        self.distribute_button.clicked.connect(self.distribute_windows)
        self.bottom.addWidget(self.distribute_button, 1, 1)

        # self.ignore_taskbar_checkbox = QCheckBox("Игнорировать панель задач")
        # self.ignore_taskbar_checkbox.setChecked(False)
        # self.bottom.addWidget(self.ignore_taskbar_checkbox)

        self.setLayout(self.layout)

        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('Настройки')

        focus_action = QAction('Навести фокус на окна', self)
        focus_action.setCheckable(True)
        focus_action.setChecked(True)
        focus_action.triggered.connect(lambda: self.set_focus_on_windows(focus_action.isChecked()))
        settings_menu.addAction(focus_action)

        ignore_taskbar_action = QAction('Игнорировать панель задач', self)
        ignore_taskbar_action.setCheckable(True)
        ignore_taskbar_action.setChecked(False)
        ignore_taskbar_action.triggered.connect(lambda: self.set_ignore_taskbar(ignore_taskbar_action.isChecked()))
        settings_menu.addAction(ignore_taskbar_action)

        show_system_processes_action = QAction('Показывать системные процессы', self)
        show_system_processes_action.setCheckable(True)
        show_system_processes_action.setChecked(False)
        settings_menu.addAction(show_system_processes_action)

        always_on_top_action = QAction('Поверх остальных окон', self)
        always_on_top_action.setCheckable(True)
        always_on_top_action.setChecked(False)
        always_on_top_action.triggered.connect(lambda: self.set_always_on_top(always_on_top_action.isChecked()))
        settings_menu.addAction(always_on_top_action)

    def set_focus_on_windows(self, checked):
        if checked:
            self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        else:
            self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

    def set_ignore_taskbar(self, checked):
        self.ignore_taskbar = checked

    def set_always_on_top(self, checked):
        if checked:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowStaysOnTopHint)

    def get_taskbar_height(self):
        """Возвращает высоту панели задач."""
        taskbar = ctypes.windll.user32.FindWindowW(u"Shell_traywnd", None)
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(taskbar, ctypes.byref(rect))
        return rect.bottom - rect.top

    def populate_window_list(self):
        open_windows = gw.getAllTitles()
        open_windows.sort()

        self.window_checkboxes = []

        for title in open_windows:
            checkbox = QCheckBox(title)
            self.window_checkboxes.append(checkbox)
            self.window_list_layout.addWidget(checkbox)

    def update_window_list(self):
        for i in reversed(range(self.window_list_layout.count())):
            widget = self.window_list_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.populate_window_list()



    def distribute_windows(self):
        try:
            selected_window_titles = [checkbox.text() for checkbox in self.window_checkboxes if checkbox.isChecked()]

            screen = gw.getWindowsWithTitle(gw.getActiveWindowTitle())[0]
            screen_width, screen_height = screeninfo.get_monitors()[0].width, screeninfo.get_monitors()[0].height

            if self.ignore_taskbar != True:
                screen_height -= self.get_taskbar_height()

            num_windows = len(selected_window_titles)

            if num_windows > 0:
                num_rows = self.num_rows_spinbox.value()
                num_columns = math.ceil(num_windows / num_rows)

                window_width = screen_width // num_columns
                window_height = screen_height // num_rows

                max_x_offset = screen_width - window_width
                max_y_offset = screen_height - window_height

                x_offset = 0
                y_offset = 0
                for title in selected_window_titles:
                    windows = gw.getWindowsWithTitle(title)
                    for window in windows:
                        if x_offset > max_x_offset:
                            x_offset = 0
                            y_offset += window_height
                        if y_offset > max_y_offset:
                            y_offset = 0
                        window.moveTo(x_offset, y_offset)
                        window.resizeTo(window_width, window_height)
                        x_offset += window_width
        except Exception as e:
            error_dialog = QMessageBox(self)
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setText("An error occurred:")
            error_dialog.setInformativeText(str(e))
            error_dialog.setWindowTitle("Error")
            error_dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window_distributor = WindowDistributor()
    window_distributor.show()
    sys.exit(app.exec())
