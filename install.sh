#!/bin/sh

# allow usb mode for user

echo "Preparing USB Subsystem..."
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04d8", ATTR{idProduct}=="f372", MODE="0666"' > /tmp/99-luxafor.rules
sudo mv /tmp/99-luxafor.rules /etc/udev/rules.d/99-luxafor.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Python magic..."
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
