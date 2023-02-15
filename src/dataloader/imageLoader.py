import os

from PyQt5.QtGui import  QPixmap, QImage

class ImageLoader:
    def __init__(self, root_path, resize_ratio = 0.15):
        self.root_path = root_path
        self.image_list = os.listdir(root_path)
        self.resize_ratio = resize_ratio
        self.image_list.sort()

    def get_image(self, index):
        img_path = os.path.join(self.root_path, self.image_list[index])
        try:
            img = QImage(img_path)
            return True, QPixmap.fromImage(img).scaledToHeight(img.height()*self.resize_ratio)
        except:
            return False, None
