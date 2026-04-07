# ESP32-C6-LCD-1.47
I'm using a ESP32-C6-LCD-1.47 for my connection to show me the timer.

## Installation of the Base-Firmware of the ESP32
* download the latest firmware: https://micropython.org/download/ESP32_GENERIC_C6/
To flash:
```
esptool --chip esp32c6 --port /dev/cu.usbmodem2101 erase_flash
esptool --chip esp32c6 --port /dev/cu.usbmodem2101 write_flash -z 0x0 ESP32_GENERIC_C6-20260406-v1.28.0.bin
bck-i-search: write_
```


## Use Thonny
Use Thonny to upload `main.py` as well `st7789.py` to the EPS32.
Make sure to change the Interpreter to "MicroPython (ESP32)" in the Thonny settings.


## Debug
Use the `macos-debug.py` script to debug the ESP32.


## Security
Yes, I know: the UUID's are hardcoded. But there is not really security needed here for this project :)

## Useful References
* https://www.waveshare.com/wiki/ESP32-C6-LCD-1.47
* https://micropython.org/download/ESP32_GENERIC_C6/
* https://github.com/russhughes/st7789py_mpy