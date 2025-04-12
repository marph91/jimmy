Documentation how to get sample exports from "difficult" apps. Difficult means that I don't have access through my phone, Linux desktop or Windows VM.

## All Apple only Apps

!!! note
    "TODO"

## FuseBase/Nimbus Note

> Server backups are available only with Plus or Ultimate plans.

Server backups contain the whole workspace. At least single page exports are possible. 

## Samsung Notes

Inside a Windows VM:

1. Install Samsung Notes
2. Launch Samsung Notes by executing [this script](https://github.com/kellwinr/galaxybook_mask/blob/c72333f22dc3be130887b5d0fe9666f3b524902a/samsungnotes-directlaunch.bat). The script does the following steps:
    1. Set `HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\BIOS\SystemProductName` to `NP960XFG-KC4UK`
    2. Set `HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\BIOS\SystemManufacturer` to `Samsung`
    3. Start Samsung Notes
    4. Restore the original registry values

## Synology Note Station

1. Go to the [demo page](https://demo.synology.com/de-de/dsm) and press the "Test" button
2. Open Note Station by Apps -> Note Station on the top left
3. Files can be transferred through the file system

## Turtl

- Linux app crashes always
- Android app still works

## Wikimedia

Export at https://de.wikipedia.org/wiki/Spezial:Exportieren.
