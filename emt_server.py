import socket
import struct

from pynput import mouse, keyboard

from mouse_keyboard_map import MouseButton, Key, Event, ModifierKey


class EMTServer:
    def __init__(self):
        self.sock = None  # 服务端套接字
        self.clients = []  # 保存已连接的客户端

    @staticmethod
    def socket_type():
        """
        判断主机将要创建的socket的类型
        :return: (是否使用IPv6协议族, 是否支持双栈协议)
        """
        from IPTools import IPTools
        if IPTools.get_host_ip(socket.AF_INET6, is_global=True):
            if socket.has_dualstack_ipv6():
                return True, True
            else:
                return True, False
        return False, False

    def create_socket(self, port, use_ipv6=False, has_dualstack=False):
        """
        创建套接字
        说明：https://docs.microsoft.com/en-us/windows/win32/winsock/ipproto-ipv6-socket-options#options
        :param use_ipv6: 套接字协议族 默认使用IPv4协议族
        :param has_dualstack: 是否支持双栈协议
        :param port: 套接字要绑定的端口
        :return: 双栈协议套接字 or IPv6套接字 or IPv4套接字 or None
        """
        sock = None
        try:
            if use_ipv6:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                if has_dualstack:
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                sock.bind(('::', port))
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('0.0.0.0', port))
            sock.listen()
            # sock.setblocking(False)
        except Exception as e:
            if sock is not None:
                sock.close()
            print(e)
            return
        self.sock = sock

    def mouse_keyboard_op(self):
        conn = self.clients[0]
        with conn:
            mouse_controller = mouse.Controller()
            keyboard_controller = keyboard.Controller()

            while True:
                data_type = struct.unpack('>b', conn.recv(1))[0]
                if data_type == 1:  # 鼠标事件数据
                    btn, e, x, y = struct.unpack('>bbhh', conn.recv(6))
                    x = int(x * 1.25)
                    y = int(y * 1.25)
                    if x < 0 or y < 0:
                        continue
                    if btn == MouseButton.LeftButton.value:
                        btn = mouse.Button.left
                    elif btn == MouseButton.RightButton.value:
                        btn = mouse.Button.right
                    elif btn == MouseButton.MiddleButton.value:
                        btn = mouse.Button.middle
                    else:
                        continue
                    mouse_controller.position = (x, y)
                    if e == Event.MouseButtonPress.value:
                        mouse_controller.press(btn)
                    elif e == Event.MouseButtonRelease.value:
                        mouse_controller.release(btn)
                    elif e == Event.MouseMove.value:
                        pass
                    elif e == Event.MouseButtonDblClick.value:
                        mouse_controller.click(btn, 2)
                else:  # 键盘事件数据
                    btn, e, _ = struct.unpack('>ibb', conn.recv(6))
                    if ModifierKey.get(btn, None) is not None:
                        btn = ModifierKey.get(btn)
                    else:
                        btn = Key(btn).name.split('_')[1]
                        if len(btn) == 1:
                            btn = btn.lower()
                        else:
                            continue
                    if e == Event.KeyPress.value:
                        keyboard_controller.press(btn)
                    elif e == Event.KeyRelease.value:
                        keyboard_controller.release(btn)


if __name__ == '__main__':
    print(Key(0x4e))
