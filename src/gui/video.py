import time
import numpy as np
import cv2
import threading

from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt5.QtGui import  QPixmap, QImage
from PyQt5.QtCore import Qt, QThread

class VideoPlayerThread(QThread):
    def __init__(self, dataloader):
        super().__init__()
        self.player = VideoPlayerWidget(dataloader)
    
    def run(self):
        self.player.show_video_images()

class VideoPlayerWidget(QWidget):
    def __init__(self, dataloader):
        super().__init__()
        self.frame_index = 0
        self.dataloader = dataloader
        self.clock = time.time()

        self.init_player()

    def _ndarray_to_qimage(self, arr):
        h, w = arr.shape[:2]
        return QImage(arr.data, w, h, w*3, QImage.Format_RGB888).rgbSwapped()
    
    def _qimage_to_qpixmap(self, qimg):
        return QPixmap.fromImage(qimg)
    
    def init_player(self):
        self.picture = QLabel(self)
        image_layout = QGridLayout()
        image_layout.addWidget(self.picture,1,1)
        image_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(image_layout)
        # set image
        success, image = self.dataloader.get_image(self.frame_index)
        print(image.width(), image.height())
        self.setFixedSize(image.width(), image.height())
        if success:
            self.picture.setPixmap(image)
    
    def show_video_images(self):
        self.clock = time.time()
        if self.dataloader is not None:
            success, frame = self.dataloader.get_image(self.frame_index)
            if success:
                self.frame_index += 1
                self.picture.setPixmap(frame)
            else:
                print("read failed, no frame data")
                success, frame = self.dataloader.get_image(self.frame_index)
                if not success:
                    print("play finished")  # 判断本地文件播放完毕
                return
        else:
            print("open file or capturing device error, init again")
