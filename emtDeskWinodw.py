import struct

import cv2
import numpy as np

from PySide6.QtCore import Qt, QSize, QEvent, QTime, QTimer
from PySide6.QtGui import QImage, QPixmap, QIcon
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSizePolicy, QVBoxLayout

from emt_client import EMTClient


class EMTDeskWindow(QWidget, EMTClient):

    def __init__(self, parent=None, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)
        EMTClient.__init__(self)
        self.setWindowTitle('EMTDesk')
        self.resize(QSize(1280, 720))
        self.setup_ui()

        self.original_pixmap = None
        self.screen_share = False

    def setup_ui(self):
        self.screenshot_label = QLabel('请稍后...', self)
        # self.screenshot_label.resize(QSize(1280, 720))
        self.screenshot_label.setStyleSheet('background-color: white;')
        self.screenshot_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 设置控件在布局里的大小变化
        self.screenshot_label.setAlignment(Qt.AlignCenter)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.screenshot_label)

    def recv_im(self):
        c = self.client
        with c:
            im_np_old = np.zeros((1080, 1920, 3), dtype=np.uint8)  # 初始化0帧
            # st = QTime.currentTime()
            cnt = 0
            while True:
                im_type, im_len = struct.unpack('>BI', c.recv(5))  # 接收数据长度
                img_bytes = b""
                while im_len > 0:
                    img_byte = c.recv(min(im_len, 4096))
                    im_len -= len(img_byte)
                    img_bytes += img_byte
                im_en_new = np.frombuffer(img_bytes, dtype=np.uint8)
                im_np_new = cv2.imdecode(im_en_new, cv2.IMREAD_COLOR)
                if im_type == 1:  # 原始图像数据
                    im_np_old = im_np_new
                else:  # 差分图像数据
                    im_np_old = im_np_new ^ im_np_old

                height, width, channels = im_np_old.shape
                qim = QImage(im_np_old.data, width, height, QImage.Format_RGB888)
                # qim = QImage(im_np_old.data, width, height, width * channels, QImage.Format_RGB888)
                self.original_pixmap = QPixmap(qim)
                self.update_screenshot_label()
                cnt += 1
                # print(cnt // (st.msecsTo(QTime.currentTime()) / 1000))
                # self.setWindowTitle('emtDesk ' + str(cnt // (st.msecsTo(QTime.currentTime()) / 1000)) + '帧')

    def update_screenshot_label(self):
        # 设置设备像素比DPR 否则图片显示不清晰
        self.original_pixmap.setDevicePixelRatio(self.devicePixelRatio())
        # self.screenshot_label.setPixmap(
        #     self.original_pixmap.scaled(
        #         self.screenshot_label.size(),
        #         Qt.KeepAspectRatio,
        #         Qt.SmoothTransformation,
        #     )
        # )
        self.screenshot_label.setPixmap(self.original_pixmap)

    # def resizeEvent(self, event):
    #     scaled_size = self.original_pixmap.size()
    #     scaled_size.scale(self.screenshot_label.size(), Qt.KeepAspectRatio)
    #     if scaled_size != self.screenshot_label.pixmap().size():
    #         self.update_screenshot_label()

    def mouseMoveEvent(self, event) -> None:
        """没有设置鼠标追踪 只会在鼠标按下时进入事件"""
        pass
        # if not self.screen_share:
        #     btn = int(event.button())
        #     e = int(QEvent.MouseMove)
        #     x = int(event.position().x())
        #     y = int(event.position().y())
        #     # 鼠标数据 鼠标按钮 鼠标事件 x坐标 y坐标 7字节
        #     self.client.send(struct.pack('>bbbhh', 1, btn, e, x, y))

    def mousePressEvent(self, event) -> None:
        if not self.screen_share:
            btn = int(event.button())
            e = int(QEvent.MouseButtonPress)
            x = int(event.position().x())
            y = int(event.position().y())
            # 鼠标数据 鼠标按钮 鼠标事件 x坐标 y坐标 7字节
            self.client.send(struct.pack('>bbbhh', 1, btn, e, x, y))

    def mouseReleaseEvent(self, event) -> None:
        if not self.screen_share:
            btn = int(event.button())
            e = int(QEvent.MouseButtonRelease)
            x = int(event.position().x())
            y = int(event.position().y())
            # 鼠标数据 鼠标按钮 鼠标事件 x坐标 y坐标 7字节
            self.client.send(struct.pack('>bbbhh', 1, btn, e, x, y))

    def mouseDoubleClickEvent(self, event) -> None:
        pass
        # if not self.screen_share:
        #     btn = int(event.button())
        #     e = int(QEvent.MouseButtonDblClick)
        #     x = int(event.position().x())
        #     y = int(event.position().y())
        #     # 鼠标数据1 鼠标按钮1 鼠标事件1 x坐标2 y坐标2 7字节
        #     self.client.send(struct.pack('>bbbhh', 1, btn, e, x, y))

    def send_mouse_event(self, event):
        if not self.screen_share:
            pass

    def keyPressEvent(self, event) -> None:
        if not self.screen_share:
            # 键盘数据1 键盘按钮4 键盘事件1 补齐1字节 7字节
            # btn = event.nativeScanCode()  # 最大值349
            btn = event.key()
            e = int(QEvent.KeyPress)
            self.client.send(struct.pack('>bibb', 2, btn, e, -1))
            # print(event.key(), event.isAutoRepeat(), event.nativeVirtualKey(), event.nativeModifiers(),
            #       event.nativeScanCode(), event.keyCombination())

    def keyReleaseEvent(self, event) -> None:
        if not self.screen_share:
            # 键盘数据1 键盘按钮4 键盘事件1 补齐1字节 7字节
            # btn = event.nativeScanCode()  # 最大值349
            btn = event.key()
            e = int(QEvent.KeyRelease)
            self.client.send(struct.pack('>bibb', 2, btn, e, -1))

    def wheelEvent(self, event) -> None:
        pass

    def closeEvent(self, event) -> None:
        if self.client is not None:
            self.client.close()
        self.client = None


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('resources/logo.ico'))
    window = EMTDeskWindow()
    window.show()
    sys.exit(app.exec())
