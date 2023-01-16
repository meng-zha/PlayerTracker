import os

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QGroupBox, QPushButton,\
    QStyle, QVBoxLayout, QLineEdit
from PyQt5.QtCore import Qt
from concurrent.futures import ThreadPoolExecutor

from src.gui import VideoPlayerWidget, VideoPlayerThread
from src.utils import VideoTimer
from src.dataloader import BEVLoader, ImageLoader

class ControllerWidget(QWidget):
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2
    def __init__(self, root_path, fps=10):
        super().__init__()
        self.root_path = root_path
        self.status = self.STATUS_INIT

        self.executor = ThreadPoolExecutor(max_workers=5)
        self.timer = VideoTimer()
        self.timer.set_fps(fps)
        self.image_player = []
        self.timer.timeSignal.signal.connect(self.update)
        for i in range(4):
            imageLoader = ImageLoader(os.path.join(root_path,  f"camera_{i}"))
            self.image_player.append(VideoPlayerWidget(imageLoader))
        
        bevLoader = BEVLoader(os.path.join(root_path, "pointclouds"))
        self.bev_player = VideoPlayerWidget(bevLoader)
    
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.switch_video)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_button.clicked.connect(self.stop)

        self.terminal_line = QLineEdit()
        self.terminal_line.setReadOnly(False)
        self.make_layout()

    def update(self):
        for i in range(4):
            self.executor.submit(self.image_player[i].show_video_images)
        self.executor.submit(self.bev_player.show_video_images)

    def make_layout(self):
        main_layout = QHBoxLayout()

        bev_box = QGroupBox("bev")
        bev_layout = QVBoxLayout()
        bev_layout.addWidget(self.bev_player)
        bev_box.setLayout(bev_layout)
        main_layout.addWidget(bev_box)

        image_box = QGroupBox("images")
        image_layout = QGridLayout()
        for i in range(4):
            image_layout.addWidget(self.image_player[i], i//2, i%2)
        image_box.setLayout(image_layout)
        main_layout.addWidget(image_box)

        control_box = QGroupBox("control")
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.terminal_line)
        control_box.setLayout(control_layout)
        control_box.setMaximumWidth(200)
        main_layout.addWidget(control_box)

        self.setLayout(main_layout)

    def switch_video(self):
        if self.status is self.STATUS_INIT:
            self.timer.start()
        elif self.status is self.STATUS_PLAYING:
            self.timer.stop()
        elif self.status is self.STATUS_PAUSE:
            self.timer.start()

        self.status = (self.STATUS_PLAYING,
                       self.STATUS_PAUSE,
                       self.STATUS_PLAYING)[self.status]

    def reset(self):
        self.timer.stop()
        self.status = self.STATUS_INIT
        for i in range(4):
            self.image_player[i].frame_index = 0

    def play(self):
        self.timer.start()
        self.status = self.STATUS_PLAYING

    def stop(self):
        self.timer.stop()
        self.status = self.STATUS_PAUSE

