---
description: This page describes some non-trivial ways to get sample data from note applications.
---

Documentation how to get sample data from "difficult" apps and OS. Difficult means everything else than Web or Linux.

## Note Apps

### FuseBase/Nimbus Note

From <https://nimbusweb.me/guides/settings/account-management-how-to-backup-and-export-your-data/>:

> Server backups are available only with Plus or Ultimate plans.

Server backups contain the whole workspace. At least single page exports are possible. 

### Samsung Notes

Inside a Windows VM:

1. Install Samsung Notes
2. Launch Samsung Notes by executing [this script](https://github.com/kellwinr/galaxybook_mask/blob/c72333f22dc3be130887b5d0fe9666f3b524902a/samsungnotes-directlaunch.bat). The script does the following steps:
    1. Set `HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\BIOS\SystemProductName` to `NP960XFG-KC4UK`
    2. Set `HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\BIOS\SystemManufacturer` to `Samsung`
    3. Start Samsung Notes
    4. Restore the original registry values

### Synology Note Station

1. Go to the [demo page](https://demo.synology.com/de-de/dsm) and press the "Test" button
2. Open Note Station by Apps → Note Station on the top left
3. Files can be transferred through the file system

### Turtl

- Linux app crashes always
- Android app still works

### Wikimedia

Export at https://de.wikipedia.org/wiki/Spezial:Exportieren.

## Virtual Machines

### macOS

!!! note
    The latest working macOS for VirtualBox is macOS 12 Monterey. See <https://forums.virtualbox.org/viewtopic.php?p=552625#p552625>. Newer versions lead to a boot cycle.

Setup a macOS 12 Monterey VM according to [this guide](https://www.maketecheasier.com/install-macos-virtualbox/).

Troubleshooting:

- Commands after creating, but before starting the VM:

```sh
vboxmanage modifyvm "macos_12_monterey" --cpuid-set 00000001 000106e5 00100800 0098e3fd bfebfbff
vboxmanage setextradata "macos_12_monterey" "VBoxInternal/Devices/efi/0/Config/DmiSystemProduct" "MacBookPro15,1"
vboxmanage setextradata "macos_12_monterey" "VBoxInternal/Devices/efi/0/Config/DmiSystemVersion" "1.0"
vboxmanage setextradata "macos_12_monterey" "VBoxInternal/Devices/efi/0/Config/DmiBoardProduct" "Mac-551B86E5744E2388"
vboxmanage setextradata "macos_12_monterey" "VBoxInternal/Devices/smc/0/Config/DeviceKey" "ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc"
vboxmanage setextradata "macos_12_monterey" "VBoxInternal/Devices/smc/0/Config/GetKeyFromRealSMC" 1
vboxmanage setextradata "macos_12_monterey" "VBoxInternal/TM/TSCMode" "RealTSCOffset"
vboxmanage modifyvm "macos_12_monterey" --cpu-profile "Intel Core i7-6700K"
```

- `LOG:EXITBS:START` error: [Specify CPU profile](https://linustechtips.com/topic/1384626-logexitbsstart-error-while-installing-mac-os-on-virtualbox/)
- Mouse and keyboard not detected: [Use USB 3.0](https://www.reddit.com/r/hackintosh/comments/cyt3mh/no_keyboard_or_mouse_input_on_virtualbox_macos/)
- No disk available at setup: [Create disk with "Disk Utility"](https://www.reddit.com/r/hackintosh/comments/cyt3mh/no_keyboard_or_mouse_input_on_virtualbox_macos/)

### Windows

Setup a Windows 11 VM according to [this guide](https://www.microsoft.com/de-de/software-download/windows11).
