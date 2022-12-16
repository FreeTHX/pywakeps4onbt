# PyWakePs4 On BlueTooth
This is a simple Python library to switch on a ps4 using Bluetooth
Based on :
- [PS4 Dev Wiki](https://www.psdevwiki.com/ps4/DS4-BT#Bluetooth_Addressing) Spoofing and HCI CC
- [bdaddr](http://blog.petrilopia.net/linux/change-your-bluetooth-device-mac-address/) BT spoofing first imp
- [bdaddr github](https://github.com/pauloborges/bluez/blob/master/tools/bdaddr.c) ... and another one available on github
- [Frank Zhao](https://eleccelerator.com/unpairing-a-dualshock-4-and-setting-a-new-bdaddr/) Article to get DS4 and PS4 BT Addr 

The main objective is to include it into [Home Assistant](https://www.home-assistant.io/ "Home Assistant") components to provide a "Wake Ps4 On Bt" service.

## Supported Devices
The module tests the adapter support via a ```hci_read_local_manufacturer``` python implementation and read the ```manufacturer``` returned value from ```OCF_READ_LOCAL_VERSION```  
Currently supported adapters :
- Broadcom devices (```manufacturer = 15```)
- Cypress Semiconductor devices (```manufacturer = 305```)

## Get Bluetooth addresses over USB
Plug the DualShock4 controler on your computer using micro USB cable.  
Once ```pywakeps4onbt``` is installed, run the following command from a python shell:
```python
>>> import wakeps4onbt
>>> wakeps4onbt.get_bt_addr()
{'dsbt_address': '00:1F:E2:12:34:56', 'ps4bt_address': '90:CD:B6:12:34:56'}
```

## No external dependency
Recent versions (0.7+) do not use external dependencies for bluetooth and HCI.