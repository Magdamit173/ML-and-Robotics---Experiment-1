from serial import Serial
from time import sleep, time

port = 'COM3'
baudrate = 9600

class TrafficLightSlave: 
    def __init__(self):
        pass

    def slave(self):
        try:
            return Serial(port=port, baudrate=baudrate, timeout=0.05)
        except Exception: 
            return False
    
class TrafficLightOperation: 
    def __init__(self, GREEN_MS=3000, RED_MS=3000, YELLOW_MS=1000):
        self.GREEN_MS = GREEN_MS
        self.RED_MS = RED_MS 
        self.YELLOW_MS = YELLOW_MS
        self.slave = TrafficLightSlave().slave()
        
        self.current_state = "RED"
        self.car_count = 0 
        self.red_light_violations = 0

    def send_command(self, cmd):
        if self.slave:
            self.current_state = cmd
            self.slave.write(f"{cmd}\n".encode())

    def run(self):
        if not self.slave:
            print(f"Error: Connection failed on {port}")
            return

        print("System Monitoring Active...")
        states = [("GREEN", self.GREEN_MS), ("YELLOW", self.YELLOW_MS), 
                  ("RED", self.RED_MS), ("YELLOW", self.YELLOW_MS)]
        
        while True:
            for state, duration in states:
                self.send_command(state)
                start_time = time()
                
                while (time() - start_time) * 1000 < duration:
                    if self.slave.in_waiting > 0:
                        line = self.slave.readline().decode('utf-8').strip()
                        
                        if line == "ON_OBJECT_ENTER":
                            pass 

                        elif line == "ON_OBJECT_LEAVE":
                            self.car_count += 1
                            if self.current_state == "RED":
                                self.red_light_violations += 1
                                print(f"VIOLATION! Car beat the RED light. Total: {self.red_light_violations}")
                            else:
                                print(f"Car passed on {self.current_state}. Total: {self.car_count}")
                    
                    sleep(0.01)

if __name__ == "__main__":
    TrafficLightOperation().run()