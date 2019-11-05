/*
Simple sketch for controlling a Red and a White LED from both pc AND with a physical button.
Physical button is now considered a non latching single throw push buton that connects to ground.
Red and White LEDs can be controlled independently. The action of the physical button on the two 
LEDs can be controlled by setting LEDs as 'disabled'.
The 'disaled' state is stored in EEPROM memory of the atmega chip, meaning that it stored even if power is lost.

(Arduino) Serial Monitor is needed to control it.
Make sure you find the right COM port (and that the software is set to Arduino Uno).
Settings or Serial Monitor:
- Baudrate:     9600            (this could be changed in this sketch if necessary, 115200 is probably the fastest working value)
- Line ending:  No line ending. (But others should work, they are ignored)

Internal wiring:
- green   pin 5V
- brown   pin Ground
- purple  pin 2  (interrupt pin for button)
- orange  pin 7
- grey    pin 8

Aron Opheij
2017-09-29
*/


// START OF CODE:
#include <EEPROM.h>   // needed for accessing EEPROM memory

// LED wiring:
// The common anode should be attached to 5V pin
// The individual cathodes should be attached to the following pins, with a current limiting resistor.
// (Note: the current limiting resistor is 'hidden' in the plug connected to the LED)
const byte redSink   = 7;
const byte whiteSink = 8;
// Set these as OUTPUT, and make them low to light up the led, and high to prevent current from flowing.
// These pins were chosen because they don't have any alternative function,
// which makes it more compatible for possible future modifications or additions.

const byte interruptPin = 2;      // for button

// Initial values of the LED.
// It is safer to have these on HIGH, because then the voltage on the 3 pins of the connector is the same.
// If the connector is accidentally connected during this stage, it should be safe, whereas if the connector
// is connected when one of these pins is LOW, an overcurrent could occur, damaging the pins.
volatile byte redState   = HIGH; // HIGH means off (LOW means on)
volatile byte whiteState = HIGH;  // HIGH means off (LOW means on)
// These values are set 'volatile' (always read from ram, not from storage register) because they're used by an interrupt routine.

// Because buttons generally don't switch nicely between open and closed contact, but they actually "bounce".
// I.e. the voltage will switch back and forth several times in a unpredictable manner. This can happen in less then a ms or during many ms.
// Therefore a "debouncing" mechanism needs to be implemented, to ignore the extra switches.
// This could be done in hardware, but here it is done in software which is easier (and maybe also more reliable).
// Settings for debouncing:
unsigned long lastDebounceTime =  0; // the last time the output pin was toggled
unsigned long debounceDelay    = 50; // this can depend on the switch used (if it malfuncions, increase it, but 50 ms should be enough for most switches)


const int addressRed  = 254;
const int addressWhite = 255;

// initialize disabled state by reading stored vallues in EEPROM:
bool disableRed   = EEPROM.read(addressRed);
bool disableWhite = EEPROM.read(addressWhite);

byte line=0;

// Funtion: setup that gets called once after booting. Used for initializing things.
void setup()
{
  // Start communication with PC
  Serial.begin(9600);       // <-- This is the baudrate that should be matched by the serial monitor, max 115200
  
  // Set pin modes and initial values:
  pinMode(redSink, OUTPUT);
  pinMode(whiteSink, OUTPUT);
  digitalWrite(redSink, redState);
  digitalWrite(whiteSink, whiteState);

  // Switch off builtin LED on pin 13
  pinMode(13,OUTPUT);
  pinMode(13,LOW);

  // Set up the interrupt pin for the button:
  pinMode(interruptPin, INPUT_PULLUP);    // When disconnected, it will be pulled UP
  attachInterrupt(digitalPinToInterrupt(interruptPin), toggle_led, LOW);
  // When button contact is closed, the input will go to ground.
  // To avoid bouncing, after a low signal is detected

  // Write some information for the user to the Serial Monitor:
  Serial.println("Connected to Arduino.\n");
  print_help();
  print_current_led_state();
}

// Function: main loop that gets called after setup.
void loop()
{
  bool flagRed = 0;
  bool flagWhite = 0;
  bool flagDisable = 0;
  bool flagInvalid = 0;
  bool toggleMode = 1;
  
  if (Serial.available())   // If data is sent to the Adruino
  {
    delay(10); // wait 10ms to allow buffer to fill
    
    int Nchar = Serial.available();   // Number of characters received
    
    while (Serial.available() > 0)    // While characters available in the serial buffer
    {
      char currentChar = Serial.read();   // read the first character (this will take it out of the buffer)
      
      switch (currentChar)
      {
        // (Programming note: Some cases share quite a lot of code. Code could probably be DRYer)
        case '?':
          break;                        // Do nothing, but also don't set 'invalid'-flag
        case 'd':
          flagDisable = 1;              // Set 'disable'-flag. This is used when interpreting the next character
          toggleMode = 0;
          break;
        case 'r':
          if (flagDisable)
          {
            disableRed = !disableRed;
            flagDisable = 0;
            Serial.print("Manual switch ");
            Serial.print(disableRed ? "DIS" : "EN");      // Look up 'ternary operator' to understand this line
            Serial.println("ABLED on Red LED");
            EEPROM.write(addressRed, disableRed);
          }
          else
          {
            flagRed = 1;                // Set flagRed. This is used when interpreting the next character
          }
          break;
        case 'w':
          if (flagDisable)
          {
            disableWhite = !disableWhite;
            flagDisable = 0;
            Serial.print("Manual switch ");
            Serial.print(disableWhite ? "DIS" : "EN");
            Serial.println("ABLED on White LED");
            EEPROM.write(addressWhite, disableWhite);
          }
          else
          {
            flagWhite = 1;
          }
          break;
        case '1':
          if (flagRed)
          {
            redState = LOW;
            flagRed = 0;
            toggleMode = 0;
          }
          else if (flagWhite)
          {
            whiteState = LOW;
            flagWhite = 0;
            toggleMode = 0;
          }
          else if (Nchar==1)
          {
            whiteState = LOW;
            redState = LOW;
          }
          else
          {
            flagInvalid = 1;        // If none of the previous conditions are met, it must be invalid input
          }
          break;
        case '0':
          if (flagRed)
          {
            redState = HIGH;
            flagRed = 0;
            toggleMode = 0;
          }
          else if (flagWhite)
          {
            whiteState = HIGH;
            flagWhite = 0;
            toggleMode = 0;
          }
          else if (Nchar==1)
          {
            whiteState = HIGH;
            redState = HIGH;
          }
          else
          {
            flagInvalid = 1;
          }
          break;
        case '\r':  // ignore carriage return
          break;
        case '\n':  // ignore newline
          break;
        case ' ':   // ignore space
          break;
        default:
        flagInvalid = 1;        // If none of the previous conditions are met, it must be invalid input
      }
    }
    if (toggleMode)
    {
      if (flagRed)
      {
        redState = !redState;
      }
      if (flagWhite)
      {
        whiteState = !whiteState;
      }
    }
    digitalWrite(redSink,redState);     // light up or dim red LED
    digitalWrite(whiteSink,whiteState); // light up or dim white LED
    print_current_led_state();  `       // write LED state to Serial Monitor
    if (flagInvalid)
    {
      print_invalid();
    }
  }
}

// Function: light up or dim LEDs according to redState and whiteState.
void toggle_led()
{
  // First check if this function was called during the last [debounceDelay] ms.
  // If so: ignore it because it is called because of button bounce.
  // Note: as long as the button is held down, this function keeps being called. ...............................
  if(millis()-lastDebounceTime > debounceDelay)
  {
    if (!disableRed)
    {
      redState = !redState;
      digitalWrite(redSink,redState);
    }
    if (!disableWhite)
    {
      whiteState = !whiteState;
      digitalWrite(whiteSink,whiteState);
    }
    print_current_led_state();
    lastDebounceTime = millis();
  }
}

// Function: prints the LED states to the Serial Monitor.
void print_current_led_state()
{
  if (line<100) Serial.print("0");
  if (line<10) Serial.print("0");
  Serial.print(line);
  line++;
  Serial.print(":  Red LED light is ");
  Serial.print(disableRed ? "DISABLED " : "");
  Serial.print(redState ? "OFF" : "ON ");
  Serial.print(" - White LED light is ");
  Serial.print(disableWhite ? "DISABLED " : "");
  Serial.println(whiteState ? "OFF" : "ON ");
}

// Funtion: print invalid input warning to Serial Monitor. Followed by Usage information.
void print_invalid()
{
  Serial.println("WARNING: Invalid input\n");
  print_help();
}

// Function: print usage information to Serial Monitor.
void print_help()
{
  // This function uses lots of memory, but as long as we don't run out it's not a problem
  Serial.println("Type 'r1' to switch Red LED light on");
  Serial.println("Type 'r0' to switch Red LED light off");
  Serial.println("Type 'r' to toggle Red LED light on/off");
  Serial.println("The same commands with 'w' instead of 'r' for white LED light.");
  Serial.println("Commands can be combined like 'r0 w1' or w0r0");
  Serial.println("Type only '0' ('1') to switch both LED lights off (on)");
  Serial.println("Type '?' to get current LED light state");
  Serial.println("Manual switch inverts both LED light states");
  Serial.println("To disable (and re-enable) the manual switch from acting on a LED, type 'dr' or 'dw'\n");
  Serial.println(">>>  Impotant note: only (dis)connect the plug when arduino is off!  <<<\n");
}

