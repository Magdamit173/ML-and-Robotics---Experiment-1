// Initialization 
#include <Adafruit_VL53L0X.h>;
#include <Wire.h>

int GREEN_LED = 9;
int YELLOW_LED = 10;
int RED_LED = 11;

int traffic_colors[3] = {GREEN_LED, YELLOW_LED, RED_LED};
String state_machine[5] = {"GREEN", "YELLOW", "RED", "OFF", "DEFAULT"};

int state_index = -1;

unsigned long previous_timestamp = 0;
unsigned long sleep_ms = 500;
unsigned long blink_logic = true;

unsigned long ir_debounced_ms = 350;
unsigned long previous_debounced_timestamp = 0;
unsigned long detected_range[2] = {10, 300}; // in millimeters
bool isObjectAlreadyInRange = false;



Adafruit_VL53L0X vl53l0x = Adafruit_VL53L0X();

void setup() {
    Serial.begin(9600);
    vl53l0x.begin();

    for(int index = 0; index < 3; index++) pinMode(traffic_colors[index], OUTPUT);
    closeAll(); // unnecessary but i still put it. 
}

void loop() {
  
    if (Serial.available() > 0) {
      String serial_input = Serial.readStringUntil('\n'); 
      serial_input.toUpperCase();
      serial_input.trim();

      for(int index = 0; index < 5; index++) if (state_machine[index] == serial_input) state_index = index;

      if (state_index != -1) closeAll();
    }
    
    if(state_index == 0) digitalWrite(GREEN_LED, HIGH); 
    else if(state_index == 1) digitalWrite(YELLOW_LED, HIGH);
    else if (state_index == 2) digitalWrite(RED_LED, HIGH);
    else if (state_index == 4 && (millis() >= sleep_ms + previous_timestamp) ) {
      digitalWrite(YELLOW_LED, blink_logic);
      blink_logic = !blink_logic;
      previous_timestamp = millis();
    }

    // VL53L0X Ranging Measurement
    VL53L0X_RangingMeasurementData_t measure;
    vl53l0x.rangingTest(&measure, false); 

    bool isObjectOnRange = (measure.RangeMilliMeter > detected_range[0]) && (measure.RangeMilliMeter < detected_range[1]);

    if (isObjectOnRange && !isObjectAlreadyInRange) {
        isObjectAlreadyInRange = true;

        Serial.write("ON_OBJECT_ENTER\n");
    }
    else if (isObjectOnRange && isObjectAlreadyInRange) {
        previous_debounced_timestamp = millis();
    }
    else if (!isObjectOnRange && isObjectAlreadyInRange && 
            (millis() - previous_debounced_timestamp >= ir_debounced_ms)) {

        isObjectAlreadyInRange = false;
        Serial.write("ON_OBJECT_LEAVE\n");
    }
}

void closeAll() {
	for(int index = 0; index < 3; index++) digitalWrite(traffic_colors[index], LOW);
}
