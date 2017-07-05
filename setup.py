import sys
import os.path
from cx_Freeze import setup, Executable

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')


base = None
if sys.platform == 'win32':
	base = "Win32GUI"

options = {
    'build_exe': {
        'include_files':[
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),'RECISTForm.docx','readme.txt','icons/'],
    'packages': ['pyqtgraph','PyQt5','pandas','numpy','easygui','openpyxl','docx','lxml._elementpath','dbm']
    }
}

setup(options = options, name = 'ENABLE 2', version = "1.0", description = "ENABLE Interface", executables = [Executable("main.py", base = base)])