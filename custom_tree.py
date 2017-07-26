'''
Custom tree class to display a patients data for editing
'''
import sys
from PyQt5.QtWidgets import (QWidget, QTreeWidget, QTreeWidgetItem, QApplication, QVBoxLayout)
from PyQt5 import QtCore,QtGui
import BLDataClasses

class PatientTree(QWidget):
    def __init__(self,pt):
        QWidget.__init__(self)
    
        self.tree = QTreeWidget()
        #self.root = QTreeWidgetItem(self.tree,[' '.join([pt.name,pt.mrn])])
        self.root = self.tree.invisibleRootItem()
        
        self.headers = [
                        'Exam',
                        'Follow-Up',
                        'Name',
                        'Description',
                        'Target',
                        'Sub-Type',
                        'Series',
                        'Slice#',
                        'RECIST Diameter (mm)'
                        ]

        self.headers_item = QTreeWidgetItem(self.headers)

        self.tree.setColumnCount(len(self.headers))
        self.tree.setHeaderItem(self.headers_item)
        self.root.setExpanded(True)

        self.addItems(self.root,pt)
                
        for i in range(0,self.tree.columnCount()):
            self.tree.resizeColumnToContents(i)
        
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def addItems(self,parent,pt):
        '''
        Add items to the table from the patient object
        '''
        for key,exam in pt.exams.items():
            column = 0
            #self.exam_item = QTreeWidgetItem(parent,[', '.join([str(exam.date),str(exam.time),str(exam.modality),str(exam.description)])])
            self.exam_item = QTreeWidgetItem(parent)
            self.exam_item.setText(column,', '.join([str(exam.date),str(exam.modality),str(exam.description)]))
            self.exam_item.setExpanded(True)

            for lesion in exam.lesions:
                column = 1
                if lesion.params['Target'].lower() == 'target' or lesion.params['Target'].lower() == 'non-target':
                    self.param_list = [
                                        lesion.params['Follow-Up'],
                                        lesion.params['Name'],
                                        lesion.params['Description'],
                                        lesion.params['Target'],
                                        lesion.params['Sub-Type'],
                                        lesion.params['Series'],
                                        lesion.params['Slice#'],
                                        round(lesion.params['RECIST Diameter (mm)'],2)
                                        ]
                                        
                    self.lesion_item = QTreeWidgetItem(self.exam_item)
                    for param_str in self.param_list:
                        self.lesion_item.setText(column,str(self.param_list[column-1]))
                        self.lesion_item.setTextAlignment(column,4) #align center of column
                        column += 1
                    self.lesion_item.setFlags(self.lesion_item.flags() | QtCore.Qt.ItemIsEditable)
                    self.lesion_item.setExpanded(True)

#### Test Code ####
if __name__ == "__main__":
    patient = BLDataClasses.Patient('1234567','12-C-1250','Bob Smith',['Field1','Field2'])
    exam = BLDataClasses.Exam('1','123.123.123')
    patient.add_exam({'1':exam})
    lesion = BLDataClasses.Lesion()
    lesion.add_params({'DIAMETER':'5','LOC':'Chest'})
    exam.add_lesion(lesion)

    app = QApplication(sys.argv)
    window = PatientTree(patient)
    window.show()
    sys.exit(app.exec_())
    