import os
import numpy as np
import matplotlib.pyplot as plt
import cv2

from PyQt5.QtGui import  QPixmap, QImage

class BEVLoader:
    def __init__(self, root_path, detection_path, resize_ratio = 30):
        self.root_path = root_path
        self.lidar_list = os.listdir(root_path)
        self.lidar_list.sort()

        self.resize_ratio = resize_ratio
        self.x_range = [0,40]
        self.z_range = [-1.3,1]
        self.y_range = [-17,3]
        self.img_shape = ((self.y_range[1] - self.y_range[0])*resize_ratio,(self.x_range[1]-self.x_range[0])*resize_ratio,3)
        self.img = np.zeros(self.img_shape, dtype = np.uint8)
        self.points = np.zeros(self.img_shape, dtype = np.uint8)
        self.traj = np.zeros(self.img_shape, dtype = np.uint8)
        self.marker = np.zeros(self.img_shape, dtype = np.uint8)

        self.start_index = 0

        self.tracking = np.loadtxt(detection_path, delimiter=' ', dtype=np.float64)
        self.colormap = plt.get_cmap('Paired')
        self.refactor_tracking()

    def reset(self, start_index=0):
        self.img = np.zeros(self.img_shape, dtype = np.uint8)
        self.points = np.zeros(self.img_shape, dtype = np.uint8)
        self.traj = np.zeros(self.img_shape, dtype = np.uint8)
        self.marker = np.zeros(self.img_shape, dtype = np.uint8)
        self.start_index = start_index
    
    def refactor_tracking(self):
        self.track_ids = set(self.tracking[:,-1])
        self.trajectories = dict()
        for track_id in self.track_ids:
            self.trajectories[track_id] = self.tracking[self.tracking[:,-1] == track_id]
    
    def filter(self, points):
        x_filter = np.logical_and((points[:,0] > self.x_range[0]), (points[:,0] < self.x_range[1]))
        y_filter = np.logical_and((points[:,1] > self.y_range[0]), (points[:,1] < self.y_range[1]))
        z_filter = np.logical_and((points[:,2] > self.z_range[0]), (points[:,2] < self.z_range[1]))
        all_filter = np.logical_and(x_filter, y_filter, z_filter)
        indices = np.argwhere(all_filter)[...,0]
        return indices

    def get_bev_image(self, index):
        lidar_path = os.path.join(self.root_path, self.lidar_list[index])
        try:
            points = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
            indices = self.filter(points)
            points = points[indices]

            points[:,0] = (points[:,0] - self.x_range[0])*self.resize_ratio
            points[:,1] = (points[:,1] - self.y_range[0])*self.resize_ratio
            points[:,2] = (points[:,2] - self.z_range[0])/(self.z_range[1] - self.z_range[0])*255
            self.points[(points[:,1]).astype(int),(points[:,0]).astype(int)] = points[:,2:3]
            return True
        except:
            return False

    def get_traj_image(self, index):
        self.marker = np.zeros(self.img_shape, dtype = np.uint8)
        if index <= self.start_index:
            return
        for track_id in self.track_ids:
            trajectory = self.trajectories[track_id]
            traj = trajectory[(trajectory[:,0] >= (index-1))*(trajectory[:,0] <= index)][:,1:3]
            traj[:,0] = (traj[:,0] - self.x_range[0])*self.resize_ratio
            traj[:,1] = (traj[:,1] - self.y_range[0])*self.resize_ratio
            cv2.polylines(self.traj, [traj.astype(int)], isClosed=0, color=np.array(self.colormap(track_id/10)[:3])*255, thickness=5)

            box = trajectory[trajectory[:,0] == index]
            if len(box) > 0:
                box = box[0, 1:3]
                start_point = (int((box[0] - 0.35 - self.x_range[0])*self.resize_ratio), int((box[1]- 0.35 - self.y_range[0])*self.resize_ratio))
                end_point = (int((box[0] + 0.35 - self.x_range[0])*self.resize_ratio), int((box[1] + 0.35 - self.y_range[0])*self.resize_ratio))
                cv2.rectangle(self.marker,start_point,end_point,np.array(self.colormap(track_id/10)[:3])*255,0)
                cv2.putText(self.marker,str(int(track_id)),(max([start_point[0],0]), max([start_point[1],0])),cv2.FONT_HERSHEY_COMPLEX,0.8,\
                    np.array(self.colormap(track_id/10)[:3])*255,1)

    def get_image(self, index):
        success = self.get_bev_image(index)
        self.get_traj_image(index)
        self.img = cv2.addWeighted(self.points, 1, self.traj, 1,0)
        self.img = cv2.addWeighted(self.img, 1, self.marker, 1,0)
        img = QPixmap.fromImage(QImage(self.img.data, self.img.shape[1], self.img.shape[0], QImage.Format_RGB888))
        return success, img