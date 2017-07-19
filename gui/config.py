# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'configuration.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_configuration(object):
    def setupUi(self, configuration):
        configuration.setObjectName("configuration")
        configuration.resize(741, 262)
        self.horizontalLayoutWidget_3 = QtWidgets.QWidget(configuration)
        self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(50, 70, 641, 41))
        self.horizontalLayoutWidget_3.setObjectName("horizontalLayoutWidget_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_3)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.horizontalLayoutWidget_3)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.bl_directory = QtWidgets.QLineEdit(self.horizontalLayoutWidget_3)
        self.bl_directory.setObjectName("bl_directory")
        self.horizontalLayout_3.addWidget(self.bl_directory)
        self.btn_bl_directory = QtWidgets.QPushButton(self.horizontalLayoutWidget_3)
        self.btn_bl_directory.setObjectName("btn_bl_directory")
        self.horizontalLayout_3.addWidget(self.btn_bl_directory)
        self.horizontalLayoutWidget_4 = QtWidgets.QWidget(configuration)
        self.horizontalLayoutWidget_4.setGeometry(QtCore.QRect(50, 120, 641, 41))
        self.horizontalLayoutWidget_4.setObjectName("horizontalLayoutWidget_4")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(self.horizontalLayoutWidget_4)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.output_directory = QtWidgets.QLineEdit(self.horizontalLayoutWidget_4)
        self.output_directory.setObjectName("output_directory")
        self.horizontalLayout_4.addWidget(self.output_directory)
        self.btn_output_directory = QtWidgets.QPushButton(self.horizontalLayoutWidget_4)
        self.btn_output_directory.setObjectName("btn_output_directory")
        self.horizontalLayout_4.addWidget(self.btn_output_directory)
        self.horizontalLayoutWidget_5 = QtWidgets.QWidget(configuration)
        self.horizontalLayoutWidget_5.setGeometry(QtCore.QRect(50, 170, 641, 41))
        self.horizontalLayoutWidget_5.setObjectName("horizontalLayoutWidget_5")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_5)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.horizontalLayoutWidget_5)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.db_path = QtWidgets.QLineEdit(self.horizontalLayoutWidget_5)
        self.db_path.setEnabled(False)
        self.db_path.setObjectName("db_path")
        self.horizontalLayout_5.addWidget(self.db_path)
        self.btn_db_path = QtWidgets.QPushButton(self.horizontalLayoutWidget_5)
        self.btn_db_path.setObjectName("btn_db_path")
        self.horizontalLayout_5.addWidget(self.btn_db_path)
        self.label = QtWidgets.QLabel(configuration)
        self.label.setGeometry(QtCore.QRect(50, 20, 111, 41))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayoutWidget_3.raise_()
        self.horizontalLayoutWidget_4.raise_()
        self.horizontalLayoutWidget_5.raise_()
        self.label.raise_()

        self.retranslateUi(configuration)
        QtCore.QMetaObject.connectSlotsByName(configuration)

    def retranslateUi(self, configuration):
        _translate = QtCore.QCoreApplication.translate
        configuration.setWindowTitle(_translate("configuration", "Configure Settings"))
        self.label_3.setText(_translate("configuration", "Bookmark List Directory:"))
        self.btn_bl_directory.setText(_translate("configuration", "Select"))
        self.label_4.setText(_translate("configuration", "Output Directory:"))
        self.btn_output_directory.setText(_translate("configuration", "Select"))
        self.label_5.setText(_translate("configuration", "Database Path"))
        self.btn_db_path.setText(_translate("configuration", "Select"))
        self.label.setText(_translate("configuration", "Settings:"))

