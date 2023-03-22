
import cv2
import threading
from PyQt5.QtCore import QFile
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QImage, QPixmap

import os
import numpy as np
import struct
from tqdm import tqdm
from copy import deepcopy
import argparse
import random,time
import open3d as o3d

def get_random_color():
    """获取一个随机的颜色"""
    r = lambda: random.uniform(0,255)
    return [r(),r(),r()]

tra_color = []
for k in range(1000):
    color_random = get_random_color()
    tra_color.append(color_random)
    
def read_bin_velodyne(path):
    pc_list=[]
    with open(path,'rb') as f:
        content=f.read()
        pc_iter=struct.iter_unpack('ffff',content)
        for idx,point in enumerate(pc_iter):
            pc_list.append([point[0],point[1],point[2]])
    return np.asarray(pc_list,dtype=np.float32)

def GetAnnotBoxLoc(box):
    r = box
    ObjBndBoxSet={}
    for j in range(len(r)):       
        BndBoxLoc = [r[j,0]-0.35, r[j,1]+17-0.35, r[j,0]+0.35,r[j,1]+17+0.35]
        BndBoxLoc = np.asarray(BndBoxLoc)
        BndBoxLoc = np.asarray(BndBoxLoc*40, dtype=np.int32)
        # print(BndBoxLoc)
        ObjBndBoxSet[str(int(r[j,-1]))] = BndBoxLoc
    
    return ObjBndBoxSet    

##draw all bndbox on image
def DrawObjectBox(im,ObjBndBoxSet,BoxColor):
    for ObjName,BndBox in ObjBndBoxSet.items():
        # print(ObjName,BndBoxSet)
        
        cv2.rectangle(im,(BndBox[0],BndBox[1]),(BndBox[2],BndBox[3]),BoxColor,0)
        dsptxt='{:s}'.format(ObjName)
        # cv2.putText(im,dsptxt,(max([int((BndBox[0]+BndBox[2])/2-30),0]), max([int(BndBox[3]-30),0])),cv2.FONT_HERSHEY_COMPLEX,0.8,(0,0,255),1)

def draw_tra(im,pred_tra,frame_):
    # ind_pred = (pred[:,0] < frame) * (pred[:,0] > frame-100)
    # pred_tra = pred[ind_pred,:]
    
    ind_tras = pred_tra[:,-1].reshape(-1,).tolist()
    ind_tras = list(set(ind_tras)) #quchong
    for ind_tra in ind_tras:
        # ind = (pred_tra[:,0] < frame_+1) * (pred_tra[:,0] > frame_-100)
        ind = (pred_tra[:,0] < frame_+1) *  (pred_tra[:,-1] == ind_tra) * (pred_tra[:,0] > frame_-100)
        points = pred_tra[ind,1:3]
        points_tra = np.concatenate((points[:,[0]]*40, (points[:,[1]]+17)*40), axis=1).reshape(1,-1,2)
        if ind.sum()>1:
            color_id = pred_tra[ind,-1].astype(int)[0]
            try:
                tra_color_one = tra_color[color_id]
            except:
                from IPython import embed
                embed()
                exit()
        else:
            tra_color_one = [0,0,0]
        # from IPython import embed
        # embed()
        # exit()
        cv2.polylines(im, [points_tra.astype(int)], isClosed=0, color=tra_color_one, thickness=1)        
        dsptxt = str(int(ind_tra))
        # print(ind.sum())
        cv2.putText(im,dsptxt,(max([int(points_tra[0,-1,0]),0]), max([int(points_tra[0,-1,1]-10),0])),cv2.FONT_HERSHEY_COMPLEX,0.8,(0,0,255),1)

root = '../../eastern_ground_20220626_first_lidar/points_bin_rot' #点云路径
pred_path = '../../basketball_outputs/3dssd_300_60-100e_0.5_ab.txt'
filename=os.listdir(root)
filename.sort(key=lambda x: int(x[:-4]))
pred =  np.loadtxt(pred_path, delimiter=' ', dtype=np.float64)

class Display:
    def __init__(self, ui, mainWnd,pred):
        self.ui = ui
        self.mainWnd = mainWnd
        self.pred = pred
 
        # 信号槽设置
        ui.Open.clicked.connect(self.Open)
        ui.Close.clicked.connect(self.Close)
        ui.delete_pushButton.clicked.connect(self.delete)
        ui.rename_pushButton.clicked.connect(self.rename)
        ui.inter_pushButton.clicked.connect(self.interpolate)
        ui.trans_pushButton.clicked.connect(self.translate)
        ui.copy_pushButton.clicked.connect(self.copy)
        ui.modulate_pushButton.clicked.connect(self.modulate)
        ui.frame_slider.valueChanged.connect(self.frame_slider)
        ui.save.clicked.connect(self.save)
        ui.select.clicked.connect(self.select)
 
        # 创建一个关闭事件并设为未触发
        self.stopEvent = threading.Event()
        self.stopEvent.clear()
        self.ui.frame_begin.setPlainText('0')
        self.ui.delete_input.setPlainText('id, begin, end')
        self.ui.rename_input.setPlainText('id_old, id_new, begin, end')
        self.ui.inter_input.setPlainText('id, begin, end')
        self.ui.trans_input.setPlainText('id, begin, end, dx, dy')
        self.ui.copy_input.setPlainText('id, begin, end, dx, dy')
        self.ui.modulate_input.setPlainText('id, begin, end')

        # 2.追加文本
        # self.ui.frame_begin.append('我是追加的文本')

        # 3.获取文本
        # text_edit_text = self.ui.frame_begin.toPlainText()
        # print(text_edit_text)
        # self.ui.frame_begin.clear()
 
    def Open(self):
        # 创建视频显示线程
        th = threading.Thread(target=self.Display)
        th.start()
        # self.ui.frame_begin.clear()
        # self.ui.frame_begin.setPlainText('begin')
 
    def Close(self):
        # 关闭事件设为触发，关闭视频播放
        self.stopEvent.set()
 
    def frame_slider(self):
        frame_str = str(self.ui.frame_slider.value())
        self.ui.frame_begin.setPlainText(frame_str)
            
    def Display(self):
        self.ui.Open.setEnabled(False)
        self.ui.Close.setEnabled(True)
        frame = int(self.ui.frame_begin.toPlainText())
 
        for k in range(frame,2000):
            pcd_path = os.path.join(root, filename[k])
            # success, frame = self.cap.read()
            # RGB转BGR
            points = read_bin_velodyne(pcd_path)
            # print(points)
            x_points = points[:, 0]
            y_points = points[:, 1]
            z_points = points[:, 2]

            f_filt = np.logical_and((x_points > -50), (x_points < 50))
            s_filt = np.logical_and((z_points > -1.15), (z_points < 0.7))
            filter = np.logical_and(f_filt, s_filt)
            indices = np.argwhere(filter)

            x_points = x_points[indices]
            y_points = y_points[indices]
            z_points = z_points[indices]

            x_img = (x_points*40).astype(np.int32)
            y_img = ((y_points+17)*40).astype(np.int32)      

            pixel_values = np.clip(z_points,-1,3)
            pixel_values = 255 - ((pixel_values +1.3) / 2) * 255
            im=np.ones([720,1400],dtype=np.uint8)* 255
            im[y_img, x_img] = pixel_values
            im[y_img-1, x_img] = pixel_values
            im[y_img-1, x_img-1] = pixel_values
            im[y_img, x_img-1] = pixel_values
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
            
            box = self.pred[self.pred[:,0]==k,1:9]
            ObjBndBoxSet=GetAnnotBoxLoc(box)
            DrawObjectBox(im, ObjBndBoxSet, (0,255,0))
            ind_pred = (self.pred[:,0] < k+1) * (self.pred[:,0] > k-100)
            pred_tra = self.pred[ind_pred,:]
            draw_tra(im,pred_tra,k)
            dsptxt=str(int(k))
            cv2.putText(im,dsptxt,(500,100),cv2.FONT_HERSHEY_COMPLEX,3,(0,255,255),3)
            frame = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
            img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.ui.DispalyLabel.setPixmap(QPixmap.fromImage(img))

            # if self.isCamera:
            #     cv2.waitKey(1)
            # else:
            #     cv2.waitKey(int(1000 / self.frameRate))
 
            # 判断关闭事件是否已触发
            if True == self.stopEvent.is_set():
                break
            cv2.waitKey(30)
        self.stopEvent.clear()
        # self.ui.DispalyLabel.clear()
        self.ui.Close.setEnabled(False)
        self.ui.Open.setEnabled(True)
        
    def delete(self):
        try:
            input_text = self.ui.delete_input.toPlainText()
            input_list = input_text.split(",")
            ind_del = (self.pred[:,0] < int(input_list[2])+1) * (self.pred[:,-1] == int(input_list[0])) * (self.pred[:,0] > int(input_list[1])-1)
            self.pred = np.delete(self.pred, ind_del, axis=0)
            self.ui.delete_input.setPlainText('id, begin, end')
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()
        
    def rename(self):
        try:
            input_text = self.ui.rename_input.toPlainText()
            input_list = input_text.split(",")
            ind_re = (self.pred[:,0] < int(input_list[3])+1) * (self.pred[:,-1] == int(input_list[0])) * (self.pred[:,0] > int(input_list[2])-1)
            self.pred[ind_re,-1] = int(input_list[1])
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()
    
    def interpolate(self): 
        try:   
            input_text = self.ui.inter_input.toPlainText()
            input_list = input_text.split(",")
            x_begin = 0
            x_end = 0
            y_begin = 0
            y_end = 0
            flag = 0
            result_i = []
            ind_id = (self.pred[:,-1] == int(input_list[0]))
            pred_i = self.pred[ind_id]
            # from IPython import embed
            # embed()
            # exit()        
            ind_i = (self.pred[:,0] < int(input_list[2])+1) * (self.pred[:,-1] == int(input_list[0])) * (self.pred[:,0] > int(input_list[1])-1)
            for i in tqdm(range(int(input_list[1]),int(input_list[2])+1)):
                box = pred_i[pred_i[:,0]==i,0:10].reshape(-1,9)
                box_f = pred_i[pred_i[:,0]==i+1,0:10]
                box_b = pred_i[pred_i[:,0]==i-1,0:10].reshape(-1,9)
                print(box_b)
                result_i.append(box)
                if len(box) < 1:
                    if flag == 0:
                        x_begin = box_b[0,1]
                        y_begin = box_b[0,2]
                    flag += 1
                    if len(box_f) != 0:
                        x_end = box_f[0,1]
                        y_end = box_f[0,2]
                        xp = [0,1]
                        fp = [x_begin,x_end]
                        yp = [y_begin,y_end]
                        x = [k/(flag+1) for k in range(1,flag+1)]
                        
                        flag = 0
                        x_chazhi = np.interp(x, xp, fp)
                        y_chazhi = np.interp(x, xp, yp)
                        for j in range(len(x)):
                            box_chazhi = box_f.copy().reshape(-1,9)
                            box_chazhi[0,1] = x_chazhi[j]
                            box_chazhi[0,2] = y_chazhi[j]
                            # box_chazhi[0,1] = x_chazhi[j]
                            box_chazhi[0,0] = box_chazhi[0,0]-len(x)+j
                            result_i.append(box_chazhi)
            result_i = np.concatenate(result_i,axis=0)
            self.pred = np.delete(self.pred, ind_i, axis=0)
            self.pred = np.concatenate((self.pred,result_i), axis=0)
            index = np.lexsort((self.pred[:,0],))
            self.pred = self.pred[index]   
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()     
        
    def translate(self):
        try:
            input_text = self.ui.trans_input.toPlainText()
            input_list = input_text.split(",")
            ind_t = (self.pred[:,0] < int(input_list[2])+1) * (self.pred[:,-1] == int(input_list[0])) * (self.pred[:,0] > int(input_list[1])-1)
            self.pred[ind_t] += [0,float(input_list[3]),float(input_list[4]),0,0,0,0,0,0]
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()
                    
    def copy(self):
        try:
            input_text = self.ui.copy_input.toPlainText()
            input_list = input_text.split(",")
            ind_c = (self.pred[:,0] < int(input_list[2])+1) * (self.pred[:,-1] == int(input_list[0])) * (self.pred[:,0] > int(input_list[1])-1)
            pred_copy = self.pred[ind_c].copy()

            pred_copy = pred_copy + [0,float(input_list[3]),float(input_list[4]),0,0,0,0,0,0]
            pred_copy[:,-1] = np.max(self.pred[:,-1]) + 1
            self.pred = np.concatenate((self.pred,pred_copy), axis=0)
            index = np.lexsort((self.pred[:,0],))
            self.pred = self.pred[index]        
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()
                    
    def modulate(self):
        try:
            input_text = self.ui.modulate_input.toPlainText()
            input_list = input_text.split(",")
            ind_m = (self.pred[:,0] < int(input_list[2])+1) * (self.pred[:,-1] == int(input_list[0])) * (self.pred[:,0] > int(input_list[1])-1)
            pred_m = self.pred[ind_m]
            for i in tqdm(range(int(input_list[1]),int(input_list[2])+1)):
                # from IPython import embed
                # embed()
                # exit()
                box_i = pred_m[pred_m[:,0]==i]
                if len(box_i) == 0:
                    continue
                box_i = box_i.reshape(1,-1)
                score = np.zeros((20,20))
                pcd = o3d.geometry.PointCloud()
                line_set = o3d.geometry.LineSet()
                pcd_path = os.path.join(root, filename[i])
                example = read_bin_velodyne(pcd_path)
                example = example[example[:,-1]>-1.15]
                example = example[example[:,-1]<1]
                pcd.points = o3d.utility.Vector3dVector(example)
                for x_int in range(20):
                    for y_int in range(20):
                        dx = x_int / 20 - 0.5
                        dy = y_int / 20 - 0.5
                        # from IPython import embed
                        # embed()
                        # exit()
                        x_cen = box_i[0,1] + dx
                        y_cen = box_i[0,2] + dy
                        inbox = (example[:,0]>x_cen-0.35) * (example[:,0]<x_cen+0.35) * \
                            (example[:,1]>y_cen-0.35) * (example[:,1]<y_cen+0.35)
                        score[x_int,y_int] = np.sum(inbox)
                max_x, max_y = np.unravel_index(np.argmax(score), score.shape)
                ind_md = (self.pred[:,0]==i) * (self.pred[:,-1]==int(input_list[1]))
                self.pred[ind_md] += [0, max_x/ 20 - 0.5, max_y / 20 - 0.5,0,0,0,0,0,0]
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误,请重新输入')
            msg_box.exec_()
            
    def save(self):
        file_path, _ = QFileDialog.getOpenFileName(self.mainWnd, "选择文件")
        f = open(file_path,'w')
        np.savetxt(f, self.pred, delimiter=" ") 
        f.close()
        
    def select(self):
        fileName, fileType = QFileDialog.getOpenFileName(self.mainWnd, '选择文件', '', '*.txt')