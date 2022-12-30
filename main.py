from machine import * #lib utilisation module ESP32
import dht
from hcsr04 import HCSR04 #lib capteur HCSR-04
import time, utime, wificonnect
import tft_config, st7789 #lib tft pour affichage sur ttgo t-display
import picoweb #affichage de la page web, ajouter utemplate, pgk_ressources et ulogging aux lib
import vga1_bold_16x32, vga2_16x16, vga1_8x8, vga2_bold_16x32 # font
import time
import capteur_temp_humi
import wificonfig


# ------------------------------------------------- WIFI ----------------------------------------------------------------------
#
# enter your wifi ssid and your password in wificonfig file

ipaddress = wificonnect.connectSTA(ssid=wificonfig.ssid, password=wificonfig.password)

# ------------------------------------------------ SET UP ------------------------------------------------------------------
# Enter the size of your own tank
maximum_water_level = 1.60   # max level of liquid in meter  / hauteur d'eau maxi dans la cuve en m
sensor_position = 0.22  # distance between sensor and max level in meter / distance entre le capteur et le niveau maxi de la cuve en m
dimension_cuve_X = 1.10  # X size of the tank / taille de la cuve en X en m
dimension_cuve_Y = 5.68  # Y size of the tank / taille de la cuve en Y en m
tank_capacity = int(round(maximum_water_level*dimension_cuve_X*dimension_cuve_Y))

# definition PIN module ESP32
frequence_led = 500
led_bleu = PWM(Pin(27, Pin.OUT, 0), frequence_led)
led_verte1 = PWM(Pin(26, Pin.OUT, 0), frequence_led)
led_verte2 = PWM(Pin(25, Pin.OUT, 0), frequence_led)
led_jaune1 = PWM(Pin(33, Pin.OUT, 0), frequence_led)
led_jaune2 = PWM(Pin(32, Pin.OUT, 0), frequence_led)
led_rouge = PWM(Pin(12, Pin.OUT, 0), frequence_led)
buzzer = PWM(Pin(15, Pin.OUT, 0))
button = Pin(35,Pin.IN, Pin.PULL_UP)

# PIN definition temperature and humidity sensor
sensor = dht.DHT22(Pin(2))

# Display box init
tfton = not button
tft = tft_config.config()
tft.init() # initialisation de l'écran
buzzer.duty(1)

# Variables definition
surface_cuve = dimension_cuve_X * dimension_cuve_Y
volume_max_cuve = round(surface_cuve * maximum_water_level, 2)
volume_available = 0.00
timer = Timer(0)

# Mesurement temperature and humidity on DHT22 sensor
def temperature_humidity_measurement():
    global temp
    global hum
    global sound_speed
    temperature_humidity = capteur_temp_humi.sensor()
    if not temperature_humidity == None:
        temp = round(temperature_humidity[0], 2)
        print("")    
        print("temperature = ", temperature_humidity[0])
        hum = round(temperature_humidity[1], 2)
        print("Humidity = ",temperature_humidity[1])
        sound_speed = 331.3 + 0.606 * temp
        print(f"Sound speed : {sound_speed}")
        print('')
        return sound_speed, temp, hum
    else:
        temp = 15
        hum = 0
        sound_speed = 331.3 + 0.606 * temp
        screen_error_temp()
        return sound_speed, temp, hum


# LEDs initialization 
def leds_init():
    led_bleu.duty(0)
    led_verte1.duty(0)
    led_verte2.duty(0)
    led_jaune1.duty(0)
    led_jaune2.duty(0)
    led_rouge.duty(0)

# Error display on screen
def screen_error():
    tft.fill(st7789.BLACK)
    tft.text(vga1_bold_16x32, "MESURE FAILED", 15, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)
    text = "PUSH RESET"
    length_text=len(text)
    tft.text(vga1_bold_16x32, text, tft.width() // 2 - length_text // 2 * vga1_bold_16x32.WIDTH, 2 * tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)

# Display on screen if mesurement error
def screen_error_temp():
    text = f"T: {str(temp)} deg    -    H: {str(hum)} %"
    length_text = len(text)
    tft.text(vga1_8x8, text, tft.width() // 2 - length_text // 2 * vga1_8x8.WIDTH, 120, st7789.RED, st7789.YELLOW)


# LEDs illumination according to the measured liquid level
def analogue_display():
    global volume_available
    leds_init()
    buzzer.duty(1)
    if volume_max_cuve > volume_available >= 0.1*volume_max_cuve:
        if volume_available >= 0.9*volume_max_cuve:
            led_bleu.duty(50)
        elif 0.8*volume_max_cuve <= volume_available < 0.9*volume_max_cuve:
            led_verte1.duty(30)
        elif 0.6*volume_max_cuve <= volume_available < 0.8*volume_max_cuve:
            led_verte2.duty(30)
        elif 0.4*volume_max_cuve <= volume_available < 0.6*volume_max_cuve:
            led_jaune1.duty(30)
        elif 0.2*volume_max_cuve <= volume_available < 0.4*volume_max_cuve:
            led_jaune2.duty(30)
        elif 0.1*volume_max_cuve <= volume_available < 0.2*volume_max_cuve:
            led_rouge.duty(10)
    elif 0 <= volume_available < 0.1*volume_max_cuve:
        buzzer.duty(250)
        led_rouge.duty(30)
    elif volume_available >= volume_max_cuve:
        led_bleu.duty(100)

# Calculation of the volume of liquid in the tank
def calculation_volume():
    global volume_available
    global temp
    data = []
    try:
        for i in range(1, 10):
            mesure = HCSR04(trigger_pin=22, echo_pin=21)
            distance_mesuree = mesure.distance_cm() / 100
            data.append(distance_mesuree)
            print("mesurement ", i ,": ", distance_mesuree)
            time.sleep(0.05)
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
    except:
        print('EXPECT : MEASUREMENT FAILED - SENSOR HCSR KO')
        screen_error()

# displaying level tank information on the screen 
def digital_display():
    global volume_available
    global temp
    global hum
    if volume_max_cuve > volume_available >= 0.1*volume_max_cuve:
        tft.fill(st7789.BLACK)
        tft.text(vga1_bold_16x32, "TANK LEVEL", 35, 10, st7789.CYAN)
        tft.text(vga2_16x16, f"Capacity: {str(tank_capacity)}m3", 6, 55, st7789.YELLOW)
        text = f"Remainder:{str(volume_available)}"
        length_text = len(text)
        tft.text(vga2_16x16, text, tft.width() // 2 - length_text // 2 * vga2_16x16.WIDTH, 80, st7789.GREEN)
    elif 0 <= volume_available < 0.1*volume_max_cuve:
        tft.fill(st7789.YELLOW)
        tft.text(vga1_bold_16x32, "EMPTY TANK", 45, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
        tft.text(vga1_bold_16x32, "LEVEL < 1 m3", 15, (tft.height() // 3)*2 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
    elif volume_available >= volume_max_cuve:
        tft.fill(st7789.CYAN)
        tft.text(vga1_bold_16x32, "FULL TANK ", 40, tft.height() // 2 - vga1_bold_16x32.HEIGHT//2, st7789.BLUE, st7789.CYAN)
    else:
        screen_error()
    if temp == 15 and hum == 0:
        screen_error_temp()
    else:
        text = f"T: {str(temp)} deg  -  H: {str(hum)} %"
        length_text = len(text)
        tft.text(vga1_8x8, text, tft.width() // 2 - length_text // 2 * vga1_8x8.WIDTH, 120, st7789.CYAN)

# Turning ON display
def button_push(p):
    global tfton
    tfton = True
    tft.on()
    digital_display()

# Management according to the state of the screen:
def handleInterrupt(timer):
    global tfton
    global volume_available
    global sound_speed
    temperature_humidity_measurement()
    mesure_volume = calculation_volume()
    if mesure_volume:
        if tfton:
            tft.on()
            analogue_display()
            digital_display()
            tfton = False
        else:
            tft.off()
            analogue_display()
    else:
        print("ERROR : Impossible mesurement")



# ---------------------------------------------------------
# --------------------- START PROGRAMME -------------------
# Start display
tft.fill(st7789.GREEN)
text = "POWER ON"
length_text = len(text)
tft.text(vga2_bold_16x32, text, tft.width() // 2 - length_text // 2 * vga2_bold_16x32.WIDTH, 30, st7789.RED, st7789.GREEN)
text = "WAIT...."
length_text = len(text)
tft.text(vga2_bold_16x32, text, tft.width() // 2 - length_text // 2 * vga2_bold_16x32.WIDTH, 75, st7789.RED, st7789.GREEN)


# Using the board's push button to turn on the screen
button.irq(trigger=Pin.IRQ_FALLING, handler=button_push)

# restarting the measurement every 10 seconds
timer.init(period=10000, mode=Timer.PERIODIC, callback=handleInterrupt)

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
        pass

app.run(debug=True, host = ipaddress, port = 80)



