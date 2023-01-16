import time

from PyQt5.QtCore import QThread, QObject, pyqtSignal, QMutex, QMutexLocker

class Communicate(QObject):

    signal = pyqtSignal()


class VideoTimer(QThread):

    def __init__(self, frequent=20):
        QThread.__init__(self)
        self.stopped = False
        self.frequent = frequent
        self.timeSignal = Communicate()
        self.mutex = QMutex()

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
        clock = time.time()
        while True:
            import threading
            t = threading.current_thread()
            print("VideoPlayerThread", time.time() - clock, t.ident)
            clock = time.time()
            if self.stopped:
                return
            self.timeSignal.signal.emit()
            time.sleep(1 / self.frequent)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, fps):
        self.frequent = fps
