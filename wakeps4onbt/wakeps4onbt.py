import struct
import socket
import time

ADAPTER_SUFFIX = 'hci'
ADAPTER_DEFAULT = 0
DEFAULT_SLEEP_AFTER_CC = 2
# SONY IDVENDOR / IDPRODUCT
IDVENDOR_SONY = [ 0x54c ]
IDPRODUCT_DS4 = [ 0x05c4, 0x09cc]
# HCI
HCI_FILTER_SIZE = 14
HCI_COMMAND_PKT = 0x01
HCI_EVENT_PKT = 0x04
EVT_CMD_COMPLETE = 0x0e
EVT_CMD_STATUS = 0x0f
# OCF and OGF opcode
OGF_LINK_CTL = 0x01
OGF_INFO_PARAM = 0x04
OGF_VENDOR_CMD = 0x3f
OCF_READ_LOCAL_VERSION = 0x0001
OCF_CREATE_CONN = 0x0005
OCF_READ_BD_ADDR = 0x0009
OCF_BCM_CYS_WRITE_BD_ADDR = 0x0001

#####################################
## HCI functions
#####################################
def get_devid_from_devname(adaptername) -> int:
    if isinstance(adaptername, int):
        return adaptername
    if isinstance(adaptername, str):
        try:
            adapter = int(adaptername.replace(ADAPTER_SUFFIX, ''))
        except:
            adapter = ADAPTER_DEFAULT
    else:
        adapter = ADAPTER_DEFAULT    
    return adapter

def hci_open_dev(dev_id: int) -> socket.socket:
    if dev_id < 0:
        # ENODEV
        return -1
    # Create HCI socket
    dd = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI)
    # Manager Error ?
    # if dd < 0:
    #    return dd
    # TODO ErrorMngment
    dd.bind((dev_id,))
    return dd

def hci_close_dev(bt_socket: socket.socket) -> None:
    bt_socket.close()

# Return an uint16 opcode
def cmd_opcode_pack(ogf: int, ocf: int) -> int:
    return	((ocf & 0x03ff)|(ogf << 10))

# Feature Filter
def get_features_filter(bt_socket: socket.socket) -> bytes:
    return bt_socket.getsockopt( socket.SOL_HCI, socket.HCI_FILTER, HCI_FILTER_SIZE)

def set_features_filter(bt_socket: socket.socket, opcode: int = 0) -> None:
    typeMask   = 1 << HCI_EVENT_PKT
    eventMask1 = (1 << EVT_CMD_COMPLETE) | (1 << EVT_CMD_STATUS)
    eventMask2 = 0
    filter = struct.pack("<LLLHH", typeMask, eventMask1, eventMask2, opcode, 0)
    bt_socket.setsockopt( socket.SOL_HCI, socket.HCI_FILTER, filter)

def reset_features_filter(bt_socket: socket.socket, filter: bytes) -> None:
    bt_socket.setsockopt( socket.SOL_HCI, socket.HCI_FILTER, filter)


def hci_read_local_bdaddr(bt_socket: socket.socket) -> str: 
    old_filter = get_features_filter(bt_socket)
    opcode = cmd_opcode_pack(OGF_INFO_PARAM, OCF_READ_BD_ADDR)
    set_features_filter(bt_socket, opcode)    
    cmd = struct.pack("<BHB", HCI_COMMAND_PKT, opcode, 0)
    bt_socket.send(cmd)
    pkt = bt_socket.recv(255)
    reset_features_filter( bt_socket, old_filter)
    if len(pkt) != 13:
        return None
    status,raw_bdaddr = struct.unpack("<xxxxxxB6s", pkt)
    if status != 0:
        return None
    t = [ "%02X" % int(b) for b in raw_bdaddr ]
    t.reverse()
    bdaddr = ":".join(t)
    return bdaddr

def hci_read_local_manufacturer(bt_socket: socket.socket) -> int:
    old_filter = get_features_filter(bt_socket)
    opcode = cmd_opcode_pack(OGF_INFO_PARAM, OCF_READ_LOCAL_VERSION)
    set_features_filter(bt_socket, opcode)
    cmd = struct.pack("<BHB", HCI_COMMAND_PKT, opcode, 0)
    bt_socket.send(cmd)
    pkt = bt_socket.recv(255)
    reset_features_filter( bt_socket, old_filter)
    if len(pkt) != 15:
        return -1
    status,manu = struct.unpack("<xxxxxxBxxxxHxx", pkt)
    if status != 0:
        return -1
    return manu

# Only BCM  and CYS( raspberry and others) supported yet)
def bcm_cys_write_local_bdaddr(bt_socket: socket.socket, dsbtaddr: str) -> bool:
    # prepare bt addr
    baddrtospoof = bytearray.fromhex(dsbtaddr.replace(":",""))
    baddrtospoof.reverse()
    baddr_param = bytes(baddrtospoof)
    bt_socket = hci_open_dev(0)
    # get filter
    old_filter = get_features_filter(bt_socket)
    # set filter
    opcode = cmd_opcode_pack(OGF_VENDOR_CMD, OCF_BCM_CYS_WRITE_BD_ADDR)
    set_features_filter(bt_socket, opcode)
    # send the cmd
    cmd = struct.pack("<BHB6s", HCI_COMMAND_PKT, opcode, 6, baddr_param)
    bt_socket.send(cmd)
    pkt = bt_socket.recv(255)
    # reset old filter
    reset_features_filter( bt_socket, old_filter)
    if len(pkt) != 7:
        return False
    t_status = struct.unpack("<xxxxxxB", pkt) 
    if t_status[0] != 0:
        return False
    return True

def hci_cc(bt_socket: socket.socket, ps4btaddr: str) -> None:
    dstaddr = bytearray.fromhex(ps4btaddr.replace(":",""))
    dstaddr.reverse()
    dstaddr_param = bytes(dstaddr)
    #           dst addr +  
    cmd_param = dstaddr_param + bytes([
        0x00, 0x00, # pkt_type (0x00,0x00 works fine)
        0x02,       # pscan_rep_mode 
        0x00,       # pscan_mode (reserved)
        0x00, 0x00, # clock_offset
        0x01])     # role_switch
    old_filter = get_features_filter(bt_socket)
    opcode = cmd_opcode_pack(OGF_LINK_CTL, OCF_CREATE_CONN)
    set_features_filter(bt_socket, opcode)
    cmd = struct.pack("<BHB13s", HCI_COMMAND_PKT, opcode, 13, cmd_param)
    bt_socket.send(cmd)
    # No need to read the feedback
    reset_features_filter( bt_socket, old_filter)
    return
    
write_local_bdaddr = { 
    15  : bcm_cys_write_local_bdaddr,
    305 : bcm_cys_write_local_bdaddr
    }

def send_magic_packet(adapter,
                      ps4_addr: str,
                      ds4_addr: str,
                      sleep: int = DEFAULT_SLEEP_AFTER_CC) -> bool:

    adapterdevid = get_devid_from_devname(adapter)
    bt_socket = hci_open_dev(adapterdevid)
    manufacturer = hci_read_local_manufacturer(bt_socket)
    if manufacturer not in write_local_bdaddr:
        hci_close_dev(bt_socket)
        return False
    """Send magic packet to wake up a device."""
    # Get the original addr
    original_bdaddr = hci_read_local_bdaddr(bt_socket)
    # Spoof the addr
    write_local_bdaddr[manufacturer](bt_socket, ds4_addr)
    # connect to the Ps4 HCI CC
    hci_cc(bt_socket, ps4_addr)
    # Wait a short delay to let the connection be established before reseting the addr
    time.sleep(sleep)
    # Write back the original addr
    write_local_bdaddr[manufacturer](bt_socket,original_bdaddr)
    hci_close_dev(bt_socket)

    return True

def get_bt_addr():
    import usb.core, usb.util

    dev = None
    for vendor in IDVENDOR_SONY:
        for product in IDPRODUCT_DS4:
            dev = usb.core.find(idVendor=vendor, idProduct=product )
            if dev is not None:
                break
        if dev is not None:
                break

    # Sony DualShock 4 not found !
    if dev is None:
        return None
    
    # Following pyusb recommendation, we detach (if needed) and claim interface
    # https://github.com/pyusb/pyusb/blob/master/docs/tutorial.rst
    reattach = False
    if dev.is_kernel_driver_active(0):
        reattach = True
        dev.detach_kernel_driver(0)
    usb.util.claim_interface(dev, 0)

    # Read PS4 et DS BT addresses with USB control transfer GET REPORT on 0x12'
    msg = dev.ctrl_transfer(0xA1, 0x01, 0x0312, 0x0000, 0x0010)
    # Clean disposal of device
    usb.util.release_interface(dev,0)
    if reattach:
        dev.attach_kernel_driver(0)

    # Get the DualShock BT Address
    dsbt_address = format(msg[6], '02X') + ':' + format(msg[5], '02X') + ':' +                 format(msg[4], '02X') + ':' + format(msg[3], '02X') + ':' +                 format(msg[2], '02X') + ':' + format(msg[1], '02X')
    # Get the Playstation 4 BT Address                  
    ps4bt_address = format(msg[15], '02X') + ':' + format(msg[14], '02X') + ':'               + format(msg[13], '02X') + ':' + format(msg[12], '02X') + ':'               + format(msg[11], '02X') + ':' + format(msg[10], '02X')
 
    return {'dsbt_address':dsbt_address, 'ps4bt_address':ps4bt_address }
