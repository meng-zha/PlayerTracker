import sys
import Ui_DisplayUI
from PyQt5.QtWidgets import QApplication, QMainWindow
from VideoDisplay import Display
import numpy as np
 
if __name__ == '__main__':
    pred_path = '../../basketball_outputs/3dssd_300_60-100e_0.5_ab.txt'
    pred =  np.loadtxt(pred_path, delimiter=' ', dtype=np.float64)
    
    app = QApplication(sys.argv)
    mainWnd = QMainWindow()
    ui = Ui_DisplayUI.Ui_MainWindow()
 
    # 可以理解成将创建的 ui 绑定到新建的 mainWnd 上
    ui.setupUi(mainWnd)
 
    display = Display(ui, mainWnd,pred)
 
    mainWnd.show()
 
    sys.exit(app.exec_())