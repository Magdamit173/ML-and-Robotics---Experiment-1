from serial import Serial
import time
import threading
from flask import Flask, render_template, jsonify

PORT = 'COM3'
BAUDRATE = 9600

app = Flask(__name__)
serial = None 

traffic_stats = {
    'A': {'PASS_GREEN': 0, 'PASS_YELLOW': 0, 'VIOLATION_RED': 0},
    'B': {'PASS_GREEN': 0, 'PASS_YELLOW': 0, 'VIOLATION_RED': 0},
    'C': {'PASS_GREEN': 0, 'PASS_YELLOW': 0, 'VIOLATION_RED': 0}
}

active_phase = {'A': 'RED', 'B': 'RED', 'C': 'RED'}

def handshake(serial, timeout = 5.0): 
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        if serial.in_waiting > 0:
            try:
                line = serial.readline().decode("utf-8").strip()
                if line == "READY":
                    return True
            except:
                pass
    return False

def traffic_command(serial, SECTOR_A, SECTOR_B, SECTOR_C):
    global active_phase
    active_phase['A'], active_phase['B'], active_phase['C'] = SECTOR_A, SECTOR_B, SECTOR_C

    serial_commands = [f'{SECTOR_A}_A\n', f'{SECTOR_B}_B\n', f'{SECTOR_C}_C\n']
    for command in serial_commands:
        serial.write(command.encode('utf-8'))
        time.sleep(0.05)

def update(): 
    global serial
    try:
        serial = Serial(port=PORT, baudrate=BAUDRATE)
        if not handshake(serial): return
            
        while True:
            traffic_command(serial, "GREEN", "RED", "GREEN")
            time.sleep(5)    
            traffic_command(serial, "YELLOW", "RED", "YELLOW")
            time.sleep(1.5)    
            traffic_command(serial, "RED", "GREEN", "RED")
            time.sleep(5)    
            traffic_command(serial, "RED", "YELLOW", "RED")
            time.sleep(1.5)
    except:
        pass

def serial_reader():
    while True:
        if serial and serial.in_waiting > 0:
            try:
                line = serial.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("ON_LEAVE_"):
                    sector = line[-1]
                    state = active_phase[sector]
                    if state == 'GREEN': traffic_stats[sector]['PASS_GREEN'] += 1
                    elif state == 'YELLOW': traffic_stats[sector]['PASS_YELLOW'] += 1
                    elif state == 'RED': traffic_stats[sector]['VIOLATION_RED'] += 1
            except:
                pass
        time.sleep(0.01)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    return jsonify(traffic_stats)

if __name__ == "__main__":
    threading.Thread(target=update, daemon=True).start()
    threading.Thread(target=serial_reader, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)