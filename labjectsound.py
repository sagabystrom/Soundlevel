
from datetime import datetime, date, time, timedelta
from sense_hat import SenseHat, ACTION_PRESSED
import numpy as np
import pyaudio
import math
import csv

def calculate_rms_to_db(data):
    audio_data = np.frombuffer(data, dtype=np.int16).astype(float)
    rms = np.sqrt(np.mean(np.square(audio_data)))
    return rms

def rms_to_db(rms):
    if rms <= 0:
        return 0
    db = 20 * math.log10(rms)
    return max(db, 0)

def log_event(sound_level, description, night_or_day):
    timestamp = datetime.now()
    with open("sound_events.csv", mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), f"{sound_level:.2f}", description, night_or_day])
    print(f"Event logged at -> {timestamp} -> {sound_level:.2f} dB -> {description}")

def night_event_occured(alerted):
    global night_start, night_end
    try:
        with open("sound_events.csv", mode="r") as file:
            reader = csv.reader(file)
            rows = list(reader)

        last_row = rows[-1]

        night_or_day = last_row[3].strip()

        get_timestamp = datetime.strptime(last_row[0], "%Y-%m-%d %H:%M:%S")

        last_date = get_timestamp.date()
        last_timestamp = get_timestamp.time()

        today = datetime.date()
        now_time = datetime.now().time()

        if (last_line == "Day") and last_date == today and (last_timestamp <= night_end and last_timestamp >= night_start):
        #if ((last_line == "False") and (last_date == today and now_time <= night_end and last_timestamp <= night_end) or (last_date == today - timedelta(days=1) and last_timestamp >= night_start)):
            last_row[3] = "Night"
            rows[-1] = last_row
            with open("sound_events.csv", mode="w") as file:
                reader = csv.reader(file)
                rows = list(reader)
        return True
    except (FileNotFoundError, IndexError):
        return False


def display_senshat(decibel_level, alerted):

    if alerted == True:
        sense.set_pixels(matrix(4))
    else:
        if decibel_level > THRESHOLD_HIGH:
            sense.set_pixels(matrix(1))
        elif decibel_level > THRESHOLD_MID:
            sense.set_pixels(matrix(2))
        elif decibel_level > THRESHOLD_LOW:
            sense.set_pixels(matrix(3))
        else:
            sense.set_pixels(matrix(5))


def matrix(selection):
    r, y, g, b = (255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 0, 0)

    if selection == 1:
        return [r] * 16 + [y] * 24 + [g] * 24
    elif selection == 2:
        return [b] * 16 + [y] * 24 + [g] * 24
    elif selection == 3:
        return [b] * 40 + [g] * 24
    elif selection == 4:
        return [b, b, b, r, r, b, b, b,
                b, b, b, r, r, b, b, b,
                b, b, b, r, r, b, b, b,
                b, b, b, r, r, b, b, b,
                b, b, b, r, r, b, b, b,
                b, b, b, b, b, b, b, b,
                b, b, b, r, r, b, b, b,
                b, b, b, r, r, b, b, b]
    elif selection == 5:
        return [b] * 64


def check_sound_level(decibel_level):
    if decibel_level >= THRESHOLD_HIGH:
        log_event(decibel_level, "High sound detected", "Day")
    elif decibel_level >= THRESHOLD_MID:
        log_event(decibel_level, "Mid sound detected", "Day")
    elif decibel_level >= THRESHOLD_LOW:
        log_event(decibel_level, "Low sound detected", "Day")
    else:
        print(f"Sound Level: {decibel_level:.2f}")


def handle_joystick(event):
    global stop_loop
    if event.action == ACTION_PRESSED:
        stop_loop = True

def get_dB_display():
    data = stream.read(CHUNK, exception_on_overflow=False)
    rms_value = calculate_rms(data)
    decibel_level = rms_to_db(rms_value)

    check_sound_level(decibel_level)

    display_senshat(decibel_level, alerted)

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

sense = SenseHat()

THRESHOLD_HIGH = 70 #120
THRESHOLD_MID = 50 #80
THRESHOLD_LOW = 40 #60

night_start = time(22,40) #time(18,0)
night_end = time(22,44) #time(7,0)


sense.stick.direction_any = handle_joystick

alerted = False

try:
   while True:
       get_dB_display()
       if datetime.now().time() >= night_start and datetime.now().time() <= night_end:
           alerted = night_event_occured(alerted)
           stop_loop = False
       while datetime.now().time() > night_end and alerted == True:
           get_dB_display()

           if stop_loop == True:
               alerted = False
               stop_loop = False
               break
       continue

except KeyboardInterrupt:
    print("Monitoring stopped by user.")
    time.sleep(5)

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    sense.clear()


