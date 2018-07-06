# Python CAN Viewer

#### Developed by Kristian Lauszus, 2018

The code is released under the GNU General Public License.
_________

A simple Python CAN Viewer terminal application written in Python. Both Python 2 and Python 3 are supported.

## Usage

The project is using [python-can](https://github.com/hardbyte/python-can) for reading the CAN-Bus, thus it needs to be installed:

```bash
pip install python-can
```

To run the script simply execute:

```bash
python python-can-viewer.py
```

A screenshot of the application can be seen below:

<img src="screenshot.png" width=400/>

The first column is the number of times a frame with the particular ID has been received, next is the timestamp of the frame relative to when the script was started. The third column is the time between the current frame relative to the previous one. Next is the length of the frame and then the data.

The last two columns are the decoded CANopen function code and node ID. If CANopen is not used, then they can simply be ignored.

### Shortcuts

| Key      | Description             |
|:--------:|:-----------------------:|
| ESC/q    | Exit the viewer         |
| c        | Clear the stored frames |
| SPACE    | Pause the viewer        |
| UP/DOWN  | Scroll the viewer       |

### Misc

I would recommend the following board for testing on a Raspberry Pi: <http://skpang.co.uk/catalog/pican2-canbus-board-for-raspberry-pi-23-p-1475.html>.

The CAN interface can be setup like so:

```bash
sudo apt-get -y install can-utils
sudo raspi-config nonint do_spi 0
sudo sh -c 'echo "dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25" >> /boot/config.txt'
sudo sh -c 'echo "dtoverlay=spi0-hw-cs" >> /boot/config.txt'
```

For more information send me an email at <lauszus@gmail.com>.
