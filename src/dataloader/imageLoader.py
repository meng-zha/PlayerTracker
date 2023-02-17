import os
import cv2

from PyQt5.QtGui import  QPixmap, QImage

from .parameters import *

class ImageLoader:
    def __init__(self, root_path, resize_ratio = 0.15):
        self.root_path = root_path
        self.image_list = os.listdir(root_path)
        self.camera_index = int(self.root_path[-1])
        self.resize_ratio = resize_ratio
        self.image_list.sort()

    def get_image(self, index):
        img_path = os.path.join(self.root_path, self.image_list[index])
        try:
            img = QImage(img_path)
            return True, QPixmap.fromImage(img).scaledToHeight(img.height()*self.resize_ratio)
        except:
            return False, None
    
    def project_image(self, index, position):
        try:
            img_path = os.path.join(self.root_path, self.image_list[index])
            image = cv2.imread(img_path)
            
            position = np.array(position + [1]).reshape(4,1)
            extra_position = [position]
            extra_position.append(position + np.array([0.25,0,0,0]).reshape(4,1))
            extra_position.append(position + np.array([-0.25,0,0,0]).reshape(4,1))
            extra_position.append(position + np.array([0,0.25,0,0]).reshape(4,1))
            extra_position.append(position + np.array([0,-0.25,0,0]).reshape(4,1))
            position = np.hstack(extra_position)

            lidar_position = np.linalg.inv(Rer) @ position
            local_position = np.linalg.inv(transforms[...,self.camera_index]) @ lidar_position
            camera_position = extrinsics[...,self.camera_index] @ local_position
            camera_cooard = intrinsics[...,self.camera_index] @ camera_position[:3]
            camera_cooard[:2] = camera_cooard[:2]/ camera_cooard[2]

            for i in range(5):
                cv2.circle(image, camera_cooard[:2,i].astype(int), radius = 10, thickness=-1, color=(0,0,255))
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            img = QPixmap.fromImage(QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888)).scaledToHeight(image.shape[0]*self.resize_ratio)
            return True, img
        except:
            return False, None
        
    def project_box(self, box):
        '''
        Args: box: 3*8, corners of the box
        '''
        corners = np.concatenate((box, np.ones((1,box.shape[1]))),axis=0)
        corners = np.linalg.inv(Rer) @ corners
        corners = np.dot(np.linalg.inv(transforms[...,self.camera_index]),corners)
        corners = np.dot(extrinsics[...,self.camera_index], corners)
        img_pts_gt = np.dot(intrinsics[...,self.camera_index], corners[:3,:])
        img_pts_gt = img_pts_gt / img_pts_gt[2,:]
        img_pts_gt = img_pts_gt[0:2,:]
        x_max = np.max(img_pts_gt[0,:])
        x_min = np.min(img_pts_gt[0,:])
        y_max = np.max(img_pts_gt[1,:])
        y_min = np.min(img_pts_gt[1,:])

        return [int(x_min), int(y_min), int(x_max), int(y_max)]

    def project_boxes(self, boxes):
        total_img = np.ones(np.array([240, (120+20)*3, 3]), dtype = np.uint8)*255
        indices = 0
        for ind in boxes.keys():
            box = self.project_box(boxes[ind])
            img_path = os.path.join(self.root_path, self.image_list[ind])
            image = cv2.imread(img_path)
            try:
                print(image[box[1]:box[3],box[0]:box[2]])
                total_img[:,10+140*indices:10+140*indices+120] = cv2.resize(image[box[1]:box[3],box[0]:box[2]],(120,240))
                indices+=1
            except:
                indices+=1
        return total_img