# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_logindialog(object):
    def setupUi(self, logindialog):
        logindialog.setObjectName("logindialog")
        logindialog.resize(500, 566)
        self.ENABLE_logo = QtWidgets.QLabel(logindialog)
        self.ENABLE_logo.setGeometry(QtCore.QRect(125, 40, 250, 250))
        self.ENABLE_logo.setText("")
        self.ENABLE_logo.setPixmap(QtGui.QPixmap("../../icons/enable_icon.png"))
        self.ENABLE_logo.setScaledContents(True)
        self.ENABLE_logo.setObjectName("ENABLE_logo")
        self.welcome_label = QtWidgets.QLabel(logindialog)
        self.welcome_label.setGeometry(QtCore.QRect(50, 360, 391, 20))
        self.welcome_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.welcome_label.setText("")
        self.welcome_label.setAlignment(QtCore.Qt.AlignCenter)
        self.welcome_label.setObjectName("welcome_label")
        self.connecting_label = QtWidgets.QLabel(logindialog)
        self.connecting_label.setGeometry(QtCore.QRect(90, 400, 311, 20))
        self.connecting_label.setText("")
        self.connecting_label.setAlignment(QtCore.Qt.AlignCenter)
        self.connecting_label.setObjectName("connecting_label")
        self.btn_log_in = QtWidgets.QPushButton(logindialog)
        self.btn_log_in.setGeometry(QtCore.QRect(200, 300, 93, 28))
        self.btn_log_in.setObjectName("btn_log_in")
        self.btn_offline_mode = QtWidgets.QPushButton(logindialog)
        self.btn_offline_mode.setEnabled(False)
        self.btn_offline_mode.setGeometry(QtCore.QRect(200, 490, 93, 28))
        self.btn_offline_mode.setObjectName("btn_offline_mode")
        self.count_label = QtWidgets.QLabel(logindialog)
        self.count_label.setEnabled(True)
        self.count_label.setGeometry(QtCore.QRect(180, 440, 131, 20))
        self.count_label.setText("")
        self.count_label.setAlignment(QtCore.Qt.AlignCenter)
        self.count_label.setObjectName("count_label")

        self.retranslateUi(logindialog)
        QtCore.QMetaObject.connectSlotsByName(logindialog)

    def retranslateUi(self, logindialog):
        _translate = QtCore.QCoreApplication.translate
        logindialog.setWindowTitle(_translate("logindialog", "ENABLE 2.0"))
        self.btn_log_in.setText(_translate("logindialog", "Log in"))
        self.btn_offline_mode.setText(_translate("logindialog", "Offline Mode"))

