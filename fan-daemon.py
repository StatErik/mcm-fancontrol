#!/usr/bin/python3 -u
#
# Simple daemon to control the fan on a WD MCMgen2 and Ex2U
# Based on fan-daemon of Lorenzo Martignoni for Dlink DNS 320l
#
# Copyright (C) 2022 Nico Maas <mail@nico-maas.de>
# Copyright (C) 2016 Carl Schiller <schreibcarl@gmail.com>
# Copyright (C) 2013 Lorenzo Martignoni <martignlo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import serial
import sys
import time

LOW_TEMP = 40
HIGH_TEMP = 50
HYSTERESIS = 2

POWER_LED_CMD = [
   # Off
   b"\xfa\x03\x06\x00\x00\x01\xfb",
   # On
   b"\xfa\x03\x06\x01\x00\x01\xfb",
   # Blink
   b"\xfa\x03\x06\x02\x00\x01\xfb",
]
DEVICE_READY_CMD = b"\xfa\x03\x01\x00\x00\x00\xfb"

THERMAL_TABLE = (0x74, 0x73, 0x72, 0x71, 0x70, 0x6F, 0x6E, 0x6D, 0x6C, 0x6B,
                 0x6A, 0x69, 0x68, 0x67, 0x66, 0x65, 0x64, 0x63, 0x62, 0x61,
                 0x60, 0x5F, 0x5E, 0x5D, 0x5C, 0x5B, 0x5A, 0x59, 0x58, 0x57,
                 0x56, 0x55, 0x54, 0x53, 0x52, 0x51, 0x50, 0x4F, 0x4E, 0x4D,
                 0x4C, 0x4B, 0x4A, 0x49, 0x48, 0x47, 0x46, 0x45, 0x44, 0x43,
                 0x42, 0x41, 0x41, 0x40, 0x3F, 0x3E, 0x3E, 0x3D, 0x3D, 0x3C,
                 0x3B, 0x3A, 0x3A, 0x39, 0x38, 0x38, 0x37, 0x36, 0x36, 0x35,
                 0x34, 0x34, 0x33, 0x33, 0x32, 0x31, 0x31, 0x30, 0x30, 0x2F,
                 0x2F, 0x2E, 0x2E, 0x2D, 0x2C, 0x2C, 0x2B, 0x2B, 0x2A, 0x2A, 
                 0x29, 0x29, 0x28, 0x28, 0x27, 0x27, 0x27, 0x26, 0x26, 0x25,
                 0x25, 0x24, 0x24, 0x23, 0x23, 0x22, 0x22, 0x21, 0x21, 0x21,
                 0x20, 0x20, 0x1F, 0x1F, 0x1E, 0x1E, 0x1E, 0x1D, 0x1D, 0x1C,
                 0x1C, 0x1B, 0x1B, 0x1B, 0x1B, 0x1A, 0x19, 0x19, 0x19, 0x18,
                 0x18, 0x17, 0x17, 0x25, 0x1B, 0x1B, 0x19, 0x19, 0x19, 0x18,
                 0x18, 0x17, 0x17, 0x16, 0x16, 0x16, 0x15, 0x15, 0x14, 0x14,
                 0x14, 0x13, 0x13, 0x12, 0x12, 0x12, 0x11, 0x11, 0x10, 0x10,
                 0x10, 0xF, 0xF, 0xE, 0xE, 0xE, 0xD, 0xD, 0xC, 0xC, 0xC, 0xB,
                 0xB, 0xA, 0xA, 9, 9, 9, 8, 8, 7, 7, 7, 6, 6, 5, 5, 4, 4, 4, 3,
                 3, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0)

READ_TEMP_CMD = b"\xfa\x03\x08\x00\x00\x00\xfb"

READ_RPM_CMD = b"\xfa\x02\x01\x00\x00\x00\xfb"

FAN_SPEED_CMDS = [
   b"\xfa\x02\x00\x00\x00\x00\xfb",
   b"\xfa\x02\x00\x20\x00\x00\xfb",
   b"\xfa\x02\x00\x35\x00\x00\xfb",
   b"\xfa\x02\x00\x40\x00\x00\xfb",
   b"\xfa\x02\x00\x50\x00\x00\xfb",
   b"\xfa\x02\x00\x60\x00\x00\xfb",
   b"\xfa\x02\x00\x80\x00\x00\xfb",
   b"\xfa\x02\x00\xa0\x00\x00\xfb",
   b"\xfa\x02\x00\xc0\x00\x00\xfb",
   b"\xfa\x02\x00\xd2\x00\x00\xfb",
]

DEBUG = os.getenv("DEBUG", False)


def Debug(fmt, *args):
   if DEBUG:
      print(fmt % args, file=sys.stderr)


def InitSerial():
   port = serial.Serial("/dev/ttyS1", 19200, 8, "N", 1, 0.1)
   return port


def WritePktToSerial(port, data):
   assert len(data) == 7
   port.write(data)
   port.flush()


def ReadPktFromSerial(port, timeout=5):
   tstamp = time.time()
   while time.time() - tstamp < timeout:
      data = port.read(7)
      if data and len(data) == 7 and data[0] == 250 and data[6] == 251:
         return data
   return None


def SetPowerLed(port, status):
   assert status >= 0 and status < len(POWER_LED_CMD)
   WritePktToSerial(port, POWER_LED_CMD[status])
   ReadPktFromSerial(port)
   return status


def ReadTemp(port):
   WritePktToSerial(port, READ_TEMP_CMD)
   data, _ = ReadPktFromSerial(port), ReadPktFromSerial(port)
   if data and data[1] == 3 and data[2] == 8:
      #temp = ord(data[5])
      temp = data[5]
      if temp < len(THERMAL_TABLE):
         return THERMAL_TABLE[temp]
   return None


def ReadRPM(port):
   WritePktToSerial(port, READ_RPM_CMD)
   data, _ = ReadPktFromSerial(port), ReadPktFromSerial(port)
   rpm = ord(data[i])
   print(rpm)
   return None


def SetFanSpeed(port, speed):
   assert speed >= 0 and speed < len(FAN_SPEED_CMDS)
   WritePktToSerial(port, FAN_SPEED_CMDS[speed])
   ReadPktFromSerial(port)
   return speed


def AutoFanControl(port):
   speed = -1
   temp_old = 0
   hyst = HYSTERESIS
   while True:
      try:
         temp = ReadTemp(port)
         Debug("Temp: %d Speed: %d", temp, speed)
         if temp < LOW_TEMP:
            if speed != 0:
               speed = 0
               speed = SetFanSpeed(port, speed)
         elif temp < temp_old:
            hyst -= 1
            if temp < temp_old - hyst:
               speed -= 1
               hyst = HYSTERESIS
               speed = SetFanSpeed(port, speed)
         elif temp > temp_old:
               speed += 1
               speed = SetFanSpeed(port, speed)
         elif temp > HIGH_TEMP:
            if speed != 9:
               speed = 9
               speed = SetFanSpeed(port, speed)
      except Exception as e:
     #    speed = -1
         print("error")
      #print("Debug Temp: %d, %d, %d, %d"%(temp, temp_old, hyst, speed))
      temp_old = temp
      time.sleep(20)


def main():
   port = InitSerial()
   try:
      SetPowerLed(port, 1)
      AutoFanControl(port)
   finally:
      SetFanSpeed(port, 0)
      SetPowerLed(port, 2)


if __name__ == "__main__":
   main()

