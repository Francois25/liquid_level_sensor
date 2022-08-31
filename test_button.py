from machine import * #lib utilisation module ESP32
import time
import tft_config, st7789 #lib tft pour affichage sur ttgo t-display
import vga1_bold_16x32


button = Pin(35,Pin.IN, Pin.PULL_UP)

tft = tft_config.config()
tft.init()
tft.sleep_mode(True)

if button.value() == 0:
    print("valeur bouton :", button.value())
    tft.sleep_mode(False)
    tft(st7789.DISPOFF)#st7789.YELLOW)
    tft.text(vga1_bold_16x32, "TEST BUTTON", 40, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
    time.sleep(5)
    tft.sleep_mode(True)
else:
    tft.sleep_mode(True)
    print("valeur bouton :", button.value())
