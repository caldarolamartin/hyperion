/* QND (quick and dirty) Simple Double Flag Controller
 * version 2019-11-19
 *
 * New in this version:
 * - expanded to three toggle switches
 * - toggle switches are accompanied by a red-green LED
 * - per toggle switch one can toggle two "objects"
 * - each of thos objects can be a regular pins or a servos
 *
 * To upload firmware with Arduino IDE, set it to 'Arduino Nano' and 'Atmega328P (Old Bootloader)'
 * For quick testing the built in Serial Monitor of the Arduino IDE can be used,
 * but any other serial communication should work (python?).
 * Default serial settings:
 *   8 data bits
 *   no parity
 *   one stop bit
 *   baudrate of 9600 (faster baudrates might be possible)
 *   commands should finish with a newline and/or carriage return character
 * To communicate with PC, any serial communication should work as long as it's set to 9600
 *
 *
 * Serial Commands:
 *   1g    set flag 1 to "green" position
 *   1r    set flag 1 to "red" position
 *   2g    set flag 2 to "green" position
 *   2r    set flag 2 to "red" position
 *   3g    set flag 3 to "green" position
 *   3r    set flag 3 to "red" position
 *   1?    returns single character ('g' or 'r') indicating the current state
 *   2?
 *   3?
 *   *IDN?
 *   at   announce true: makes the arduino send a state change (e.g. '1g', if 1 was switched to green)
 *   af   announce off: turns announcing states off
 *   a?   returns the current state of announce
 *
 * The Arduino should be powered with 5V through the usb cable in order for the buttons to work.
 * If include_eeprom is defined it will remember (and implement) the last used states of the two flags and announce on reboot.
 *
 *
 * written by Aron Opheij
 */

// You could flip the meaning of green == true and red == false
// You may want/need to toggle the characters and/or inverse_leds
#define green false
#define red true

// #define DEBUG

#ifdef DEBUG
 #define DEBUG_PRINT(x)  Serial.println (x)
#else
 #define DEBUG_PRINT(x)
#endif

#define include_eeprom       // comment this line to exclude all eeprom memory stuff from code
#define print_start_message  // comment this line if you don't want the arduino to print the start message

// Toggle these parameters to switch between use_servo and use_pin for using a servo or regular pin
#define flag_1a_style use_servo
#define flag_1b_style use_servo
#define flag_2a_style use_servo
#define flag_2b_style use_pin
#define flag_3a_style use_servo
#define flag_3b_style use_pin

// Set the two angles for each (potential) servo:
const int servo_1a_angles[2] = {40,130};
const int servo_1b_angles[2] = {40,130};
const int servo_2a_angles[2] = {40,130};
const int servo_2b_angles[2] = {40,130};
const int servo_3a_angles[2] = {40,130};
const int servo_3b_angles[2] = {40,130};

// This parameter could be used to invert the behaviour of the leds.
// (Might be useful in case of common cathode LEDs instead of common anode)
bool inverse_leds = true;

// The characters for the 'green' and the 'red' state can be changed here:
#define char_green 'g'
#define char_red 'r'

uint32_t debounce_timeout_ms = 50; // button debounce in ms (50ms seems to be good)

const int baudrate = 9600; // Baudrates that work: 9600 (default) and 19200.
// Usually higher baudrates should also work, but they seem to be unstable on this arduino.

// Define pins:
// I suggest to stick with the chosen pin selection
const uint8_t pin_toggle_1_green =A1;     // connect to "green" side of momentary toggle switch
const uint8_t pin_toggle_1_red = 8;       // connect to "red" side of momentary toggle switch
const uint8_t pin_led_1_green =  A0;       // connect to green side of red-green LED with resistor! (using PWM pin leaves option open to use shades of red/orange/yellow/green)
const uint8_t pin_led_1_red =    11; //PWM        // connect to red side of red-green LED with resistor! (using PWM pin leaves option open to use shades of red/orange/yellow/green)
const uint8_t pin_flag_1a =      2;           // connect to servo or something else (make sure not to exceed 20mA),
const uint8_t pin_flag_1b =      3; //PWM    // connect to servo or something else (make sure not to exceed 20mA)

const uint8_t pin_toggle_2_green=A3;
const uint8_t pin_toggle_2_red = A2;
const uint8_t pin_led_2_green =  13;      // connect to green side of red-green LED with resistor! (using PWM pin leaves option open to use shades of red/orange/yellow/green)
const uint8_t pin_led_2_red =    10; //PWM       // connect to red side of red-green LED with resistor! (using PWM pin leaves option open to use shades of red/orange/yellow/green)
const uint8_t pin_flag_2a =      4;
const uint8_t pin_flag_2b =      5; //PWM

const uint8_t pin_toggle_3_green=A5;
const uint8_t pin_toggle_3_red = A4;
const uint8_t pin_led_3_green =  12;     // connect to green side of red-green LED with resistor! (using PWM pin leaves option open to use shades of red/orange/yellow/green)
const uint8_t pin_led_3_red =     9; //PWM    // connect to red side of red-green LED with resistor! (using PWM pin leaves option open to use shades of red/orange/yellow/green)
const uint8_t pin_flag_3a =      7;
const uint8_t pin_flag_3b =      6; //PWM

/////////////////////////////  END OF USER SETTINGS ////////////////////////////////

// You should probably not change anything beyond this point unless you know what you're doing

#include <Servo.h>
// Might not need all of them, but there's plenty of memory
Servo myservo_1a;  // create servo object to control a servo; twelve servo objects can be created on most boards
Servo myservo_1b;
Servo myservo_2a;
Servo myservo_2b;
Servo myservo_3a;
Servo myservo_3b;

#ifdef include_eeprom
  #include <EEPROM.h>
  #define eeprom_offset 0
  const int16_t eeprom_announce= EEPROM.length() - eeprom_offset - 1;
  const int16_t eeprom_flag_1  = EEPROM.length() - eeprom_offset - 2;
  const int16_t eeprom_flag_2  = EEPROM.length() - eeprom_offset - 3;
  const int16_t eeprom_flag_3  = EEPROM.length() - eeprom_offset - 4;
#endif

int8_t switch1_down = 0;
int8_t switch2_down = 0;
int8_t switch3_down = 0;
//int8_t button_pin = 0;          // remove this ?????
bool toggle_1_triggered = false;
bool toggle_2_triggered = false;
bool toggle_3_triggered = false;

bool flag_1_state = green;
bool flag_2_state = green;
bool flag_3_state = green;
bool announce_state = true;

uint32_t timestamp1 = millis();
uint32_t timestamp2 = millis();
uint32_t timestamp3 = millis();

int8_t flag = 0;
char serial_buffer[6] = {0,0,0,0,0,0};
bool serial_in = false;
bool command_a = false;

void setup() {
  Serial.begin(baudrate);

  DEBUG_PRINT("debug is on");

  #ifdef print_start_message
    Serial.println("");
    print_idn();
    Serial.print("Baudrate: ");
    Serial.println(baudrate);
  #endif

  #ifdef include_eeprom
    //Serial.println(EEPROM.length());
    announce_state = EEPROM.read(eeprom_announce);
    flag_1_state = EEPROM.read(eeprom_flag_1);
    flag_2_state = EEPROM.read(eeprom_flag_2);
    flag_3_state = EEPROM.read(eeprom_flag_2);
  #endif

  pinMode(pin_flag_1a, OUTPUT);
  pinMode(pin_flag_1b, OUTPUT);
  pinMode(pin_flag_2a, OUTPUT);
  pinMode(pin_flag_2b, OUTPUT);
  pinMode(pin_flag_3a, OUTPUT);
  pinMode(pin_flag_3b, OUTPUT);

  // initialize the states
  flag_1_state = !flag_1_state;
  flag_2_state = !flag_2_state;
  flag_3_state = !flag_3_state;
  set_flag(1, !flag_1_state);
  set_flag(2, !flag_2_state);
  set_flag(3, !flag_3_state);
  
  pinMode(pin_toggle_1_green,INPUT_PULLUP);
  pinMode(pin_toggle_1_red,  INPUT_PULLUP);
  pinMode(pin_toggle_2_green,INPUT_PULLUP);
  pinMode(pin_toggle_2_red,  INPUT_PULLUP);
  pinMode(pin_toggle_3_green,INPUT_PULLUP);
  pinMode(pin_toggle_3_red,  INPUT_PULLUP);

  pinMode(pin_led_1_green, OUTPUT);
  pinMode(pin_led_1_red, OUTPUT);
  pinMode(pin_led_2_green, OUTPUT);
  pinMode(pin_led_2_red, OUTPUT);
  pinMode(pin_led_3_green, OUTPUT);
  pinMode(pin_led_3_red, OUTPUT);

  #if flag_1a_style == use_servo
    myservo_1a.attach(pin_flag_1a);  // attaches the servo on pin ... to the servo object
  #endif
  #if flag_1b_style == use_servo
    myservo_1b.attach(pin_flag_1b);
  #endif
  #if flag_2a_style == use_servo
    myservo_2a.attach(pin_flag_2a);  // attaches the servo on pin ... to the servo object
  #endif
  #if flag_2b_style == use_servo
    myservo_2b.attach(pin_flag_2b);
  #endif
  #if flag_3a_style == use_servo
    myservo_3a.attach(pin_flag_3a);  // attaches the servo on pin ... to the servo object
  #endif
  #if flag_3b_style == use_servo
    myservo_3b.attach(pin_flag_3b);
  #endif
}

void loop() {

  //if (millis() - timestamp > debounce_timeout_ms) {

  toggle_1_triggered = false;
  if (!digitalRead(pin_toggle_1_green)) {                   // toggle 1 green triggered
    toggle_1_triggered = true;
    if (millis() - timestamp1 > debounce_timeout_ms) {      // if timout 1 expired since last trigger
      if (switch1_down != 1) set_flag(1,green);             // if switch 1 not already down: set_flag
      switch1_down = 1;                                     // set flag switch 1 down
    }
    if (switch1_down == 1) timestamp1 = millis();
  }
  if (!digitalRead(pin_toggle_1_red)) {
    toggle_1_triggered = true;
    if (millis() - timestamp1 > debounce_timeout_ms) {  // if timout expired
      if (switch1_down != -1) set_flag(1,red);  // if button not already down
      switch1_down = -1;
    }
    if (switch1_down == -1) timestamp1 = millis();
  }

  toggle_2_triggered = false;
  if (!digitalRead(pin_toggle_2_green)) {
    toggle_2_triggered = true;
    if (millis() - timestamp2 > debounce_timeout_ms) {  // if timout expired
      if (switch2_down !=1) set_flag(2,green);
      switch2_down = 1;
    }
    if (switch2_down == 1) timestamp2 = millis();
  }
  if (!digitalRead(pin_toggle_2_red)) {
    toggle_2_triggered = true;
    if (millis() - timestamp2 > debounce_timeout_ms) {  // if timout expired
      if (switch2_down != -1) set_flag(2,red);  // if button not already down
      switch2_down = -1;
    }
    if (switch2_down == -1) timestamp2 = millis();
  }

  toggle_3_triggered = false;
  if (!digitalRead(pin_toggle_3_green)) {
    toggle_3_triggered = true;
    if (millis() - timestamp3 > debounce_timeout_ms) {  // if timout expired
      if (switch3_down !=1) set_flag(3,green);
      switch3_down = 1;
    }
    if (switch3_down == 1) timestamp2 = millis();
  }
  if (!digitalRead(pin_toggle_3_red)) {
    toggle_3_triggered = true;
    if (millis() - timestamp2 > debounce_timeout_ms) {  // if timout expired
      if (switch3_down != -1) set_flag(3,red);  // if button not already down
      switch3_down = -1;
    }
    if (switch3_down == -1) timestamp2 = millis();
  }

  if (!toggle_1_triggered) {                              // if switch 1 appears to be in rest position (0,1,2)
    if (millis() - timestamp1 > debounce_timeout_ms) {    // and if timeout has expired
      if (switch1_down) {                                 // and if a button is marked as held down
        switch1_down = 0;                                 // reset button_down
        timestamp1 = millis();                            // reset timestamp so that button is unresponsive for debounce_timeout_ms
      }
    }
  }
  if (!toggle_2_triggered) {                              // if switch 2 appears to be in rest position
    if (millis() - timestamp2 > debounce_timeout_ms) {    // and if timeout has expired
      if (switch2_down) {                                 // and if a button is marked as held down
        switch2_down = 0;                                 // reset button_down
        timestamp2 = millis();                            // reset timestamp so that button is unresponsive for debounce_timeout_ms
      }
    }
  }
  if (!toggle_3_triggered) {                              // if switch 3 appears to be in rest position
    if (millis() - timestamp2 > debounce_timeout_ms) {    // and if timeout has expired
      if (switch3_down) {                                 // and if a button is marked as held down
        switch3_down = 0;                                 // reset button_down
        timestamp3 = millis();                            // reset timestamp so that button is unresponsive for debounce_timeout_ms
      }
    }
  }

//  if (millis() - timestamp > debounce_timeout_ms) {
//    if (!digitalRead(pin_toggle_1_green)) {
//      set_flag(1,green);
//      timestamp = millis();
//    }
//    if (!digitalRead(pin_toggle_1_red)) {
//      set_flag(1,red);
//      timestamp = millis();
//    }
//    if (!digitalRead(pin_toggle_2_green)) {
//      set_flag(2,green);
//      timestamp = millis();
//    }
//    if (!digitalRead(pin_toggle_2_red)) {
//      set_flag(2,red);
//      timestamp = millis();
//    }
//  }

  while (Serial.available() > 0) {
    char ser = Serial.read();
    if ((ser == '\n') || (ser == '\r')) {
      serial_in = true;
      break;
    } else {
      shift_serial_buffer();
      serial_buffer[5] = ser;
    }
  }

  if (serial_in) {
    flag = 0;           // TESTING
    command_a = false;  // TESTING
    for (uint8_t s=0; s<6; s++) {
      switch (serial_buffer[0]) {
        case '1':
          flag = 1;
          command_a = false;
          break;
        case '2':
          flag = 2;
          command_a = false;
          break;
        case '3':
          flag = 3;
          command_a = false;
          break;
        case char_green:
          if (flag) set_flag(flag,green);
          flag = 0;
          break;
        case char_red:
          if (flag) set_flag(flag,red);
          flag = 0;
          break;
        case '?':
          if (flag) {
            query_flag(flag);
          }
          else if (command_a) {
            (announce_state) ? Serial.println('t') : Serial.println('f');
          }
          flag = 0;
          command_a = false;
          break;
        case 'a':
          command_a = true; // setting flag to toggle "announce"
          flag = 0;
          break;
        case 't':
          if (command_a && !announce_state) {
            announce_state = true;
            #ifdef include_eeprom
              EEPROM.update(eeprom_announce, announce_state);
            #endif
          }
          command_a = false;
          break;
        case 'f':
          if (command_a && announce_state) {
            announce_state = false;
            #ifdef include_eeprom
              EEPROM.update(eeprom_announce, announce_state);
            #endif
          }
          command_a = false;
          break;
        case '*':
          check_idn();
          flag = 0;
          command_a = false;
          s=6;
          break;
        default:
          flag = 0;
          command_a = false;
          break;
      }
      shift_serial_buffer();
      serial_buffer[5] = 0;
    }
    serial_in = false;
  }

}

void set_flag(uint8_t sflag, bool state) {
  if (sflag==1) {
    if (flag_1_state != state) {
      flag_1_state = state;
      #if flag_1a_style == use_servo
        myservo_1a.write(servo_1a_angles[state]);
      #else
        digitalWrite(pin_flag_1a, flag_1_state);
      #endif
      #if flag_1b_style == use_servo
        myservo_1b.write(servo_1b_angles[state]);
      #else
        digitalWrite(pin_flag_1a, flag_1_state);
      #endif
      DEBUG_PRINT("hier");
      //digitalWrite(pin_led_1_green, state);
      //digitalWrite(pin_led_1_red, !state );
      digitalWrite(pin_led_1_green, state ^ inverse_leds);
      digitalWrite(pin_led_1_red, !(state^ inverse_leds) );
      #ifdef include_eeprom
        EEPROM.update(eeprom_flag_1, state);
      #endif
    }
    if (announce_state) {
      Serial.print('1');
      (state==red) ? Serial.println(char_red) : Serial.println(char_green);
    }
  }
  if (sflag==2) {
    if (flag_2_state != state) {
      flag_2_state = state;
      #if flag_2a_style == use_servo
        myservo_2a.write(servo_2a_angles[state]);
      #else
        digitalWrite(pin_flag_2a, flag_2_state);
      #endif
      #if flag_2b_style == use_servo
        myservo_2b.write(servo_2b_angles[state]);
      #else
        digitalWrite(pin_flag_2a, flag_2_state);
      #endif
      digitalWrite(pin_led_2_green, state ^ inverse_leds);
      digitalWrite(pin_led_2_red, !(state^ inverse_leds) );
      #ifdef include_eeprom
        EEPROM.update(eeprom_flag_2, flag_2_state);
      #endif
    }
    if (announce_state) {
      Serial.print('2');
      (state==red) ? Serial.println(char_red) : Serial.println(char_green);
    }
  }
  if (sflag==3) {
    if (flag_3_state != state) {
      flag_3_state = state;
      #if flag_3a_style == use_servo
        myservo_3a.write(servo_3a_angles[state]);
      #else
        digitalWrite(pin_flag_3a, flag_3_state);
      #endif
      #if flag_3b_style == use_servo
        myservo_3b.write(servo_3b_angles[state]);
      #else
        digitalWrite(pin_flag_3a, flag_3_state);
      #endif
      digitalWrite(pin_led_3_green, state ^ inverse_leds);
      digitalWrite(pin_led_3_red, !(state^ inverse_leds) );
      #ifdef include_eeprom
        EEPROM.update(eeprom_flag_3, state);
      #endif
    }
    if (announce_state) {
      Serial.print('3');
      (state==red) ? Serial.println(char_red) : Serial.println(char_green);
    }
  }
}

void query_flag(uint8_t qflag) {
  if (qflag==1) {
    (flag_1_state==red) ? Serial.println(char_red) : Serial.println(char_green);
  } else if (qflag==2) {
    (flag_2_state==red) ? Serial.println(char_red) : Serial.println(char_green);
  } else if (qflag==3) {
    (flag_3_state==red) ? Serial.println(char_red) : Serial.println(char_green);
  }

}

void check_idn() {
  char idn[5] = {'*','I','D','N','?'};
  uint8_t s;
  for (s=1; s<5; s++) {
    if ((serial_buffer[s] != idn[s]) && (serial_buffer[s] != idn[s]+32)) {        // the +32 is the equivalent lowercase letter
      return;
    }
  }
  print_idn();
}

void print_idn() {
  Serial.println("QND Simple Double Flag Controller, version 0.2, date 2019-11-19");
}

void shift_serial_buffer() {
  //for (uint8_t b=0; b<
  serial_buffer[0] = serial_buffer[1];
  serial_buffer[1] = serial_buffer[2];
  serial_buffer[2] = serial_buffer[3];
  serial_buffer[3] = serial_buffer[4];
  serial_buffer[4] = serial_buffer[5];
}
