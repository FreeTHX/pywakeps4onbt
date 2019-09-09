ADAPTER_SUFFIX = 'hci'
ADAPTER_DEFAULT = 0
IDVENDOR_SONY = [ 0x54c ]
IDPRODUCT_DS4 = [ 0x05c4, 0x09cc]

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

def hci_read_local_version_compid(adapter: int) -> int: 
    import bluetooth._bluetooth as _bt

    try:
        hci_sock = _bt.hci_open_dev(adapter)
        res = _bt.hci_send_req(hci_sock,
                               _bt.OGF_INFO_PARAM,
                               _bt.OCF_READ_LOCAL_VERSION,
                               _bt.EVT_CONN_COMPLETE,
                               9)
        hci_sock.close()
        # Check first byte.
        # See read_local_version_rp.status
        # 0 if OK or ERRNO if an error has been raised 
        if res[0]:
            # Invalid response
            return -1
            
        return int.from_bytes(res[5:7],byteorder='little', signed=False)

    except _bt.error as e:
        raise BluetoothError(*e.args)

def read_local_bdaddr(adapter: int) -> str: 
    import struct
    import bluetooth._bluetooth as _bt

    try:
        hci_sock = _bt.hci_open_dev(adapter)

        old_filter = hci_sock.getsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, 14)
        flt = _bt.hci_filter_new()
        opcode = _bt.cmd_opcode_pack(_bt.OGF_INFO_PARAM, _bt.OCF_READ_BD_ADDR)
        _bt.hci_filter_set_ptype(flt, _bt.HCI_EVENT_PKT)
        _bt.hci_filter_set_event(flt, _bt.EVT_CMD_COMPLETE)
        _bt.hci_filter_set_opcode(flt, opcode)
        hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, flt )

        _bt.hci_send_cmd(hci_sock, _bt.OGF_INFO_PARAM, _bt.OCF_READ_BD_ADDR )
        pkt = hci_sock.recv(255)
        status,raw_bdaddr = struct.unpack("xxxxxxB6s", pkt)
        assert status == 0

        t = [ "%02X" % int(b) for b in raw_bdaddr ]
        t.reverse()
        bdaddr = ":".join(t)

        # restore old filter
        hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, old_filter )
        hci_sock.close()
        return bdaddr
    except _bt.error as e:
        raise BluetoothError(*e.args)

# Only BCM ( raspberry and others) supported yet)
def bcm_write_local_bdaddr(adapter: int, dsbtaddr: str) -> None:
    import bluetooth._bluetooth as _bt

    try:
        # Open hci socket
        hci_sock = _bt.hci_open_dev(adapter)

        # Get bytes from bluetooth address
        baddrtospoof = bytearray.fromhex(dsbtaddr.replace(":",""))
        baddrtospoof.reverse()

        # Send HCI request
        cmd_pkt = bytes( baddrtospoof)

        # BCM WRITE ADDR command
        # https://github.com/pauloborges/bluez/blob/master/tools/bdaddr.c
        _bt.hci_send_req(hci_sock,
                         _bt.OGF_VENDOR_CMD,
                         0x0001, #OCF_BCM_WRITE_BD_ADDR
                         0x00000000,
                         1000,
                         cmd_pkt)

        hci_sock.close()

    except _bt.error as e:
        raise BluetoothError(*e.args)


def hci_cc(adapter: int, ps4btaddr: str) -> None:
    import bluetooth._bluetooth as _bt

    try:
        hci_sock = _bt.hci_open_dev(adapter)

        # Get bytes from bluetooth address
        baps4addr = bytearray.fromhex(ps4btaddr.replace(":",""))
        baps4addr.reverse()
        # HCI CONNECT
        # BLUETOOTH SPECIFICATION Version 5.0 | Vol 2, Part E page 774
        # https://github.com/pauloborges/bluez/blob/master/tools/hcitool.c => cmd_cc
        # https://github.com/pauloborges/bluez/blob/master/lib/hci.c => hci_create_connection
        cmd_pkt = bytes(baps4addr) + bytes([ # Target BTADDR on 6 bytes reverse order,
                        0x18, 0xCC, # pkt_type HCI_DM1 | HCI_DM3 | HCI_DM5 | HCI_DH1 | HCI_DH3 | HCI_DH5
                        0x02, # pscan_rep_mode
                        0x00, # pscan_mode (reserved)
                        0x00, 0x00, # clock_offset
                        0x01]) # role_switch

        # Send HCI request
        _bt.hci_send_req(hci_sock,
                        _bt.OGF_LINK_CTL,
                        _bt.OCF_CREATE_CONN,
                        _bt.EVT_CONN_COMPLETE,
                        1000,
                        cmd_pkt)
        hci_sock.close()

    except _bt.error as e:
        raise BluetoothError(*e.args)


write_local_bdaddr = { 15 : bcm_write_local_bdaddr}

def send_magic_packet(adapter,
                      ps4_addr: str,
                      ds4_addr: str) -> None:

    adapterdevid = get_devid_from_devname(adapter)
    compid = hci_read_local_version_compid(adapterdevid)
    if compid not in write_local_bdaddr:
        return False

    """Send magic packet to wake up a device."""
    # Get the original addr
    original_bdaddr = read_local_bdaddr(adapterdevid)
    # Spoof the addr
    write_local_bdaddr[compid](adapterdevid, ds4_addr)
    # connect to the Ps4 HCI CC
    hci_cc(adapterdevid, ps4_addr)
    # Write back the original addr
    write_local_bdaddr[compid](adapterdevid,original_bdaddr)

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
