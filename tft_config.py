""" LilyGo T-DISPLAY 135x240 ST7789 display """

from machine import Pin, SPI, SoftSPI
import st7789py as st7789

TFA = 40
BFA = 40

def config(rotation=1):
    spi = SoftSPI(
    baudrate=20000000,
    polarity=1,
    phase=0,
    sck=Pin(18),
    mosi=Pin(19),
    miso=Pin(13))

    
    return st7789.ST7789(
        spi,
        135,
        240,
        reset=Pin(23, Pin.OUT),
        cs=Pin(5, Pin.OUT),
        dc=Pin(16, Pin.OUT),
        backlight=Pin(4, Pin.OUT),
        rotation=rotation
        #options=options,
        #buffer_size= buffer_size
        )
