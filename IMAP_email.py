"""
Программа, которая по протоколу imap подключается к почтовому ящику (gmail, yandex, etc) и смотрит,
есть ли в папке Inbox непрочитанные сообщения. Если такие сообщения имеются – программа
зажигает на клавиатуре светодиод SCROLL LOCK(CAPS LOCK), если нет – гасит его.
        В качестве дополнения – сделайте так, чтобы программа сворачивалась в трей,
        запускалась фоновым процессом или службой Windows (демоном в Linux).

yandex:
1. Все настройки -> Почтовые программы -> С сервера imap.yandex.ru по протоколу IMAP (Способ авторизации по IMAP)
(Пароли приложений и OAuth-токены) check
2. Управление аккаунтом -> Пароли приложений -> Создать новый пароль (Почта: IMAP, POP3, SMPT)

Запуск pycharm от root: sudo /snap/pycharm-community/205/bin/pycharm.sh

print(subprocess.check_output('xset q | grep LED', shell=True)[65])   # Узнаем число для CAPSLOCK_Off(On)
"""

from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QSystemTrayIcon, QMenu, \
    QAction, qApp, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QSize
from daemonize import Daemonize

import imaplib
import pyautogui
import subprocess
import os, sys
import socket


class EmailPassword(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setMinimumSize(QSize(700, 250))  # Устанавливаем размеры
        self.setWindowTitle("Entry billboard")  # Устанавливаем заголовок окна

        self.grid_layout = QGridLayout(self)  # Создаём QGridLayout

        self.textbox1 = QLineEdit(self)     # Email
        self.textbox1.move(320, 20)
        self.textbox1.resize(350, 40)

        self.textbox2 = QLineEdit(self)     # Password
        self.textbox2.setEchoMode(QLineEdit.Password)
        self.textbox2.move(320, 80)
        self.textbox2.resize(350, 40)

        self.label1 = QLabel(self)      # Email
        self.label1.move(50, 20)
        self.label1.resize(300, 40)
        self.label1.setText("Enter your email:")

        self.label2 = QLabel(self)      # Password
        self.label2.move(50, 80)
        self.label2.resize(300, 40)
        self.label2.setText("Enter password:")

        self.btn = QPushButton('Enter', self)       # Enter email and password
        self.btn.move(250, 130)
        self.btn.resize(200, 60)
        self.btn.clicked.connect(self.email_password_sender_slot)

        self.email = 'feuerlag999@yandex.ru'
        self.password = '*************'
        self.textbox1.setText(self.email)
        self.textbox2.setText(self.password)

    @QtCore.pyqtSlot("bool", name="email_password_sender_slot")
    def update_email_password(self):
        self.on_click_email_pass()

    def on_click_email_pass(self):
        self.value1 = self.textbox1.text()
        self.value2 = self.textbox2.text()

        self.mw = MainWindow(self.value1, self.value2)
        self.mw.setWindowTitle("Message_Billboard")
        self.mw.setMinimumSize(700, 250)

        self.mw.show()
        self.close()


class MessageScript:

    def __init__(self, value1, value2):
        super().__init__()

        try:
            self.imap = imaplib.IMAP4_SSL('imap.yandex.com')
            self.imap.login(value1, value2)
        except socket.error:
            print("Ошибка подключения к почте. Проверьте подключение к интернету!")
        except imaplib.IMAP4_SSL.error:
            print("Проверьте правильность введенного пароля и логина!")

        self.imap.select(mailbox='INBOX')
        self.messages = self.count()  # Определяем количество непрочитанных сообщений
        self.capslock_on_off()      # Инициализируем загорание светодиода

    def count(self):
        status, response = self.imap.search('INBOX', '(UNSEEN)')
        unread_msg_nums = response[0].split()
        return len(unread_msg_nums)

    def capslock_on_off(self):
        pyautogui.FAILSAFE = True
        if self.messages != 0 and subprocess.check_output('xset q | grep LED', shell=True)[65] == 48:
            pyautogui.press('capslock')
            pyautogui.press('scrolllock')
            pyautogui.press('fn')
        elif self.messages == 0 and subprocess.check_output('xset q | grep LED', shell=True)[65] == 49:
            pyautogui.press('capslock')

class MainWindow(QWidget, MessageScript):
    def __init__(self, value1, value2):
        # Вызов метода супер класса
        QWidget.__init__(self, value1=value1, value2=value2)

        self.grid_layout = QGridLayout(self)  # Создаём QGridLayout

        self.reload = QPushButton('apt update', self)    # Update current information
        self.reload.move(200, 150)
        self.reload.resize(300, 60)
        self.reload.clicked.connect(self.__update)

        self.output_text = QLabel(self)
        self.output_text.move(150, 70)
        self.output_text.resize(500, 40)

        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        hide_action = QAction("Hide", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(qApp.quit)
        self.tray_menu = QMenu()
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(hide_action)
        self.tray_menu.addAction(quit_action)

        # Определяем иконку приложения для трея
        self.icon_tray = "002.jpg"
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon(self.icon_tray))
        self.tray_icon.setContextMenu(self.tray_menu)

        self.messageFinder()
        self.tray_icon.show()
        self.__update()

    # Возвращаем сообщение о наличии новых сообщений в окно уведомления
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if self.messages == 0:
            self.tray_icon.showMessage("Message information", "You don't have unread message!",
                                       QSystemTrayIcon.Information, 1000)
        else:
            self.tray_icon.showMessage("Message information", f"You have unread message: {self.messages}!",
                                       QSystemTrayIcon.Information, 1000)

    # Возвращаем сообщение о наличии сообщений в строку вывода
    def messageFinder(self):
        if self.messages == 0:
            self.output_text.setText(f"You don't have unread message!")
        else:
            self.output_text.setText(f"You have unread message: {self.messages}!")

    # Обновляем данные по нажатию кнопки
    def __update(self):
        self.messages = self.count()
        self.capslock_on_off()
        self.output_text.clear()
        self.messageFinder()

        print(f"Количество непрочитанных сообщений: {self.messages}")


def main():
    app = QApplication(sys.argv)

    emp = EmailPassword()
    emp.show()

    app.exec_()


if __name__ == '__main__':
    print(subprocess.check_output('xset q | grep LED', shell=True)[65])
    main()

    pidfile = "/var/tmp/daemon.pid"
    Message_billboard = os.path.basename(sys.argv[0])
    daemon = Daemonize(app="billboard", pid=pidfile, action=main)
    daemon.start()
