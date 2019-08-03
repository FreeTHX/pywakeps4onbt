# PyWakePs4 On BlueTooth
This is a simple Python library to switch on a ps4 using Bluetooth
Based on :
- [PS4 Dev Wiki](https://www.psdevwiki.com/ps4/DS4-BT#Bluetooth_Addressing) Spoofing and HCI CC
- [bdaddr](http://blog.petrilopia.net/linux/change-your-bluetooth-device-mac-address/) BT spoofing first imp
- [bdaddr github](https://github.com/pauloborges/bluez/blob/master/tools/bdaddr.c) ... and another one available on github
- [Frank Zhao](https://eleccelerator.com/unpairing-a-dualshock-4-and-setting-a-new-bdaddr/) Article to get DS4 and PS4 BT Addr 

The main objective is to include it into [Home Assistant](https://www.home-assistant.io/ "Home Assistant") components to provide a "Wake Ps4 On Bt" service.
