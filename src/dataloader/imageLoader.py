import os

from PyQt5.QtGui import  QPixmap, QImage

class ImageLoader:
    def __init__(self, root_path):
        self.root_path = root_path
        self.image_list = os.listdir(root_path)
        self.image_list.sort()

    def get_image(self, index):
        img_path = os.path.join(self.root_path, self.image_list[index])
        try:
            img = QImage(img_path)
            return True, QPixmap.fromImage(img)
        except:
            return False, None
