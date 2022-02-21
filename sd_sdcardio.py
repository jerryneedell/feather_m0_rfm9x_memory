# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import os
import busio
import digitalio
import board
import storage
import sdcardio

rfm9x_cs = digitalio.DigitalInOut(board.RFM9X_CS)
rfm9x_cs.switch_to_output(True)
# The SD_CS pin is the chip select line.
#
#     The Adalogger Featherwing with ESP8266 Feather, the SD CS pin is on board.D15
#     The Adalogger Featherwing with Atmel M0 Feather, it's on board.D10
#     The Adafruit Feather M0 Adalogger use board.SD_CS
#     For the breakout boards use any pin that is not taken by SPI


# Connect to the card and mount the filesystem.
sdcard = sdcardio.SDCard(board.SPI(), board.D5)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# Use the filesystem as normal! Our files are under /sd

# This helper function will print the contents of the SD
def print_directory(path, tabs=0):
    for file in os.listdir(path):
        stats = os.stat(path + "/" + file)
        filesize = stats[6]
        isdir = stats[0] & 0x4000

        if filesize < 1000:
            sizestr = str(filesize) + " bytes"
        elif filesize < 1000000:
            sizestr = "%0.1f KB" % (filesize / 1000)
        else:
            sizestr = "%0.1f MB" % (filesize / 1000000)

        prettyprintname = ""
        for _ in range(tabs):
            prettyprintname += "   "
        prettyprintname += file
        if isdir:
            prettyprintname += "/"
        print("{0:<40} Size: {1:>10}".format(prettyprintname, sizestr))

        # recursively print directory contents
        if isdir:
            print_directory(path + "/" + file, tabs + 1)


print("Files on filesystem:")
print("====================")
print_directory("/sd")
