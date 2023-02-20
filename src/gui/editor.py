import os
import sys
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
        print(sys.platform)
        if sys.platform == "win32":
            # if windows
            import win32gui
            hwnd = win32gui.FindWindowEx(0, 0, None, "Open3D")
        else:
            # if linux
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

        self.merge_line = QLineEdit()
        self.merge_button = QPushButton("Merge")
        self.merge_button.clicked.connect(self.merge)

        self.split_line = QLineEdit()
        self.split_button = QPushButton("Split")
        self.split_button.clicked.connect(self.split)

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

        merge_box = QGroupBox("merge")
        merge_layout = QHBoxLayout()
        merge_layout.addWidget(self.merge_line)
        merge_layout.addWidget(self.merge_button)
        merge_box.setLayout(merge_layout)

        split_box = QGroupBox("split")
        split_layout = QHBoxLayout()
        split_layout.addWidget(self.split_line)
        split_layout.addWidget(self.split_button)
        split_box.setLayout(split_layout)

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

    def merge(self):
        try:
            input_text = self.merge_line.text()
            input_list = input_text.split(",")
            trackid_master, trackid_slave, start, end = int(input_list[0]), int(input_list[1]), int(input_list[2]), int(input_list[3])
            self.bevLoader.merge(trackid_master, trackid_slave, start, end)
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()

    def split(self):
        try:
            input_text = self.merge_line.text()
            input_list = input_text.split(",")
            trackid, frame = int(input_list[0]), int(input_list[1])
            self.bevLoader.split(trackid, frame)
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