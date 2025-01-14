Fancontrol for WD Mycloud Mirror gen2 and Ex2 Ultra.
This is for my personal setup. I use an external 80mm Fan below the NAS to keep it cool. It starts spinning reliably on speed setting 3. So I added an MIN_SPEED setting. For completion there is also a MAX_SPEED setting.
Also a few minor bugs were fixed.

Temperature sensor & fan
------------------------

You can use the fan-daemon.py script to automatically control the speed of the fan depending on the temperature of the board. 

Installation
------------
Instead of the original / Python 2 version by cschil, this script is adapted to support Python 3 and got an Systemd file so that it can automatically start on boot. Also if you have installed hdparm you can set both the ````DEBUG```` and ````HDD_AND_CPU_TEMP```` switches in the Python file to True to allow the script to output Case, CPU, HDD1 and HDD2 temperature every 20 seconds in the journal log.

Basic install: 
````
cp fan-daemon.py /usr/sbin/
chmod +x /usr/sbin/fan-daemon.py
cp fan-daemon.service /etc/systemd/system/
systemctl enable fan-daemon
systemctl start fan-daemon
````

Known bugs
----------
- ReadRPM does not work

Thanks
------
- [Nico Maas](mailto:mail@nico-maas.de) (for the enhanced version)
- [Lorenzo Martignoni](mailto:martignlo@gmail.com) (basic script)
- [Jamie Lentin](http://jamie.lentin.co.uk/)
- [Roberto Paleari](http://roberto.greyhats.it) (for the thermal table)
- [Carl Schiller](https://github.com/cschil) (for adapting the basic script to be used with WD Mycloud Mirror gen2 and Ex2 Ultra)
