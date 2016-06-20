
def to_vxlan(ip_addr):
    """
    Converts ip_addr to vxlan ip
    """
    return "192.168." + ".".join(ip_addr.split(".")[2:])
