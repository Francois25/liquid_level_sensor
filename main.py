import st7789py as st7789
from hcsr04 import HCSR04  # lib capteur HCSR-04

import capteur_temp_humi
import machine
import picoweb  # affichage de la page web, ajouter utemplate, pgk_ressources et ulogging aux lib
import utime
from machine import Pin, PWM, Timer  # lib utilisation module ESP32

import data_analyse
import tft_config  # lib tft pour affichage sur ttgo t-display
import wificonfig
import wificonnect
from romfonts import vga1_16x16 as font3
from romfonts import vga1_8x8 as font1
from romfonts import vga1_bold_16x32 as font4

# --------------------- WIFI ------------------------
#
# enter your wifi ssid and your password in wificonfig file

ipaddress = wificonnect.connectSTA(ssid=wificonfig.ssid, password=wificonfig.password)

# ------------------ SET UP --------------------------
# Taille de la cuve
MAXIMUM_WATER_LEVEL = 1.60  # hauteur d'eau maxi dans la cuve en m
SENSOR_POSITION = 0.22  # distance entre le capteur et le niveau maxi de la cuve en m
CUVE_X = 1.10  # taille de la cuve en X en m
CUVE_Y = 5.68  # taille de la cuve en Y en m
CAPACITE_CUVE = int(round(MAXIMUM_WATER_LEVEL * CUVE_X * CUVE_Y))

# definition des PIN du module ESP32 
frequence_led = 500
led_bleu = PWM(Pin(27, Pin.OUT, 0), frequence_led)
led_verte1 = PWM(Pin(26, Pin.OUT, 0), frequence_led)
led_verte2 = PWM(Pin(25, Pin.OUT, 0), frequence_led)
led_jaune1 = PWM(Pin(33, Pin.OUT, 0), frequence_led)
led_jaune2 = PWM(Pin(32, Pin.OUT, 0), frequence_led)
led_rouge = PWM(Pin(12, Pin.OUT, 0), frequence_led)
buzzer = PWM(Pin(15, Pin.OUT, 0))
button = Pin(35, Pin.IN, Pin.PULL_UP)
button_reset = Pin(0, Pin.IN, Pin.PULL_UP)

# Initialisation de l'écran tft
tfton = not button
tft = tft_config.config()
buzzer.duty(1)

# Définition des variables
SURFACE_CUVE = CUVE_X * CUVE_Y
VOLUME_MAX_CUVE = round(SURFACE_CUVE * MAXIMUM_WATER_LEVEL, 2)
timer = Timer(0)
previous_volume = 0


# Mesure de la température et de l'humidité avec le capteur DHT22
def temperature_humidity_measurement():
    temperature_humidity = capteur_temp_humi.sensor()  # temp, hum
    if temperature_humidity is not None:
        temp = round(temperature_humidity[0], 2)
        print("")
        print("temperature = ", temp)
        hum = round(temperature_humidity[1], 2)
        print("Humidity = ", hum)
        sound_speed = 331.3 + 0.606 * temp
        print(f"Sound speed : {sound_speed}")
        print('')
    else:
        temp = 15
        hum = 0
        sound_speed = 331.3 + 0.606 * temp
        screen_error_temp(temp, hum)

    return sound_speed, temp, hum


# Initialization des LED
def leds_init():
    led_bleu.duty(0)
    led_verte1.duty(0)
    led_verte2.duty(0)
    led_jaune1.duty(0)
    led_jaune2.duty(0)
    led_rouge.duty(0)


# Affichage erreur sur écran tft
def screen_error():
    tft.fill(st7789.BLACK)
    tft.text(font4, "MESURE FAILED", 15, tft.height // 3 - font4.HEIGHT // 2, st7789.RED, st7789.BLACK)
    text = "PUSH RESET"
    length_text = len(text)
    tft.text(font4, text, tft.width // 2 - length_text // 2 * font4.WIDTH, 2 * tft.height // 3 - font4.HEIGHT // 2,
             st7789.RED, st7789.BLACK)


# Affichage d'erreur de mesure température et/ou humidité sur l'écran tft
def screen_error_temp(temp, hum):
    text = f"T: {str(temp)} deg    -    H: {str(hum)} %"
    length_text = len(text)
    tft.text(font1, text, tft.width // 2 - length_text // 2 * font1.WIDTH, 120, st7789.RED, st7789.YELLOW)


# Allumage des LED selon le niveau d'eau mesuré
def analogue_display(volume):
    leds_init()
    buzzer.duty(1)
    if VOLUME_MAX_CUVE > volume >= 0.1 * VOLUME_MAX_CUVE:
        if volume >= 0.9 * VOLUME_MAX_CUVE:
            led_bleu.duty(50)
        elif 0.8 * VOLUME_MAX_CUVE <= volume < 0.9 * VOLUME_MAX_CUVE:
            led_verte1.duty(30)
        elif 0.6 * VOLUME_MAX_CUVE <= volume < 0.8 * VOLUME_MAX_CUVE:
            led_verte2.duty(30)
        elif 0.4 * VOLUME_MAX_CUVE <= volume < 0.6 * VOLUME_MAX_CUVE:
            led_jaune1.duty(30)
        elif 0.2 * VOLUME_MAX_CUVE <= volume < 0.4 * VOLUME_MAX_CUVE:
            led_jaune2.duty(30)
        elif 0.1 * VOLUME_MAX_CUVE <= volume < 0.2 * VOLUME_MAX_CUVE:
            led_rouge.duty(10)
    elif 0 <= volume < 0.1 * VOLUME_MAX_CUVE:
        buzzer.duty(250)
        led_rouge.duty(30)
    elif volume < 0:     
        buzzer.duty(250)
        led_rouge.duty(30)
        led_jaune2.duty(30)
        led_verte2.duty(30)
        led_bleu.duty(30)
    elif volume >= VOLUME_MAX_CUVE:
        led_bleu.duty(100)


# Calcul du volume d'eau dans la cuve
def calculation_volume(sound_speed, temp):
    data = []
    try:
        for i in range(10):
            mesure = HCSR04(trigger_pin=22, echo_pin=21)
            distance_mesuree = mesure.distance_cm() / (1000000 / sound_speed)
            data.append(distance_mesuree)
            print("mesurement ", i, ": ", distance_mesuree)
            utime.sleep(0.5)
        maxi = max(data)
        mini = min(data)
        data.remove(maxi)
        data.remove(mini)
        distance_moyenne = sum(data) / len(data)
        print(f'Valeurs exclues => mini: {round(mini, 4)} et maxi: {round(maxi), 4}')
        if distance_moyenne > 0:
            print(f"Average distance: {round(distance_moyenne, 4)}m")
            volume_available = round(((MAXIMUM_WATER_LEVEL + SENSOR_POSITION) * SURFACE_CUVE) - (distance_moyenne * SURFACE_CUVE), 2)
            print(f"Available volume used: {volume_available}m3")
            return volume_available
        else:
            print("Mesurement <= 0, no sensor response")
            screen_error()
    except Exception:
        print('EXPECT : MEASUREMENT FAILED - SENSOR HCSR KO')
        screen_error()


# Affichage du la hauteur d'eau sur l'écran tft
def digital_display(volume, hum, temp):
    if volume >= (0.95 * VOLUME_MAX_CUVE):
        tft.fill(st7789.CYAN)
        tft.text(font4, "FULL TANK ", 40, tft.height // 2 - font4.HEIGHT // 2, st7789.BLUE, st7789.CYAN)
    elif VOLUME_MAX_CUVE > volume >= 0.1 * VOLUME_MAX_CUVE:
        tft.fill(st7789.BLACK)
        tft.text(font4, "TANK LEVEL", 35, 10, st7789.CYAN)
        tft.text(font3, f"Capacity: {str(CAPACITE_CUVE)}m3", 6, 55, st7789.YELLOW)
        text = f"Remainder:{str(volume)}"
        length_text = len(text)
        tft.text(font3, text, tft.width // 2 - length_text // 2 * font3.WIDTH, 80, st7789.GREEN)
    elif 0 <= volume < 0.1 * VOLUME_MAX_CUVE:
        tft.fill(st7789.YELLOW)
        tft.text(font4, "EMPTY TANK", 45, tft.height // 3 - font4.HEIGHT // 2, st7789.RED, st7789.YELLOW)
        tft.text(font4, "LEVEL < 1 m3", 15, (tft.height // 3) * 2 - font4.HEIGHT // 2, st7789.RED, st7789.YELLOW)
    else:
        screen_error()
    if temp == 15 and hum == 0:
        screen_error_temp(temp, hum)
    else:
        text = f"T: {str(temp)} deg  -  H: {str(hum)} %"
        length_text = len(text)
        tft.text(font1, text, tft.width // 2 - length_text // 2 * font1.WIDTH, 120, st7789.CYAN)


# Allumage de l'écran par appui sur le bouton
def button_push(p):
    tft.sleep_mode(False)
    utime.sleep(5)
    tft.sleep_mode(True)


def button_push_reset(p):
    machine.reset()


# Gestion du système
def handleInterrupt(timer, tfton, previous_volume):
    mesure = temperature_humidity_measurement()  # return sound_speed, temp, hum
    sound_speed = mesure[0]
    temp = mesure[1]
    hum = mesure[2]
    volume_available = calculation_volume(sound_speed, temp)  # round(uniform(9, 10.0), 2)       # return volume_available
    if volume_available:
        digital_display(volume_available, hum, temp)
        if tfton:
            return not tfton
        else:
            tft.sleep_mode(True)
        analogue_display(volume_available)
    if volume_available != previous_volume:
        previous_volume = volume_available
        data_analyse.send_data(volume_available, temp)    
    else:
        print("ERROR : Impossible mesurement")
    timer.init(period=300000, mode=Timer.PERIODIC, callback=handleInterrupt(timer, tfton, previous_volume))  # refresh toutes les minutes


# ---------------------------------------------------------
# --------------------- START PROGRAMME -------------------
# Allumage de l'écran à la mise sous tension
tft.fill(st7789.GREEN)
text = "POWER ON"
length_text = len(text)
tft.text(font4, text, tft.width // 2 - length_text // 2 * font4.WIDTH, 30, st7789.RED, st7789.GREEN)
text = "WAIT...."
length_text = len(text)
tft.text(font4, text, tft.width // 2 - length_text // 2 * font4.WIDTH, 75, st7789.RED, st7789.GREEN)
utime.sleep(3)

# Utilisation du bouton de facade pour allumer l'écran
button.irq(trigger=Pin.IRQ_FALLING, handler=button_push)
button_reset.irq(trigger=Pin.IRQ_FALLING, handler=button_push_reset)
handleInterrupt(timer, tfton, previous_volume)

# ---- Routing Picoweb ------------------------------------
app = picoweb.WebApp(__name__)


@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/index.html')


@app.route("/get_data")
def get_volume(req, resp):
    yield from picoweb.jsonify(resp, {'volume': volume_available, 'temperature': temp, 'humidite': hum})


@app.route("/style.css")
def css(req, resp):
    print("Send style.css")
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/style.css')


@app.route("/goutte_eau.jpg")
def index(req, resp):
    yield from picoweb.start_response(resp)
    try:
        with open("web/goutte_eau.jpg", 'rb') as img_binary:
            img = img_binary.read()
        yield from resp.awrite(img)
        print("Send JPG")
    except Exception:
        print("Image file not found.")


app.run(debug=True, host=ipaddress, port=80)
