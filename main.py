from serial import Serial
import time
import threading
from flask import Flask, render_template, jsonify, request

PORT = 'COM3'
BAUDRATE = 9600

app = Flask(__name__)
serial_conn = None 

durations = {
    "phase_1": 5.0,
    "phase_2": 1.5,
    "phase_3": 5.0,
    "phase_4": 1.5
}

traffic_stats = {
    'A': {'PASS_GREEN': 0, 'PASS_YELLOW': 0, 'VIOLATION_RED': 0},
    'B': {'PASS_GREEN': 0, 'PASS_YELLOW': 0, 'VIOLATION_RED': 0},
    'C': {'PASS_GREEN': 0, 'PASS_YELLOW': 0, 'VIOLATION_RED': 0}
}

system_state = {
    "active_phase": {'A': 'RED', 'B': 'RED', 'C': 'RED'},
    "phase_end_time": 0,
    "is_paused": False,
    "adaptive_mode": False
}

def calculate_adaptive_timing():
    if not system_state["adaptive_mode"]: return
    
    count_ac = traffic_stats['A']['PASS_GREEN'] + traffic_stats['C']['PASS_GREEN'] + 1 
    count_b = traffic_stats['B']['PASS_GREEN'] + 1
    total_traffic = count_ac + count_b
    
    current_total_green = durations["phase_1"] + durations["phase_3"]
    
    ratio_ac = count_ac / total_traffic
    ratio_b = count_b / total_traffic
    
    durations["phase_1"] = round(max(2.0, current_total_green * ratio_ac), 1)
    durations["phase_3"] = round(max(2.0, current_total_green * ratio_b), 1)

def execute_phase(sa, sb, sc, phase_key):
    global system_state
    d = durations[phase_key]
    system_state["active_phase"].update({'A': sa, 'B': sb, 'C': sc})
    system_state["phase_end_time"] = time.time() + d
    
    if serial_conn:
        for cmd in [f'{sa}_A\n', f'{sb}_B\n', f'{sc}_C\n']:
            serial_conn.write(cmd.encode('utf-8'))
            time.sleep(0.05)
            
    while True:
        if system_state["is_paused"]:
            system_state["phase_end_time"] += 0.1
        elif time.time() >= system_state["phase_end_time"]:
            break
        time.sleep(0.1)

def logic_loop():
    global serial_conn
    try:
        serial_conn = Serial(port=PORT, baudrate=BAUDRATE, timeout=0.1)
        start = time.time()
        while (time.time() - start) < 5:
            if serial_conn.in_waiting > 0:
                if "READY" in serial_conn.readline().decode(errors='ignore'): break
        while True:
            execute_phase("GREEN", "RED", "GREEN", "phase_1")
            execute_phase("YELLOW", "RED", "YELLOW", "phase_2")
            execute_phase("RED", "GREEN", "RED", "phase_3")
            execute_phase("RED", "YELLOW", "RED", "phase_4")
            calculate_adaptive_timing()
    except: pass

def serial_reader():
    while True:
        if serial_conn and serial_conn.in_waiting > 0:
            try:
                line = serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("ON_LEAVE_"):
                    sec = line[-1]
                    state = system_state["active_phase"].get(sec)
                    if state:
                        key = f"PASS_{state}" if state != "RED" else "VIOLATION_RED"
                        traffic_stats[sec][key] += 1
            except: pass
        time.sleep(0.01)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/status')
def get_status():
    return jsonify({
        "stats": traffic_stats, 
        "state": system_state, 
        "durations": durations,
        "server_time": time.time()
    })

@app.route('/toggle_feature', methods=['POST'])
def toggle_feature():
    feat = request.json.get("feature")
    if feat in system_state:
        system_state[feat] = not system_state[feat]
    return jsonify({"status": "ok", "state": system_state.get(feat)})

@app.route('/toggle_pause', methods=['POST'])
def toggle_pause():
    system_state["is_paused"] = not system_state["is_paused"]
    return jsonify({"status": "ok", "is_paused": system_state["is_paused"]})

@app.route('/update_timers', methods=['POST'])
def update_timers():
    data = request.json
    for key in durations:
        if key in data: durations[key] = float(data[key])
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    threading.Thread(target=logic_loop, daemon=True).start()
    threading.Thread(target=serial_reader, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)