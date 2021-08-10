

class DeviceInfo:
    def __init__(self, host_name, addr_ip, device_name, device_id, software_version, os_version) -> None:
        self.host_name = host_name
        self.addr_ip = addr_ip
        self.device_name = device_name
        self.device_id = device_id
        self.software_version = software_version
        self.os_version = os_version

    def get_host_name(self):
        return self.host_name

    def get_addr_ip(self):
        return self.addr_ip
    
    def get_device_name(self):
        return self.device_name

    def get_device_id(self):
        return self.device_id

    def get_software_version(self):
        return self.software_version

    def get_os_version(self):
        return self.os_version
