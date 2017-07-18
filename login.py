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
        self.pushButton = QtWidgets.QPushButton(logindialog)
        self.pushButton.setGeometry(QtCore.QRect(302, 520, 111, 28))
        self.pushButton.setObjectName("pushButton")
        self.verticalLayoutWidget = QtWidgets.QWidget(logindialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(110, 310, 281, 92))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.lineEdit = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout_2.addWidget(self.lineEdit_2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.pushButton_2 = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout.addWidget(self.pushButton_2)

        self.retranslateUi(logindialog)
        QtCore.QMetaObject.connectSlotsByName(logindialog)

    def retranslateUi(self, logindialog):
        _translate = QtCore.QCoreApplication.translate
        logindialog.setWindowTitle(_translate("logindialog", "ENABLE 2.0"))
        self.pushButton.setText(_translate("logindialog", "Request Access"))
        self.label_2.setText(_translate("logindialog", "Username:"))
        self.label_3.setText(_translate("logindialog", "Password:"))
        self.pushButton_2.setText(_translate("logindialog", "Log in"))

