from machine import * #lib utilisation module ESP32
import dht
from hcsr04 import HCSR04 #lib capteur HCSR-04
import utime, wificonnect
import tft_config, st7789 #lib tft pour affichage sur ttgo t-display
import picoweb #affichage de la page web, ajouter utemplate, pgk_ressources et ulogging aux lib
import vga1_bold_16x32, vga2_16x16, vga1_8x8, vga2_bold_16x32 # font
import capteur_temp_humi
import wificonfig
import data_analyse
import gc

# effacement de la mémoire du module ESP
gc.collect()

# ------------------------------------------------- WIFI ----------------------------------------------------------------------
#
# enter your wifi ssid and your password in wificonfig file

ipaddress = wificonnect.connectSTA(ssid=wificonfig.ssid, password=wificonfig.password)

# ------------------------------------------------ SET UP ------------------------------------------------------------------
# Taille de la cuve
maximum_water_level = 1.60   # hauteur d'eau maxi dans la cuve en m
sensor_position = 0.22  # distance entre le capteur et le niveau maxi de la cuve en m
dimension_cuve_X = 1.10  # taille de la cuve en X en m
dimension_cuve_Y = 5.68  # taille de la cuve en Y en m
tank_capacity = int(round(maximum_water_level*dimension_cuve_X*dimension_cuve_Y))

# definition des PIN du module ESP32
frequence_led = 500
led_bleu = PWM(Pin(27, Pin.OUT, 0), frequence_led)
led_verte1 = PWM(Pin(26, Pin.OUT, 0), frequence_led)
led_verte2 = PWM(Pin(25, Pin.OUT, 0), frequence_led)
led_jaune1 = PWM(Pin(33, Pin.OUT, 0), frequence_led)
led_jaune2 = PWM(Pin(32, Pin.OUT, 0), frequence_led)
led_rouge = PWM(Pin(12, Pin.OUT, 0), frequence_led)
buzzer = PWM(Pin(15, Pin.OUT, 0))
button = Pin(35,Pin.IN, Pin.PULL_UP)

# Définition du PIN du capteur de temperature et d'humidité
sensor = dht.DHT22(Pin(2))

# Initialisation de l'écran tft
tfton = not button
tft = tft_config.config()
tft.init() # initialisation de l'écran
buzzer.duty(1)

# Définition des variables
surface_cuve = dimension_cuve_X * dimension_cuve_Y
volume_max_cuve = round(surface_cuve * maximum_water_level, 2)
timer = Timer(0)

# Mesure de la température et de l'humidité avec le capteur DHT22
def temperature_humidity_measurement():
    temperature_humidity = capteur_temp_humi.sensor() # temp, hum
    if temperature_humidity is not None:
        temp = round(temperature_humidity[0], 2)
        print("")
        print("temperature = ", temp)
        hum = round(temperature_humidity[1], 2)
        print("Humidity = ",hum)
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
    tft.text(vga1_bold_16x32, "MESURE FAILED", 15, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)
    text = "PUSH RESET"
    length_text=len(text)
    tft.text(vga1_bold_16x32, text, tft.width() // 2 - length_text // 2 * vga1_bold_16x32.WIDTH, 2 * tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)

# Affichage d'erreur de mesure température et/ou humidité sur l'écran tft
def screen_error_temp(temp, hum):
    text = f"T: {str(temp)} deg    -    H: {str(hum)} %"
    length_text = len(text)
    tft.text(vga1_8x8, text, tft.width() // 2 - length_text // 2 * vga1_8x8.WIDTH, 120, st7789.RED, st7789.YELLOW)


# Allumage des LED selon le niveau d'eau mesuré
def analogue_display(volume):
    leds_init()
    buzzer.duty(1)
    if volume_max_cuve > volume_available >= 0.1*volume_max_cuve:
        if volume >= 0.9*volume_max_cuve:
            led_bleu.duty(50)
        elif 0.8*volume_max_cuve <= volume < 0.9*volume_max_cuve:
            led_verte1.duty(30)
        elif 0.6*volume_max_cuve <= volume < 0.8*volume_max_cuve:
            led_verte2.duty(30)
        elif 0.4*volume_max_cuve <= volume < 0.6*volume_max_cuve:
            led_jaune1.duty(30)
        elif 0.2*volume_max_cuve <= volume < 0.4*volume_max_cuve:
            led_jaune2.duty(30)
        elif 0.1*volume_max_cuve <= volume < 0.2*volume_max_cuve:
            led_rouge.duty(10)
    elif 0 <= volume < 0.1*volume_max_cuve:
        buzzer.duty(250)
        led_rouge.duty(30)
    elif volume >= volume_max_cuve:
        led_bleu.duty(100)

# Calcul du volume d'eau dans la cuve
def calculation_volume(sound_speed, temp):
    data = []
    try:
        for i in range(1, 10):
            mesure = HCSR04(trigger_pin=22, echo_pin=21)
            distance_mesuree = mesure.distance_cm() / 100
            data.append(distance_mesuree)
            print("mesurement ", i ,": ", distance_mesuree)
            utime.sleep(0.05)
        distance_moyenne = sum(data)/len(data)
        distance_moyenne_corrigee = (distance_moyenne * temp) / 19.5
        if distance_moyenne > 0:
            print(f"average distance: {distance_moyenne}m")
            print(f"distance used: {distance_moyenne_corrigee}m")
            volume_available_avant_correction = round(((maximum_water_level + sensor_position) * surface_cuve) - (distance_moyenne * surface_cuve), 2)
            print(f"Volume before correction: {volume_available_avant_correction}m3")
            volume_available = round(((maximum_water_level + sensor_position) * surface_cuve) - (distance_moyenne_corrigee * surface_cuve), 2)
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
    if volume_max_cuve > volume >= 0.1*volume_max_cuve:
        tft.fill(st7789.BLACK)
        tft.text(vga1_bold_16x32, "TANK LEVEL", 35, 10, st7789.CYAN)
        tft.text(vga2_16x16, f"Capacity: {str(tank_capacity)}m3", 6, 55, st7789.YELLOW)
        text = f"Remainder:{str(volume)}"
        length_text = len(text)
        tft.text(vga2_16x16, text, tft.width() // 2 - length_text // 2 * vga2_16x16.WIDTH, 80, st7789.GREEN)
    elif 0 <= volume < 0.1*volume_max_cuve:
        tft.fill(st7789.YELLOW)
        tft.text(vga1_bold_16x32, "EMPTY TANK", 45, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
        tft.text(vga1_bold_16x32, "LEVEL < 1 m3", 15, (tft.height() // 3)*2 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
    elif volume >= volume_max_cuve:
        tft.fill(st7789.CYAN)
        tft.text(vga1_bold_16x32, "FULL TANK ", 40, tft.height() // 2 - vga1_bold_16x32.HEIGHT//2, st7789.BLUE, st7789.CYAN)
    else:
        screen_error()
    if temp == 15 and hum == 0:
        screen_error_temp(temp, hum)
    else:
        text = f"T: {str(temp)} deg  -  H: {str(hum)} %"
        length_text = len(text)
        tft.text(vga1_8x8, text, tft.width() // 2 - length_text // 2 * vga1_8x8.WIDTH, 120, st7789.CYAN)

# Allumage de l'écran par appui sur le bouton
def button_push(p):
    tft.on()
    digital_display()
    return True

# Gestion du système
def handleInterrupt(timer, tfton):
    mesure = temperature_humidity_measurement()      # return sound_speed, temp, hum
    sound_speed=mesure[0]
    temp = mesure[1]
    hum = mesure[2]
    volume_available = calculation_volume(sound_speed, temp)       # return volume_available
    if volume_available:
        if tfton:
            tft.on()
            analogue_display(volume_available)
            digital_display(volume_available, hum, temp)
            tfton = False
            return tfton
        else:
            tft.off()
            analogue_display(volume_available)
        data_analyse.send_data(volume_available)
    else:
        print("ERROR : Impossible mesurement")



# ---------------------------------------------------------
# --------------------- START PROGRAMME -------------------
# Allumage de l'écran à la mise sous tension
tft.fill(st7789.GREEN)
text = "POWER ON"
length_text = len(text)
tft.text(vga2_bold_16x32, text, tft.width() // 2 - length_text // 2 * vga2_bold_16x32.WIDTH, 30, st7789.RED, st7789.GREEN)
text = "WAIT...."
length_text = len(text)
tft.text(vga2_bold_16x32, text, tft.width() // 2 - length_text // 2 * vga2_bold_16x32.WIDTH, 75, st7789.RED, st7789.GREEN)


# Utilisation du bouton de facade pour allumer l'écran
button.irq(trigger=Pin.IRQ_FALLING, handler=button_push)

# Cycle de mesure toutes les 10 minutes
timer.init(period=600000, mode=Timer.PERIODIC, callback=handleInterrupt) # refresh toutes les 10 mn

# ---- Routing Picoweb ------------------------------------ 
app = picoweb.WebApp(__name__)
@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/index.html')

@app.route("/get_data")
def get_volume(req, resp):
    global volume_available
    global temp
    global hum
    yield from picoweb.jsonify(resp, {'volume': volume_available, 'temperature': temp, 'humidite': hum})

@app.route("/style.css")
def css(req, resp):
    print("Send style.css")
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/style.css')
    
@app.route("/goutte_eau.jpg")
def index(req, resp):
    print("Send JPG")
    yield from picoweb.start_response(resp)
    try:
        with open("web/goutte_eau.jpg", 'rb') as img_binary:
            img= img_binary.read()
        yield from resp.awrite(img)
    except Exception:
        print("Image file not found.")

app.run(debug=True, host = ipaddress, port = 80)

