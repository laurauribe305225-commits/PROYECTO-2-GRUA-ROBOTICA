from machine import Pin, ADC, PWM
import time

# ---------- POTENCIOMETROS ----------
pot_base = ADC(Pin(34))
pot_brazo = ADC(Pin(35))
pot_base.atten(ADC.ATTN_11DB)
pot_brazo.atten(ADC.ATTN_11DB)
pot_base.width(ADC.WIDTH_12BIT)   # Potenciometro 1: 12 bits -> 0 a 4095
pot_brazo.width(ADC.WIDTH_10BIT)  # Potenciometro 2: 10 bits -> 0 a 1023

# ---------- SERVOS ----------
servo_base = PWM(Pin(18))
servo_base.freq(50)
servo_brazo = PWM(Pin(19))
servo_brazo.freq(50)

# ---------- BOTONES ----------
btn_retorno = Pin(25, Pin.IN, Pin.PULL_UP)
btn_rutina  = Pin(26, Pin.IN, Pin.PULL_UP)

# ---------- LEDS ----------
led_verde = Pin(4, Pin.OUT)
led_rojo  = Pin(5, Pin.OUT)

# ---------- BUZZER ----------
buzzer = PWM(Pin(23))
buzzer.freq(2000)
buzzer.duty(0)

# ---------- VARIABLES GLOBALES ----------
angulo_base = 90
angulo_brazo = 0

flag_retorno = False
flag_rutina  = False
ultimo_tiempo_retorno = 0
ultimo_tiempo_rutina  = 0
DEBOUNCE_MS  = 200

# ---------- INTERRUPCIONES CON ANTIRREBOTE ----------
def isr_retorno(pin):
    global flag_retorno, ultimo_tiempo_retorno
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_tiempo_retorno) > DEBOUNCE_MS:
        flag_retorno = True
        ultimo_tiempo_retorno = ahora

def isr_rutina(pin):
    global flag_rutina, ultimo_tiempo_rutina
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_tiempo_rutina) > DEBOUNCE_MS:
        flag_rutina = True
        ultimo_tiempo_rutina = ahora

btn_retorno.irq(trigger=Pin.IRQ_FALLING, handler=isr_retorno)
btn_rutina.irq(trigger=Pin.IRQ_FALLING, handler=isr_rutina)

# ---------- FUNCION SERVO ----------
def mover_servo(servo, angulo):
    duty = int((angulo / 180) * 75 + 40)
    servo.duty(duty)

# ---------- MOVIMIENTO SUAVE ----------
def mover_suave(servo, inicio, fin):
    paso = 1 if fin > inicio else -1
    for ang in range(inicio, fin, paso):
        mover_servo(servo, ang)
        time.sleep_ms(15)
    mover_servo(servo, fin)

# ---------- BUZZER ON/OFF ----------
def buzzer_on():
    buzzer.duty(800)

def buzzer_off():
    buzzer.duty(0)

# ---------- RETORNO AUTOMATICO ----------
def rutina_retorno():
    global angulo_base, angulo_brazo
    led_verde.off()
    led_rojo.on()
    buzzer_on()
    mover_suave(servo_base,  angulo_base,  90)
    mover_suave(servo_brazo, angulo_brazo, 90)
    angulo_base  = 90
    angulo_brazo = 90
    buzzer_off()
    led_rojo.off()
    led_verde.on()

# ---------- RUTINA AUTOMATICA ----------
def rutina_robot():
    global angulo_base, angulo_brazo
    led_verde.off()
    led_rojo.on()
    buzzer_on()
    mover_suave(servo_base,  angulo_base,  0)
    mover_suave(servo_base,  0,            180)
    mover_suave(servo_brazo, angulo_brazo, 90)
    mover_suave(servo_brazo, 90,           0)
    angulo_base  = 180
    angulo_brazo = 0
    buzzer_off()
    led_rojo.off()
    led_verde.on()

# ---------- INICIO ----------
led_verde.on()
led_rojo.off()
mover_servo(servo_base,  angulo_base)
mover_servo(servo_brazo, angulo_brazo)

# ---------- LOOP PRINCIPAL ----------
while True:
    # BOTON RETORNO (via interrupcion)
    if flag_retorno:
        flag_retorno = False
        rutina_retorno()

    # BOTON RUTINA (via interrupcion)
    elif flag_rutina:
        flag_rutina = False
        rutina_robot()

    # MODO MANUAL
    else:
        led_verde.on()
        led_rojo.off()
        buzzer_off()

        v1 = pot_base.read()   # 0 a 4095 (12 bits)
        v2 = pot_brazo.read()  # 0 a 1023 (10 bits)

        nuevo_base  = int(v1 * 180 / 4095)
        nuevo_brazo = int(v2 * 180 / 1023)

        if abs(nuevo_base - angulo_base) > 2:
            mover_servo(servo_base, nuevo_base)
            angulo_base = nuevo_base

        if abs(nuevo_brazo - angulo_brazo) > 2:
            mover_servo(servo_brazo, nuevo_brazo)
            angulo_brazo = nuevo_brazo

    time.sleep_ms(50)
