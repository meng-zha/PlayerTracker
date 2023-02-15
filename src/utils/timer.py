import time

from PyQt5.QtCore import QThread, QObject, pyqtSignal, QMutex, QMutexLocker

class Communicate(QObject):

    signal = pyqtSignal()


class VideoTimer(QThread):

    def __init__(self, frequent=10, section_length = 10):
        QThread.__init__(self)
        self.stopped = True
        self.frequent = frequent
        self.section_length = section_length
        self.timeSignal = Communicate()
        self.mutex = QMutex()

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
        clock = time.time()
        counter = 0
        while counter<self.section_length:
            import threading
            t = threading.current_thread()
            print("VideoPlayerThread", time.time() - clock, t.ident)
            clock = time.time()
            if self.stopped:
                return
            self.timeSignal.signal.emit()
            counter += 1
            time.sleep(1 / self.frequent)
        with QMutexLocker(self.mutex):
            self.stopped = True

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, fps):
        self.frequent = fps
