# coding:utf-8
__author__ = "zhou"
# create by zhou on 2020/3/3
from flask import Flask,render_template,request
import threading
import time
import pywinauto
from pywinauto.controls.hwndwrapper import DialogWrapper, BaseWrapper
import time
import typing
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow,QApplication,QMessageBox
import json
import sys
from queue import Queue, Empty


desktop = pywinauto.Desktop()


class WeChatApi(object):
    def __init__(self):
        self.chat_list = []
        self.chat_list_uptime = 0
        self._fresh_window()
        self.queue = Queue(10000)
        self.chat_window_titles = []

    def _fresh_window(self):
        global desktop
        buff = []
        buff_1 = []
        for i in range(10):
            try:
                windows:typing.List[DialogWrapper] = desktop.windows()
            except Exception as e:
                print(str(e))
                desktop = pywinauto.Desktop()
        for i in windows:
            if i.friendly_class_name() == 'ChatWnd':
                _ = i.window_text()
                buff.append([i, _])
                buff_1.append(_)
        buff_1 = list(set(buff_1))
        buff_1.sort()
        self.chat_list = buff
        self.chat_window_titles = buff_1
        self.chat_list_uptime = time.time()

    def send_to_chat_window(self, window_title, message):
        self.queue.put((window_title, message), timeout=0.5)


    def _send(self, window_title, message):
        result = True
        if window_title not in self.chat_window_titles:
            result = False, ('%s聊天对话框暂未找到' % window_title)
        else:
            try:
                for _ in self.chat_list:
                    i = _[0]
                    try:
                        if i.window_text() == window_title:
                            i.set_focus()
                            for msg in message.split('\n'):
                                i.send_chars(msg)
                                time.sleep(0.02)
                                i.send_keystrokes("^~")
                            time.sleep(0.1)
                            i.send_keystrokes("~")
                            result = True
                            break
                    except Exception as _e:
                        raise Exception(str(_e))
                    else:
                        pass
            except Exception as e:
                result = False,str(e)
        return result

    def init(self):
        def target_fun():
            self._fresh_window()
            time.sleep(1)
            while 1:
                try:
                    task = self.queue.get(timeout=0.1)
                except Empty:
                    task = None
                if task:
                    print(task, self.chat_list)
                if time.time() - self.chat_list_uptime >= 1:
                    self._fresh_window()
                if task:

                    try:
                        result = self._send(*task)
                    except:
                        pass
                    print(result)
        _thread = threading.Thread(target=target_fun)
        _thread.setDaemon(True)
        _thread.start()


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(353, 303)
        self.plainTextEdit = QtWidgets.QPlainTextEdit(Dialog)
        self.plainTextEdit.setGeometry(QtCore.QRect(20, 60, 311, 101))
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 60, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(90, 20, 261, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(20, 40, 141, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setGeometry(QtCore.QRect(20, 170, 60, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setGeometry(QtCore.QRect(20, 200, 311, 101))
        self.label_5.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_5.setObjectName("label_5")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "接口地址："))
        self.label_2.setText(_translate("Dialog", "http://0.0.0.0:99/send_message"))
        self.label_3.setText(_translate("Dialog", "可发送的对话："))
        self.label_4.setText(_translate("Dialog", "使用说明："))
        self.label_5.setText(_translate("Dialog", "1.本程序可用在32位系统 及64位系统\n"
"2.本程序提供api 对聊天窗口发送内容。\n"
"3.聊天窗口必须从微信windows端单独拖出才能识别\n"
"4.参数传递形式POST\n"
"5.参数共两个：dialog_name,message"))




if __name__ == '__main__':
    app = Flask(__name__)
    api_obj = WeChatApi()
    api_obj.init()

    @app.route('/')
    def index():
        return str('wechat dialog api server')


    @app.route("/send_message", methods=['POST'])
    def send_message():
        status = True
        result = ''
        try:
            assert request.method == 'POST',Exception('please use post method')
            dialog_name = request.form['dialog_name']
            message = request.form['message']
            assert dialog_name and message, Exception('dialog_name message必须全不为空')
            api_obj.send_to_chat_window(dialog_name, message)
            result = "已入队列,正在推送"
        except Exception as e :
            status = False
            result = str(e)
        return json.dumps({'status': status, 'result': result})

    def run_flask():
        app.run('0.0.0.0', 99)
    thread = threading.Thread(target=run_flask)
    thread.setDaemon(True)
    thread.start()

    app = QApplication(['windows微信助手'])
    main_window = QMainWindow()
    ui_dialog = Ui_Dialog()
    ui_dialog.setupUi(main_window)
    main_window.setWindowTitle('windows微信助手')

    def state_sync():
        dialog_list = api_obj.chat_window_titles
        content = ''
        for i in dialog_list:
            content += '%s\n' % i
        content = content.strip()
        if not content:
            content = "暂无可用的对话窗口"
        ui_dialog.plainTextEdit.setPlainText(content)
    state_timer = QtCore.QTimer()
    state_timer.timeout.connect(state_sync)
    state_timer.start(500)
    main_window.show()

    sys.exit(app.exec_())