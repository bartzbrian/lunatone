from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont, Image, ImageDraw
import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
chans = [17,27,22,23,24,25,5,6,16]
GPIO.setup(chans, GPIO.OUT)

display = i2c(port=1, address=0x3C)
device = sh1106(display)
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-17 Richard Hull and contributors
# See LICENSE.rst for details.
# PYTHON_ARGCOMPLETE_OK

"""
3D starfield simulation.

Adapted from:
http://codentronix.com/2011/05/28/3d-starfield-made-using-python-and-pygame/
"""

from random import randrange

def randLED(led):
    GPIO.output(chans,0)
    if led == 0:
        GPIO.output([17,22,23,25,16,6],1)
    if led == 1:
        GPIO.output([17,27,25,24,5,6],1)
    if led == 2:
        GPIO.output([27,22,23,24,5,16],1)
    

def init_stars(num_stars, max_depth):
    stars = []
    for i in range(num_stars):
        # A star is represented as a list with this format: [X,Y,Z]
        star = [randrange(-25, 25), randrange(-25, 25), randrange(1, max_depth)]
        stars.append(star)
    return stars

def move_and_draw_stars2(stars, max_depth):
    
    origin_x = device.width // 2
    origin_y = device.height // 2

    with canvas(device) as draw:
        for star in stars:
            # The Z component is decreased on each frame.
            star[2] -= 1.5

            # Convert the 3D coordinates to 2D using perspective projection.
            k = 128.0 / star[2]
            x = int(star[0] * k + origin_x)
            y = int(star[1] * k + origin_y)

            # Draw the star (if it is visible in the screen).
            # We calculate the size such that distant stars are smaller than
            # closer stars. Similarly, we make sure that distant stars are
            # darker than closer stars. This is done using Linear Interpolation.
            if 0 <= x < device.width and 0 <= y < device.height:
                size = (1 - float(star[2]) / max_depth) * 4
                shade = "white"
                draw.rectangle((x, y, x + size, y + size), fill=shade)


def move_and_draw_stars1(stars, max_depth):
    origin_x = device.width // 2
    origin_y = device.height // 2
    
    with canvas(device) as draw:
        for star in stars:
            # The Z component is decreased on each frame.
            star[2] -= 1.5

            # If the star has past the screen (I mean Z<=0) then we
            # reposition it far away from the screen (Z=max_depth)
            # with random X and Y coordinates.
            if star[2] <= 0:
                star[0] = randrange(-25, 25)
                star[1] = randrange(-25, 25)
                star[2] = max_depth

            # Convert the 3D coordinates to 2D using perspective projection.
            k = 128.0 / star[2]
            x = int(star[0] * k + origin_x)
            y = int(star[1] * k + origin_y)

            # Draw the star (if it is visible in the screen).
            # We calculate the size such that distant stars are smaller than
            # closer stars. Similarly, we make sure that distant stars are
            # darker than closer stars. This is done using Linear Interpolation.
            if 0 <= x < device.width and 0 <= y < device.height:
                size = (1 - float(star[2]) / max_depth) * 4
                shade = "white"
                draw.rectangle((x, y, x + size, y + size), fill=shade)


def loop():
    stime = time.time()
    ctime = time.time()
    max_depth = 32
    stars = init_stars(512, max_depth)
    led=0
    while (ctime - stime) < 4:
        
        if led == 3:
            led = 0
        randLED(led)
        led += 1

        ctime = time.time()
        move_and_draw_stars1(stars, max_depth)
    while (ctime - stime) < 14:
        if led == 3:
            led = 0
        randLED(led)
        led += 1
        
        ctime = time.time()
        move_and_draw_stars2(stars, max_depth)
    x = 0
    while x < 26:
        with canvas(device) as draw:
            fnt = (ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf', x))
            w, h = draw.textsize('LUNATONE', font=fnt)
            draw.rectangle(device.bounding_box, outline="white", fill="white")
            draw.text(((128-w)/2, 20), 'LUNATONE', font=fnt, fill="black")
            if x == 25:
                time.sleep(3)
                break
        x += 2
def main():
    display = i2c(port=1, address=0x3C)
    device = sh1106(display)
    loop()
