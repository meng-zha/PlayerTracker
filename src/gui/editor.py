import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import open3d as o3d
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QGroupBox, QPushButton,\
    QMessageBox, QVBoxLayout, QLineEdit
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal

class Editor(QWidget):
    show_image_signal = pyqtSignal(dict)
    def __init__(self, bevLoader):
        super().__init__()
        self.bevLoader = bevLoader
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window()

        widget = QtWidgets.QWidget()
        hwnd = self.get_hwnd()
        self.window = QtGui.QWindow.fromWinId(hwnd)    
        self.windowcontainer = self.createWindowContainer(self.window, widget)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_vis)
        timer.start(10)

        self.create_panel()
        self.make_out()

    def create_panel(self):
        #delete
        self.delete_line = QLineEdit()
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete)

        self.show_line = QLineEdit()
        self.show_button = QPushButton("Show Points")
        self.show_button.clicked.connect(self.show_pcd)
        self.show_image_button = QPushButton("Show Image")
        self.show_image_button.clicked.connect(self.show_image)
    
    def update_vis(self):
        self.vis.poll_events()
        self.vis.update_renderer()
    
    def get_hwnd(self):
        from subprocess import Popen, PIPE
        hwnd = None
        while hwnd == None:
            proc = Popen('xwininfo -tree -root', stdin=None, stdout=PIPE, stderr=None, shell=True)
            out, err = proc.communicate()
            for window in out.decode('utf-8').split('\n'):
                if 'Open3D' in window:
                    print(window.strip().split(' '))
                    hwnd = int(window.strip().split(' ')[0], 16)
                    return hwnd

    def make_out(self):
        main_layout = QVBoxLayout()

        delete_box = QGroupBox("delete")
        delete_layout = QHBoxLayout()
        delete_layout.addWidget(self.delete_line)
        delete_layout.addWidget(self.delete_button)
        delete_box.setLayout(delete_layout)

        show_box = QGroupBox("show")
        show_layout = QHBoxLayout()
        show_layout.addWidget(self.show_line)
        show_layout.addWidget(self.show_image_button)
        show_layout.addWidget(self.show_button)
        show_box.setLayout(show_layout)

        main_layout.addWidget(delete_box)
        main_layout.addWidget(show_box)
        main_layout.addWidget(self.windowcontainer)
        self.setLayout(main_layout)

    def delete(self):
        try:
            input_text = self.delete_line.text()
            input_list = input_text.split(",")
            trackid, start, end = int(input_list[0]), int(input_list[1]), int(input_list[2])
            self.bevLoader.delete(trackid, start, end)
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()
        
    def show_pcd(self):
        try:
            lidar_path = os.path.join(self.bevLoader.root_path, self.bevLoader.lidar_list[self.bevLoader.start_index])
            points = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points[:,:3])
            self.vis.clear_geometries()
            self.vis.add_geometry(pcd)
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()
    
    def show_image(self):
        try:
            input_text = self.show_line.text()
            input_list = input_text.split(",")
            trackid, start, end = int(input_list[0]), int(input_list[1]), int(input_list[2])
            boxes = self.bevLoader.project_box(trackid, start, end)
            print(boxes)
            if len(boxes)>0:
                self.show_image_signal.emit(boxes)
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()