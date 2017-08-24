'''
Generic plot widget
'''
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rc

from PyQt5.QtWidgets import (QLabel, QFontDialog, QListWidgetItem, QColorDialog, QHeaderView, QApplication, QDialog, QWidget, QPushButton, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QComboBox)
from PyQt5 import QtCore, QtGui

import numpy as np
import random

class Plotter(QWidget):
    def __init__(self,parent):
        super(Plotter,self).__init__(parent)

        #creating plotting widget
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas,self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

    def plot_this(self,x_series,y_series,title,xlab,ylab):
        '''
        Plot y vs. x as line plot
        '''
        self.fontsize = 15
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        x_series = np.array(x_series)
        A = np.vstack([x_series, np.ones(len(x_series))]).T

        self.ax.set_title(title, fontsize = self.fontsize)
        self.ax.set_xlabel(xlab, fontsize = self.fontsize)
        self.ax.set_ylabel(ylab, fontsize = self.fontsize)

        try:
            y_series[0][0]
            y_array = np.array(y_series)
            for i in range(len(y_array[0])):
                clr = "#%06x" % random.randint(0, 0xFFFFFF)
                m,c = np.linalg.lstsq(A,y_array[:,i])[0]

                self.ax.plot(x_series,y_array[:,i], c=clr, linestyle='solid',marker='o')
                self.ax.plot(x_series,m*x_series + c, c=clr, label='LinReg')
                self.ax.legend()

        except:
            m,c = np.linalg.lstsq(A,y_series)[0]
            clr = "#%06x" % random.randint(0, 0xFFFFFF)
            self.ax.plot(x_series,y_series,linestyle='solid',marker='o', c=clr)
            self.ax.plot(x_series,m*x_series + c, label='LinReg', c=clr)

        self.ax.grid(color = 'k', axis = 'y', alpha=0.25)
        self.canvas.draw()
