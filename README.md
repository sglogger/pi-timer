# pi-timer
PI Timer


Goal is to remotely control a timer for conferences.


== Installation of Headend ==
The headend (Raspberry pi zero e.g. witch 7" waveshare touchscreen 'Zero-DISP-7A') is installed with raspberry pi desktop.
* https://www.waveshare.com/zero-disp-7a.htm
* https://www.waveshare.com/wiki/Zero-DISP-7A



=== Base System on Raspberry ===
Download Raspberry PI Manager (https://www.raspberrypi.com/software/)

During Installation choose:
- Modell: Raspberry PI Zero 2 W 
- OS: Raspberry Pi OS (Other) > Raspberry PI OS Lite (64bit)
- Memory: <choose the right disk :))>
- Settings:
    - Hostname: pi-timer
    - Localization: Bern / Europe/Zurich / ch
    - User: pitimer / <password>
    - Wlan Settings: according to your data
    - SSH: activate
    - Raspberry PI connect: deactivate
- Save/Write

=== Changes for Waveshare Display ===
From the Waveshare Wiki (https://www.waveshare.com/wiki/Zero-DISP-7A):

After programming, open the config.txt file in the root directory of the TF card and enter the following codes at the end of config.txt. Then, save and safely eject the TF card.
    hdmi_force_hotplug=1 
    config_hdmi_boost=10
    hdmi_group=2 
    hdmi_mode=87 
    hdmi_cvt 1024 600 60 6 0 0 0

== Raspberry Configuration / Further Setup ==

=== Enable Autologin ===
    sudo raspi-config

Select: 1 System Options > S6 Autologin


== Installation OS & Tools ==
1. Update System:
    sudo apt update
    sudo apt upgrade -y 
    sudo apt full-upgrade -y
    sudo reboot

2. Install X-Server:
    sudo apt-get install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox

3. Install other tools:
    sudo apt install git -y

4. Install lightweight Browser:
    sudo apt install falkon -y

````
steven@pi-timer:~$ falkon --help
Usage: falkon [options] [URL...]
QtWebEngine based browser

Options:
  -h, --help                   Displays help on commandline options.
  --help-all                   Displays help, including generic Qt options.
  -v, --version                Displays version information.
  -a, --authors                Displays author information.
  -p, --profile <profileName>  Starts with specified profile.
  -e, --no-extensions          Starts without extensions.
  -i, --private-browsing       Starts private browsing.
  -o, --portable               Starts in portable mode.
  -r, --no-remote              Starts new browser instance.
  -t, --new-tab                Opens new tab.
  -w, --new-window             Opens new window.
  -d, --download-manager       Opens download manager.
  -c, --current-tab <URL>      Opens URL in current tab.
  -u, --open-window <URL>      Opens URL in new window.
  -f, --fullscreen             Toggles fullscreen.
  --wmclass <WM_CLASS>         Application class (X11 only).

Arguments:
  URL                          URLs to open
```

Note: modori is not supported anymore, chromium too big, ...

5. Configure X Server
    sudo vi ~/.xinitrc

add following at the bottom of the file:
``` 
xset s off
xset -dpms
xset s noblank
exec falkon -e -o -f http://localhost:8000/
```



6. Disable unnecessary services & Disable Logging to Reduce Memory Usage:
    sudo systemctl disable --now avahi-daemon.service  # Disable mDNS (not needed)
    sudo systemctl disable --now ModemManager.service  # Disable modem manager
    sudo systemctl disable --now triggerhappy.service  # Disable hotkey daemon
    sudo systemctl disable --now systemd-timesyncd.service  # Disable time sync (use cron instead)
 
    sudo systemctl disable hciuart
    sudo systemctl disable --now systemd-journald
    sudo systemctl disable --now rsyslog

== Installation Luxafer & Server ==

=== Clone Github project ===
    git clone https://github.com/sglogger/pi-timer.git

then:
    cd pi-timer
    ./install.sh
