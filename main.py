import serial
import time
import threading
from flask import Flask, render_template, jsonify

app = Flask(__name__)
ser = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)

stats = {
    'A': {'G': 0, 'Y': 0, 'R': 0},
    'B': {'G': 0, 'Y': 0, 'R': 0},
    'C': {'G': 0, 'Y': 0, 'R': 0}
}

current_light = {'A': 'R', 'B': 'R', 'C': 'R'}

def set_lights(a, b, c):
    global current_light
    current_light['A'] = a
    current_light['B'] = b
    current_light['C'] = c

    if a == 'G': ser.write(b"GREEN_A\n")
    elif a == 'Y': ser.write(b"YELLOW_A\n")
    elif a == 'R': ser.write(b"RED_A\n")

    if b == 'G': ser.write(b"GREEN_B\n")
    elif b == 'Y': ser.write(b"YELLOW_B\n")
    elif b == 'R': ser.write(b"RED_B\n")

    if c == 'G': ser.write(b"GREEN_C\n")
    elif c == 'Y': ser.write(b"YELLOW_C\n")
    elif c == 'R': ser.write(b"RED_C\n")

def traffic_controller():
    while True:
        set_lights('G', 'R', 'G')
        time.sleep(5)
        set_lights('Y', 'R', 'Y')
        time.sleep(1.5)
        set_lights('R', 'G', 'R')
        time.sleep(5)
        set_lights('R', 'Y', 'R')
        time.sleep(1.5)

def serial_reader():
    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("ON_LEAVE_"):
                    sector = line[-1]
                    if sector in stats:
                        state = current_light[sector]
                        stats[sector][state] += 1
            except:
                pass

threading.Thread(target=traffic_controller, daemon=True).start()
threading.Thread(target=serial_reader, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)