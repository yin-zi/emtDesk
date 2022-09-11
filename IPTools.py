import socket


class IPTools:
    """IP地址处理工具类"""
    @staticmethod
    def get_host_info():
        """返回主机相关的网络信息"""
        host_info = {}
        host_info.setdefault('主机名', socket.gethostname())
        host_info.setdefault('IPv6支持', '是' if socket.has_ipv6 else '否')
        host_info.setdefault('IPv4和IPv6双层堆栈支持', '是' if socket.has_dualstack_ipv6() else '否')

        host_info.setdefault('公网IPv6地址', IPTools.get_host_ip(socket.AF_INET6, is_global=True))
        host_info.setdefault('公网IPv4地址', IPTools.get_host_ip(socket.AF_INET, is_global=True))
        host_info.setdefault('私网IPv6地址', IPTools.get_host_ip(socket.AF_INET6, is_global=False))
        host_info.setdefault('私网IPv4地址', IPTools.get_host_ip(socket.AF_INET, is_global=False))

        return host_info

    @staticmethod
    def get_host_ip(family=0, is_global=None):
        """返回主机所有网卡的ip地址（包括虚拟机）
        :family: 地址族 默认0 返回所有ip地址
                       socket.AF_INET6 返回所有ipv6地址
                       socket.AF_INET 返回所有ipv4地址
        :is_global: IP是否是公网 默认None 返回公网和私网地址
                               True 返回公网地址

                               False 返回私网地址
        """
        import ipaddress
        # 每个IP信息是元组类型 (地址族, 套接字类型, 协议, canonname, 套接字地址)
        ip_list = []
        if is_global is None:
            for addr_info in socket.getaddrinfo('', None, family):
                ip_list.append(addr_info[-1][0])
        elif is_global:
            for addr_info in socket.getaddrinfo('', None, family):
                if ipaddress.ip_address(addr_info[-1][0]).is_global:
                    ip_list.append(addr_info[-1][0])
        else:
            for addr_info in socket.getaddrinfo('', None, family):
                if ipaddress.ip_address(addr_info[-1][0]).is_private:
                    ip_list.append(addr_info[-1][0])
        return ip_list

    @staticmethod
    def get_ip_info(ip):
        """检查ip是否合法 返回值为元组 (是否合法, 是否ipv6, 是否公网)"""
        import ipaddress
        try:
            ip_addr = ipaddress.ip_address(ip)
        except ValueError:
            return False, None, None
        return True, isinstance(ip_addr, ipaddress.IPv6Address), ip_addr.is_global


if __name__ == '__main__':
    print(IPTools.get_host_info())
    print(IPTools.get_host_ip())
    print(IPTools.get_ip_info('127.0.0.1'))
    print(IPTools.get_ip_info('124.222.44.157'))
    print(IPTools.get_ip_info('xxx.abc.xyz.yyy'))
    print(IPTools.get_ip_info('fe80::e80b:eab9:70bd:3335'))
    print(IPTools.get_ip_info('2409:8a44:6e1a:8850::261'))
    print(IPTools.get_ip_info('xxx::abc:yyy'))
