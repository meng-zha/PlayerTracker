import os
import numpy as np

from PyQt5.QtGui import  QPixmap, QImage

class BEVLoader:
    def __init__(self, root_path):
        self.root_path = root_path
        self.lidar_list = os.listdir(root_path)
        self.lidar_list.sort()

        self.x_range = [0,50]
        self.z_range = [-1.3,1]
        self.y_range = [-17,100]
        self.img_shape = (720,1400)
    
    def filter(self, points):
        x_filter = np.logical_and((points[:,0] > self.x_range[0]), (points[:,0] < self.x_range[1]))
        y_filter = np.logical_and((points[:,1] > self.y_range[0]), (points[:,1] < self.y_range[1]))
        z_filter = np.logical_and((points[:,2] > self.z_range[0]), (points[:,2] < self.z_range[1]))
        all_filter = np.logical_and(x_filter, y_filter, z_filter)
        indices = np.argwhere(all_filter)[...,0]
        return indices

    def get_image(self, index):
        lidar_path = os.path.join(self.root_path, self.lidar_list[index])
        try:
            points = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
            indices = self.filter(points)
            points = points[indices]

            img = np.zeros(self.img_shape, dtype = np.uint8)
            points[:,0] = (points[:,0] - self.x_range[0])*40
            points[:,1] = (points[:,1] - self.y_range[0])*40
            points[:,2] = (points[:,2] - self.z_range[0])/(self.z_range[1] - self.z_range[0])*255
            img[(points[:,1]).astype(int),(points[:,0]).astype(int)] = points[:,2]
            img = QPixmap.fromImage(QImage(img.data, img.shape[1], img.shape[0], QImage.Format_Grayscale8))
            return True, img
        except:
            return False, None
