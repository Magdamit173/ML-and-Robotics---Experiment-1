const int BAUDRATE = 9600;
const int SECTORS_SHAPE = 9;
const int SENSORS_SHAPE = 3;

const int GREEN_A = 2; 
const int YELLOW_A = 3; 
const int RED_A = 4;

const int GREEN_B = 5; 
const int YELLOW_B = 6; 
const int RED_B = 7;

const int GREEN_C = 8;
const int YELLOW_C = 9;
const int RED_C = 10;

const int SENSOR_A = A0; 
const int SENSOR_B = A1; 
const int SENSOR_C = A2;

const float SENSOR_TOLERANCE = 100;

unsigned long sensor_timestamps[3] = {0, 0, 0};
bool sensor_onrange[3] = {false, false, false};
bool sensor_entered[3] = {false, false, false};
unsigned long sensor_sleep_ms = 250;

unsigned long sensor_modes[3] = {0, 0, 0};
unsigned long previous_timestamp = 0;
unsigned long sleep_ms = 500;
bool blink_state = false;

int default_modes[3] = {0, 0, 0};

const int SECTOR_PINS[SECTORS_SHAPE] = {GREEN_A, YELLOW_A, RED_A, GREEN_B, YELLOW_B, RED_B, GREEN_C, YELLOW_C, RED_C};
const String SECTOR_KEYWORD[SECTORS_SHAPE] = {"GREEN_A", "YELLOW_A", "RED_A", "GREEN_B", "YELLOW_B", "RED_B", "GREEN_C", "YELLOW_C", "RED_C"};

void initialized_sectors() {
  for(int i = 0; i < SECTORS_SHAPE; i++) pinMode(SECTOR_PINS[i], OUTPUT);
}

void setAllOff() {
  for(int i = 0; i < 3; i++) default_modes[i] = 0;
  for(int i = 0; i < SECTORS_SHAPE; i++) digitalWrite(SECTOR_PINS[i], LOW);
}

int pinFinder(String serial_args) {
  for(int i = 0; i < SECTORS_SHAPE; i++) if (serial_args == SECTOR_KEYWORD[i]) return i;
  return -1;
}

void stateMatchine(String serial_args) {
  int sector_index = pinFinder(serial_args);

  if (sector_index >= 0) {
    int sector_id = sector_index / 3;
    default_modes[sector_id] = 0; 
    
    int sector_start = sector_id * 3;
    for (int i = sector_start; i < sector_start + 3; i++) digitalWrite(SECTOR_PINS[i], LOW);
    digitalWrite(SECTOR_PINS[sector_index], HIGH);
  } 
  else if (serial_args == "OFF") {
    setAllOff();
  } 
  else if (serial_args.startsWith("DEFAULT_")) {
    char sector_char = serial_args[8]; 
    int sector_id = sector_char - 'A'; 
    
    if (sector_id >= 0 && sector_id < 3) {
      default_modes[sector_id] = 1;
      int sector_start = sector_id * 3;
      digitalWrite(SECTOR_PINS[sector_start], LOW);     
      digitalWrite(SECTOR_PINS[sector_start + 2], LOW); 
    }
  }
}

void handleBlink() {
  if (millis() - previous_timestamp >= sleep_ms) {
    previous_timestamp = millis();
    blink_state = !blink_state;

    for (int i = 0; i < 3; i++) if (default_modes[i] == 1) digitalWrite(SECTOR_PINS[(i * 3) + 1], blink_state);
  }
}

void handleSensors() {
    unsigned long ANALOG_SENSORS[SENSORS_SHAPE] = {analogRead(SENSOR_A), analogRead(SENSOR_B), analogRead(SENSOR_C)};

    for(int sensor_index = 0; sensor_index < SENSORS_SHAPE; sensor_index++) 
    {
        if (ANALOG_SENSORS[sensor_index] <= SENSOR_TOLERANCE) sensor_onrange[sensor_index] = true;
        else sensor_onrange[sensor_index] = false;

        char initialCharacter = 'A' + sensor_index;

        if (sensor_onrange[sensor_index] && !sensor_entered[sensor_index]) {
            sensor_entered[sensor_index] = true;
            sensor_timestamps[sensor_index] = millis();
            Serial.write("ON_ENTER_");
            Serial.write(initialCharacter);
            Serial.write("\n");
        }
        else if (sensor_onrange[sensor_index] && sensor_entered[sensor_index]) {
            sensor_timestamps[sensor_index] = millis();
        }
        else if (!sensor_onrange[sensor_index] && sensor_entered[sensor_index] && (millis() - sensor_timestamps[sensor_index] >= sensor_sleep_ms)) {
            sensor_entered[sensor_index] = false;
            Serial.write("ON_LEAVE_");
            Serial.write(initialCharacter);
            Serial.write("\n");
        }
    }
}

void setup() {
  Serial.begin(BAUDRATE);
  initialized_sectors();
}

void loop() {
  if (Serial.available() > 0) {
    String serial_cli = Serial.readStringUntil('\n');
    serial_cli.trim();
    serial_cli.toUpperCase();
    stateMatchine(serial_cli);
  }
  handleBlink();
  handleSensors();
}