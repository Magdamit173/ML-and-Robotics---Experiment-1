from serial import Serial
from time import sleep

port = 'COM3'
baudrate = 9600


class TrafficLightSlave: 
    def __init__(self):
        pass

    def slave(self):
        try:
            return Serial(port=port, baudrate=baudrate)
        except Exception: 
            return False
    
class TrafficLightOperation: 
    def __init__(self, GREEN_MS = 1000, RED_MS = 1000, YELLOW_MS = 500):
        self.GREEN_MS = GREEN_MS
        self.RED_MS = RED_MS 
        self.YELLOW_MS = YELLOW_MS
        self.slave = TrafficLightSlave().slave()

    def red(self): 
        if self.slave: 
            self.slave.write(b'RED\n')

    def yellow(self): 
        if self.slave: 
            self.slave.write(b'YELLOW\n')

    def green(self): 
        if self.slave: 
            self.slave.write(b'GREEN\n')

    def sequence(self): 
        seq = [self.green, self.yellow, self.red, self.yellow]
        delay = [self.GREEN_MS, self.YELLOW_MS, self.RED_MS, self.YELLOW_MS]

        for (color_chosen, delay_ms) in zip(seq, delay): 
            color_chosen()
            sleep(delay_ms/1000)
        
    

operation = TrafficLightOperation().sequence()