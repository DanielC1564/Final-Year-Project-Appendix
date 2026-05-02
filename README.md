My name is Daniel Connolly and this is my Github Repository for the code in my Final Year Project for Mechatronic Engineering. This file will go over the initial setup required to setup up the Raspberry Pi Os for this project.

# Raspberry Pi OS Setup
The first thing that you need to do is download the Raspberry Pi Imager to allow you to download the Raspberry Pi OS onto an SD card. This can be gotten at the website provided here: [Raspberry Pi Imager](https://www.raspberrypi.com/software/)

When installing the Raspberry Pi Os it is important to choose a version of the OS that is based on the **Bookworm version of Debian**. Bookworm is the codename for the Debian 12 distro and is required for certain libraries for the AI Camera to work correctly. The newest Raspberry Pi OS is based on the Trixie version of Debian which is Debian 13. To download the Bookworm OS go into the Legacy OS tab in the Raspberry Pi Imager and look for the 64-bit OS bookworm based OS. Once the OS is installed on the SD card and booted onto the Raspberry Pi, to check if the installed OS is the correct verion use the code.
```
cat /etc/os-release
```
Once this is done you should see an output that looks similar to the one seen below:
```
PRETTY_NAME="Raspberry Pi OS (64-bit)"
NAME="Raspberry Pi OS"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
ID_LIKE=debian
```
If Debian 12 (bookworm) appears in either the `PRETTY_NAME` or `VERSION` section of the code then you have installed the correct version of the OS.

One this is done it is advised to run a quick update to all the libraries on the Pi to make sure everything is up to date. The following line of code updates the local list of packages on the Pi
```
sudo apt update
```
Running the next command upgrades all installed packages to the latest version.
```
sudo apt full-upgrade
```

# AI Camera Library Setup
The AI Camera used in this project is a Sony **IMX500** that requires specific packages to be downloaded in order for it to function properly. Run the following code to download all the required IMX500 packages:
```
sudo apt install imx500-all
```
After installing the packages, a reboot is needed before the installed packages can be used. Run the following code to reboot the system.
```
sudo reboot
```
Now that all the libraries are installed, it is best to run a quick test program to ensure that all files have been downloaded properly. The following code will turn on the connected AI camera and display a preview to test if the camera is working properly:
```
rpicam-hello -t 0s --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json --viewfinder-width 1920 --viewfinder-height 1080 --framerate 30
```
After the test has been performed and the camera is working properly the next thing to do is to download the Core Electronics AI_camera library that is used in the vision system. The library can be gotten from the attached link: [AI Camera Library](https://core-electronics.com.au/attachments/uploads/ai-camera-library-demo.zip). When this file is unzipped there are some demo code files as well as the ai_camera.py library file. It is important that this library file is stored in the **same working directory** as the code files that are using it otherwise the code will not run.

# Radar Setup
For the radar sensor setup all that was required was to download the required rd03d library. The library is also made by Core Electronics and can be gotten at the attached link: [Rd03d Library](https://core-electronics.com.au/attachments/uploads/rpi_mmwave.zip). Similarly to the AI camera library this zip file will contain some demo code files as well as the required library. This library must also be stored in the **same working directory** as the code file in order for it to run properly.

One last change that may need to be made depends on the type of Raspberry Pi that is being used. If you are using a Raspberry Pi 4, a small edit needs to be made to the library. Open up the rd03d library file and look for the following line of code:
```
def __init__(self, uart_port='/dev/ttyAMA0', baudrate=256000, multi_mode=True):
```
This line initialises the UART communication and is done differently on the Pi 5 compared to older models. Replace it with the following line of code:
```
def __init__(self, uart_port='/dev/ttyS0', baudrate=256000, multi_mode=True):
```
