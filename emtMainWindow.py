import struct
import threading

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, \
    QCheckBox, QGridLayout, QMessageBox

from emt_server import EMTServer
from emtDeskWinodw import EMTDeskWindow


class EMTMainWindow(QWidget, EMTServer):
    def __init__(self, parent=None, *args, **kwargs):
        # print(EMTMainWindow.mro())
        QWidget.__init__(self, parent, *args, **kwargs)
        EMTServer.__init__(self)
        self.setWindowTitle('emtDesk')
        self.setFixedSize(633, 399)
        self.setup_ui()
        self.emtDesk = None  # 远程桌面窗口
        self.ims_old = None  # 记录旧一帧截屏的numpy数组 同时记录是否有服务线程

    def setup_ui(self):
        # 总体布局 左3右7(上5下5)
        self.main_h_layout = QHBoxLayout(self)
        self.left_widget = QWidget(self)
        self.right_widget = QWidget(self)
        self.main_h_layout.addWidget(self.left_widget, 3)
        self.main_h_layout.addWidget(self.right_widget, 7)
        self.left_v_layout = QVBoxLayout(self.left_widget)
        self.right_top_widget = QWidget(self.right_widget)
        self.right_bottom_widget = QWidget(self.right_widget)
        self.right_v_layout = QVBoxLayout(self.right_widget)
        self.right_v_layout.addWidget(self.right_top_widget, 5)
        self.right_v_layout.addWidget(self.right_bottom_widget, 5)
        self.right_top_grid_layout = QGridLayout(self.right_top_widget)
        self.right_bottom_grid_layout = QGridLayout(self.right_bottom_widget)
        # 窗口左侧控件
        self.remote_desk_btn = QPushButton(QIcon('resources/logo.ico'), '远程桌面', self.left_widget)
        self.net_info_btn = QPushButton('网络信息', self.left_widget)
        self.wait_connect_btn = QPushButton('邀请远程协助', self.left_widget)
        self.wait_connect_btn.setToolTip('邀请远程协助端口为右侧输入文本框端口')
        self.wait_connect_btn.setMinimumHeight(66)
        self.check_update_btn = QPushButton('检查更新', self.left_widget)
        self.left_v_layout.addWidget(self.remote_desk_btn)
        self.left_v_layout.addWidget(self.net_info_btn)
        self.left_v_layout.addWidget(self.wait_connect_btn)
        self.left_v_layout.addWidget(self.check_update_btn)
        # 窗口右侧上部控件
        self.host_label = QLabel('IP地址', self.right_top_widget)
        self.host_le = QLineEdit(self.right_top_widget)
        self.host_le.setPlaceholderText('请输入要远程的IP地址')
        self.port_label = QLabel('端口', self.right_top_widget)
        self.port_label.setToolTip('邀请远程协助和连接远程桌面均使用此端口')
        self.port_le = QLineEdit('3389', self.right_top_widget)
        self.port_le.setPlaceholderText('请输入端口号')
        self.port_le.setToolTip('有效端口范围：1024-65535')
        self.screen_share_cb = QCheckBox('屏幕分享', self.right_top_widget)
        self.screen_share_cb.setChecked(True)
        self.system_audio_cb = QCheckBox('系统声音', self.right_top_widget)
        self.clipboard_cb = QCheckBox('剪贴板', self.right_top_widget)
        self.microphone_cb = QCheckBox('麦克风', self.right_top_widget)
        self.connect_btn = QPushButton('连接', self.right_top_widget)
        self.right_top_grid_layout.addWidget(self.host_label, 0, 0, 1, 3)
        self.right_top_grid_layout.addWidget(self.port_label, 0, 3)
        self.right_top_grid_layout.addWidget(self.host_le, 1, 0, 1, 3)
        self.right_top_grid_layout.addWidget(self.port_le, 1, 3)
        self.right_top_grid_layout.addWidget(self.screen_share_cb, 2, 0)
        self.right_top_grid_layout.addWidget(self.clipboard_cb, 2, 1)
        self.right_top_grid_layout.addWidget(self.system_audio_cb, 2, 2)
        self.right_top_grid_layout.addWidget(self.microphone_cb, 2, 3)
        self.right_top_grid_layout.addWidget(self.connect_btn, 3, 1, 1, 2)
        self.right_top_grid_layout.setColumnStretch(0, 1)
        self.right_top_grid_layout.setColumnStretch(1, 1)
        self.right_top_grid_layout.setColumnStretch(2, 1)
        self.right_top_grid_layout.setColumnStretch(3, 1)
        # 窗口右侧下部控件
        self.ip_list_label = QLabel('可用公网IP地址', self.right_bottom_widget)
        self.ip_list_label.setToolTip('下方列出的IP地址选中按下Ctrl+C即可复制')
        self.right_bottom_grid_layout.addWidget(self.ip_list_label, 0, 0)
        from IPTools import IPTools
        ip_list = IPTools.get_host_ip(is_global=True)
        for row_num, ip in enumerate(ip_list):
            ip_label = QLabel(ip, self.right_bottom_widget)
            ip_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.right_bottom_grid_layout.addWidget(ip_label, row_num + 1, 0)
        if len(ip_list) == 0:
            no_ip_label = QLabel('没有公网IP可用！', self.right_bottom_widget)
            self.right_bottom_grid_layout.addWidget(no_ip_label, 1, 0)
        # 设置控件信号与槽的连接
        # self.remote_desk_btn.clicked.connect(lambda: print('远程桌面'))
        self.net_info_btn.clicked.connect(self.on_net_info_btn_clicked)
        self.check_update_btn.clicked.connect(self.on_check_update_btn_clicked)

        self.wait_connect_btn.clicked.connect(self.on_wait_connect_btn_clicked)
        self.connect_btn.clicked.connect(self.on_connect_btn_clicked)

        self.setup_style()

    def setup_style(self):
        """todo:考虑样式写到qss文件中"""
        # self.setWindowOpacity(0.9)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)
        self.left_v_layout.setContentsMargins(0, 0, 0, 0)
        self.right_v_layout.setContentsMargins(0, 0, 0, 0)
        self.right_v_layout.setSpacing(0)
        self.left_widget.setStyleSheet("""
        QWidget {
            font-size: 15px;
            font-family: 宋体;
            background-color: rgb(232,232,232);
        }
        QPushButton {
            border-radius: 9px;
            border: none;
            margin-left: 15px;
            margin-right: 15px;
            min-height: 35px;
        }
        QPushButton:hover {
            background-color: rgb(219, 219, 219);
        }
        """)
        self.right_widget.setStyleSheet("""
        QWidget {
            font-size: 15px;
            font-family: 宋体;
            background-color: rgb(243, 243, 243);
        }
        QLabel {
            padding-left: 5px;
        }
        QLineEdit {
            min-height: 33px;
            margin-bottom: 13px;
            border: 1px solid black;
            border-radius: 9px;
            padding-left: 5px;
        }
        """)
        self.right_top_widget.setStyleSheet("""
        QWidget {
            margin-left: 6px;
        }
        """)
        self.right_bottom_widget.setStyleSheet("""
        QWidget {
            margin-left: 6px;
        }
        """)
        self.wait_connect_btn.setStyleSheet("""
        QPushButton {
            background-color: rgb(209, 209, 209);
            border-radius: 29px;
            font-size: 19px;
            min-height: 66px;
        }
        """)
        self.connect_btn.setStyleSheet("""
        QPushButton {
            background-color: rgb(209, 209, 209);
            border-radius: 16px;
            font-size: 19px;
            min-height: 39px;
            margin-top: 13px;
        }
        """)

    def on_device_list_btn_clicked(self):
        QMessageBox.information(self, '设备信息', '暂无设备保存记录')

    def on_net_info_btn_clicked(self):
        from IPTools import IPTools
        QMessageBox.information(self, '网络信息', str(IPTools.get_host_info()))

    def on_check_update_btn_clicked(self):
        QMessageBox.information(self, '检查更新', '已是最新版本')

    def on_connect_btn_clicked(self):
        if self.emtDesk is not None:
            self.emtDesk.close()
            self.emtDesk = None
            self.connect_btn.setText('连接')
            return

        # IP和PORT的合法性校验
        from IPTools import IPTools
        ip = self.host_le.text().strip()
        ip_is_valid, ip_is_v5, ip_is_global = IPTools.get_ip_info(ip)
        if not ip_is_valid:
            QMessageBox.critical(self, '错误', '请输入正确的IP地址')
            return
        try:
            port = int(self.port_le.text())
            if port < 1024 or port > 65535:
                raise ValueError('可用端口号范围应为1024-65535')
        except ValueError:
            QMessageBox.critical(self, '错误', '请输入正确的端口号（1024-65535）！')
            return
        # IP和PORT校验通过 连接远程桌面
        self.connect_btn.setDisabled(True)
        self.connect_btn.setText('正在连接{ip}:{port}...')
        self.emtDesk = EMTDeskWindow()
        self.emtDesk.connect_socket(ip, port)
        if self.emtDesk.client is not None:
            self.emtDesk.show()
            self.connect_btn.setText('正在远程 单击断开')
            self.connect_btn.setDisabled(False)
            self.emtDesk.screen_share = self.screen_share_cb.isChecked()
            try:
                t = threading.Thread(target=self.emtDesk.recv_im, daemon=True)
                t.start()
                # print('子窗口接收数据线程是否存活', t.is_alive())
            except Exception as e:
                print(e)
        else:
            QMessageBox.critical(self, '错误', '连接远程桌面失败！')
            self.connect_btn.setText('连接')
            return

    def on_wait_connect_btn_clicked(self):
        """
        邀请远程协助 等待连接 正在远程
        :return:
        """
        if self.sock is not None:
            for client in self.clients:
                if client is not None:
                    client.close()
            self.clients = []
            self.sock.close()
            self.sock = None
            self.wait_connect_btn.setText('邀请远程协助')
            return
        try:
            port = int(self.port_le.text())
            if port < 1024 or port > 65535:
                raise ValueError('可用端口号范围应为1024-65535')
        except ValueError:
            QMessageBox.critical(self, '错误', '请输入正确的端口号 1024-65535 ！\n连接按钮上方的端口同时也是远程协助端口！')
            return
        # 创建套接字
        use_ipv6, has_dualstack = self.socket_type()
        self.create_socket(port, use_ipv6, has_dualstack)
        if self.sock is None:
            QMessageBox.critical(self, '错误', '创建套接字出错！\n请稍后再试！')
            return
        # 修改按钮状态
        self.wait_connect_btn.setDisabled(True)
        self.wait_connect_btn.setText(f'{"[::]" if use_ipv6 else "0.0.0.0"}:{port}\n等待远程协助...')
        threading.Thread(target=self.accept, daemon=True).start()

    def accept(self):
        while True:
            conn, addr = self.sock.accept()
            self.clients.append(conn)
            self.wait_connect_btn.setText(f'已连接{len(self.clients)}台设备\n远程中 单击断开')
            self.wait_connect_btn.setDisabled(False)
            if self.ims_old is None:  # 说明当前不存在服务线程 使用图片变量标记
                self.ims_old = np.zeros((1080, 1920, 3), dtype=np.uint8)  # 开启服务前初始化0帧
                threading.Thread(target=self.server, daemon=True).start()
                threading.Thread(target=self.mouse_keyboard_op, daemon=True).start()

    def server(self):
        while True:
            if len(self.clients) == 0:
                continue
            is_diff_im, im_len, im_data = self.im_diff()
            if im_data is None:
                continue
            for conn in self.clients:
                try:
                    conn.send(struct.pack('>BI', is_diff_im, im_len))
                    conn.send(im_data)
                except Exception:
                    conn.close()
                    self.clients.remove(conn)
                    self.wait_connect_btn.setText(f'已连接{len(self.clients)}台设备\n远程中 单击断开')

    def im_diff(self):
        im_np_new = self.screenshot()
        _, im_en_new = cv2.imencode('.png', im_np_new)
        ims_new = cv2.imdecode(np.asarray(im_en_new, dtype=np.uint8), cv2.IMREAD_COLOR)
        ims_diff = ims_new ^ self.ims_old
        if (ims_diff != 0).any():  # 新旧两帧不同
            self.ims_old = ims_new
        else:  # 新旧两帧相同 跳过此帧传输
            return None, None, None
        _, im_en_diff = cv2.imencode('.png', ims_diff)
        im_en_new_len = len(im_en_new)
        im_en_diff_len = len(im_en_diff)
        if im_en_new_len <= im_en_diff_len:
            return 1, im_en_new_len, im_en_new
        else:
            return 0, im_en_diff_len, im_en_diff

    def screenshot(self):
        screen = QGuiApplication.primaryScreen()
        if window := self.windowHandle():
            screen = window.screen()
        if not screen:
            return
        qpix = screen.grabWindow(0)
        qim = qpix.toImage()  # 将QPixmap转换为QImage
        im_bytes = bytes(qim.bits())
        # 将截图得到的二进制数据转换为numpy数组
        im_np = np.frombuffer(im_bytes, dtype=np.uint8)
        im_np = im_np.reshape((qim.height(), qim.width(), qim.depth() // 8))  # 注意h和w的顺序
        im_np = im_np[:, :, :3].copy()  # BGRA->BGR 不调用copy返回的是视图且只读
        im_np[:, :, [0, 2]] = im_np[:, :, [2, 0]]  # BGR->RGB
        return im_np

    def closeEvent(self, event) -> None:
        if self.emtDesk is not None:
            self.emtDesk.close()
        sys.exit(0)


if __name__ == '__main__':
    import sys
    import resources

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/icons/logo.ico'))
    window = EMTMainWindow()
    window.show()
    sys.exit(app.exec())
