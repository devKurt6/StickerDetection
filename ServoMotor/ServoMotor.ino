#include <Servo.h>
#include <SPI.h>
#include <Ethernet.h>
#include <SPI.h>
#include <DMD2.h>
#include <fonts/SystemFont5x7.h>
#include <fonts/Arial14.h>
Servo servo;

const char* MESSAGE = "abcdefghijklmnopqrstuvwxyz";
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };  // MAC Address of your Ethernet shield
IPAddress ip(192, 168, 1, 177);                       // IP Address of your Arduino
EthernetServer server(80);                            // Create a server at port 80
bool triggered = false;                               // Flag to track if action is triggered for display counting capacity of parking slot exit
bool triggered2 = false;
bool triggered3 = false;  // Flag to track if action is triggered for display counting capacity of parking slot entry
const int WIDTH = 1;      // Set Width to the number of displays wide you have
// and uncommenting the line after it:
const uint8_t* FONT = Arial14;
SoftDMD dmd(1, 1);  // DMD controls the entire display
DMD_TextBox box(dmd);

// const int irSensorPin4 = A3;
// const int irSensorPin3 = A2;
const int irSensorPin2 = A2;
const int irSensorPin = A1;
const int rLed = 12;
const int gLed = 1;

int carSlot = 20;
int motorSlot = 40;
int Contrast = 75;
int total;
int total2;
int carNo = 0;
int angle = servo.read();
EthernetClient client;
EthernetClient client_connected;
void upServo(int total) {
  Serial.println("Up");
  for (int angle = servo.read(); angle <= 60; angle += 1) {
    servo.write(angle);
    delay(70);  // Delay for smooth movement
  }
  triggered2 = true;
  triggered3 = false;
}

void downServo(int total2) {
  Serial.println("Down");
  for (int angle = servo.read(); angle >= 0; angle -= 1) {
    servo.write(angle);
    delay(70);  // Delay for smooth movement
    int sensorValue2 = analogRead(irSensorPin2);
    total2 = (sensorValue2 / 1023.0) * 100;  // Convert to percentage correctly
    if (total2 >= 7) {
      triggered2 = true;  //prevent to close gate if there are car in front of sensor
      break;
    }
  }
  // triggered2 = false;
}

void downServo2(int total2) {
  Serial.println("Down");
  for (int angle = servo.read(); angle >= 0; angle -= 1) {
    servo.write(angle);
    delay(70);  // Delay for smooth movement
    int sensorValue2 = analogRead(irSensorPin2);
    total2 = (sensorValue2 / 1023.0) * 100;  // Convert to percentage correctly
    
  }
  // triggered2 = false;
}
void redLed() {
  int redLed = digitalRead(rLed);
  digitalWrite(redLed, HIGH);
}
void greenLed() {
  int greenLed = digitalRead(gLed);
  digitalWrite(greenLed, HIGH);
}

void sendNotificationToPython(const char* message) {
  EthernetClient client;
  if (client.connect("192.168.1.10", 5000)) {
    Serial.println("Connected to Python server");
    client.println("GET /general_notification");
    client.print(message);
    client.println(" HTTP/1.0\r\n");
    client.println("Host: 192.168.1.15\r\n");
    client.println("Connection: close\r\n\r\n");
    delay(100);  // Wait for the response
    client.stop();
  } else {
    Serial.println("Connection to Python server failed");
  }
}

void updateEntry(const char* message) {
  EthernetClient client;
  if (client.connect("192.168.1.10", 5000)) {
    Serial.println("Sending notification to Python server");
    client.println("POST /receive_plate HTTP/1.1");
    client.print("Content-Length: ");
    client.println(strlen(message));
    client.println("Content-Type: text/plain");
    client.println();
    client.println(message);
    delay(100);  // Wait for the response
    client.stop();
    Serial.println(message);
    Serial.println("Data sent successfully");
  } else {
    Serial.println("Not connected to server!!!");
    Serial.println(message);
  }
}

void updateOne(const char* message) {
  EthernetClient client;
  if (client.connect("192.168.1.10", 5000)) {
    Serial.println("Sending notification to Python server");
    client.println("POST /update_one HTTP/1.1");
    client.print("Content-Length: ");
    client.println(strlen(message));
    client.println("Content-Type: text/plain");
    client.println();
    client.println(message);
    delay(100);  // Wait for the response
    client.stop();
    Serial.println(message);
    Serial.println("Update ONE");
  } else {
    Serial.println("Not connected to server#$%!!!");
    Serial.println(message);
  }
}
void updateExit(const char* message) {
  EthernetClient client;
  if (client.connect("192.168.1.10", 5000)) {
    Serial.println("Sending notification to Python server");
    client.println("POST /update_exit HTTP/1.1");
    client.print("Content-Length: ");
    client.println(strlen(message));
    client.println("Content-Type: text/plain");
    client.println();
    client.println(message);
    delay(100);  // Wait for the response
    client.stop();
    Serial.println(message);
    Serial.println("Update Exit");
  } else {
    Serial.println("Not connected to server#$%!!!");
    Serial.println(message);
  }
}

void capture(const char* message) {
  EthernetClient client;
  if (client.connect("192.168.1.10", 5000)) {
    Serial.println("Sending notification to Python server");
    client.println("POST /capture HTTP/1.1");
    client.print("Content-Length: ");
    client.println(strlen(message));
    client.println("Content-Type: text/plain");
    client.println();
    client.println(message);
    delay(100);  // Wait for the response
    client.stop();
    Serial.println(message);
    Serial.println("Update Exit");
  } else {
    Serial.println("Not connected to server#$%!!!");
    Serial.println(message);
  }
}

void systemStart() {
  const char* next = "Starting...  ";
  while (*next) {

    Serial.print(*next);
    box.print(*next);
    delay(500);
    next++;
  }
  delay(500);
  dmd.clearScreen();
}
void slot() {

  // Clear the display by filling it with a blank space character
  dmd.drawChar(0, 0, ' ');
  // Display "Car 0/20" on the first 8 LEDs
  dmd.drawString(0, 0, "car");
  dmd.drawChar(19, 0, (char)(carSlot / 10) + '0');
  dmd.drawChar(24, 0, (char)(carSlot % 10) + '0');
  dmd.drawString(36, 0, "/20");
  // Clear the second line
  dmd.drawChar(0, 8, ' ');
  // Display "Motor 0/20" on the second 8 LEDs
  dmd.drawString(0, 8, "mtr");
  dmd.drawChar(19, 8, (char)(motorSlot / 10) + '0');
  dmd.drawChar(24, 8, (char)(motorSlot % 10) + '0');
  dmd.drawString(36, 8, "/20");
  // Update display
  dmd.scanDisplay();

  // Delay before updating again
  delay(500);
}

void intruder() {
  // Clear the display by filling it with a blank space character
  dmd.drawChar(0, 0, ' ');
  // Display "Car 0/20" on the first 8 LEDs
  dmd.drawString(0, 0, "Intru");
  // Clear the second line
  dmd.drawChar(0, 8, ' ');
  // Display "Motor 0/20" on the second 8 LEDs
  dmd.drawString(0, 8, "der!...");
  // Update display
  dmd.scanDisplay();

  // Delay before updating again
  delay(1000);
  dmd.clearScreen();
}

void welcome() {
  // Clear the display by filling it with a blank space character
  dmd.drawChar(0, 0, ' ');
  // Display "Car 0/20" on the first 8 LEDs
  dmd.drawString(0, 0, "Wel   ");
  // Clear the second line
  dmd.drawChar(0, 8, ' ');
  // Display "Motor 0/20" on the second 8 LEDs
  dmd.drawString(8, 8, "come");
  // Update display
  dmd.scanDisplay();
  // Delay before updating again
  //delay(500);
}



void setup() {

  Serial.begin(9600);
  pinMode(irSensorPin, INPUT);
  pinMode(irSensorPin2, INPUT);
  //pinMode(irSensorPin3, INPUT);
  //pinMode(irSensorPin4, INPUT);
  //pinMode(rLed,OUTPUT);
  //pinMode(gLed,OUTPUT);
  dmd.setBrightness(255);
  dmd.selectFont(SystemFont5x7);
  dmd.begin();
  servo.attach(38);
  servo.write(0);

  systemStart();
  downServo(total);
  //systemStart();
  Ethernet.begin(mac, ip);  // Initialize Ethernet with the given MAC and IP address
  server.begin();           // Start the server
  Serial.println("Server started at");
  Serial.println(Ethernet.localIP());
}


void loop() {
  int count = 0;
  int sensorValue = analogRead(irSensorPin);
  int sensorValue2 = analogRead(irSensorPin2);
  // int sensorValue3 = analogRead(irSensorPin3);
  // int sensorValue4 = analogRead(irSensorPin4);
  total = (sensorValue / 1023.0) * 100;    // Convert to percentage correctly
  total2 = (sensorValue2 / 1023.0) * 100;  // Convert to percentage correctly
  int data = 0;
  String plateNumber;
  String vehicle_type;
  
  EthernetClient client = server.available();  // Check for client connection
  // if (total >=40){
  //   Serial.print(total);
  // Serial.println(" Sensor 1");
  // }
  // if (total2 >=40){
  //   Serial.print(total2);
  // Serial.println(" Sensor 2");
  // }


  Serial.print(total);
  Serial.print(" Sensor 1");
  Serial.print("   ");
  Serial.print(total2);
  Serial.println(" sensor 2");
  // delay(100);
  // Serial.print("                                       ");
  // Serial.print(sensorValue3);
  // Serial.println(" sensor 3");
  // Serial.print("                                                            ");
  // Serial.print(sensorValue4);
  // Serial.println(" sensor 4");
  /*
          const float conversionFactor= 0.0048828125;
          float voltage = sensorValue * conversionFactor;
          float slope = 30.0;
          float intercept = 0.1;

          float distance = slope*voltage +intercept;

          Serial.print(distance);
          Serial.println(" inches");*/


  //slot();




  if (client) {
    triggered2 = false;
    Serial.println("Client connected");
    while (client.connected()) {                     // Continue loop while client is connected
      if (client.available()) {                      // Check if client has data available
        String data = client.readStringUntil('\n');  // Read the incoming data until newline character
        Serial.println("Received data: " + data);


        // Split the received data
        int firstCommaIndex = data.indexOf(',');
        String entry_or_exit = data.substring(0, firstCommaIndex);
        data = data.substring(firstCommaIndex + 1);  // Remove the first part (entry or exit)

        int secondCommaIndex = data.indexOf(',');
        String plateNumber = data.substring(0, secondCommaIndex);
        String vehicle_type = data.substring(secondCommaIndex + 1);
        Serial.println("Entry or Exit: " + entry_or_exit);
        Serial.println("Plate Number: " + plateNumber);
        Serial.println("Vehicle Type: " + vehicle_type);


        // Clear the buffer
        client.flush();
        //s***************************************************loop while connected**************************************************************************************************
        while (true) {
          sensorValue = analogRead(irSensorPin);
          sensorValue2 = analogRead(irSensorPin2);
          total = (sensorValue / 1023.0) * 100;    // Convert to percentage correctly
          total2 = (sensorValue2 / 1023.0) * 100;  // Convert to percentage correctly
          Serial.println("Stuck here");
          // sensorValue3 = analogRead(irSensorPin3);
          // sensorValue4 = analogRead(irSensorPin4);
          Serial.print(total);
          Serial.println(" Sensor 1");
          Serial.print("  ");
          Serial.print(sensorValue2);
          Serial.println(" sensor 2");
          // Serial.print("                                       ");
          // Serial.print(sensorValue3);
          // Serial.println(" sensor 3");
          // Serial.print("                                                            ");
          // Serial.print(sensorValue4);
          // Serial.println(" sensor 4");
          if (entry_or_exit == "exit") {
            updateExit(plateNumber.c_str());  //update database entry
            if (vehicle_type == "4wheels") {
              // if (carSlot < 20) {
              //   carSlot++;
              //   Serial.println("increase slot for motor");
              // }
            } else if (vehicle_type == "2wheels") {
              // if (motorSlot < 40) {
              //   motorSlot++;
              //   Serial.println("increase slot for car");
              // }
            }
          }

          // slot();
          // Check for specific commands
          if (data == "opengate") {
            welcome();
            upServo(total);

            break;  // Exit the inner loop when "closegate" command is received
          }
          if (data == "closegate") {
            downServo2(total);
            updateOne(plateNumber.c_str());  //update one in database
            break;                           // Exit the inner loop when "closegate" command is received
          }


          if (total >= 4) {  // open gate sensorValue >= 30 && sensorValue2 <= 50 && triggered2 == false && motorSlot != 0 && carSlot != 0
            while (true) {
              sensorValue = analogRead(irSensorPin);
              sensorValue2 = analogRead(irSensorPin2);
              total = (sensorValue / 1023.0) * 100;    // Convert to percentage correctly
              total2 = (sensorValue2 / 1023.0) * 100;  // Convert to percentage correctly

              Serial.println(plateNumber);
              welcome();
              triggered3 = false;
              if ((total >= 2 && triggered2 == false) || (total2 >= 7 && triggered2 == true)) {
                triggered2 = true;
                //continue;
                upServo(total);
                while (count < 5) {
                  int sensorValue2 = analogRead(irSensorPin2);
                  total2 = (sensorValue2 / 1023.0) * 100;  // Convert to percentage correctly
                  if (total2 >= 7) {
                    // Reset the counter if a new detection occurs while counting
                    count = 0;
                  }
                  count++;
                  Serial.println(count);
                  delay(1000);
                }
                // triggered3 = true;
              } else {
                count = 0;
                downServo(total2);
              }
              // if (total2 < 40 && triggered2 == false) {

              // }
              if (servo.read() == 0 ) {
                updateEntry(plateNumber.c_str());  //update database entry
                //capture(plateNumber.c_str());
                Serial.println("done here");
                triggered2 = true;
                triggered3 = false;
                client.stop();  // Close the connection
                Serial.println("Client disconnected'''''''////");
                break;
              }
            }

            //delay(2000);

            // if (total <= 45 && triggered3 == true) {
            //   upServo(total);
            // }

            // if (total <= 45 && triggered2 == true) {  // close gate and update database entry sensorValue <= 50 && sensorValue2 <= 50 && triggered2 == true
            //   triggered2 = false;
            //   updateEntry(plateNumber.c_str());  //update database entry
            //   capture(plateNumber.c_str());
            //   delay(1000);
            //   downServo(total);
            //   //sendNotificationToPython("arduino");
            //   // if (vehicle_type == "4wheels") {
            //   //   if (carSlot > 0) {
            //   //     carSlot--;
            //   //   }
            //   // } else if (vehicle_type == "2wheels") {
            //   //   if (motorSlot > 0) {
            //   //     motorSlot--;
            //   //   }
            //   // }
            //   break;
            // }
          }
          if (total <= 4 && triggered2 == true  ) {  //remain close the gate && update database one  sensorValue <= 20 && sensorValue2 <= 20 && triggered2 == false
            
            break;
          }
          if (total <= 4 && triggered2 == false ) {  //remain close the gate && update database one  sensorValue <= 20 && sensorValue2 <= 20 && triggered2 == false
            updateOne(plateNumber.c_str());          //update one in database
            Serial.println("update one hereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
            delay(200);
            break;
          }
          // if (sensorValue3 >= 300 && sensorValue4 <= 100) {  // exit
          //   triggered = true;
          //   if (vehicle_type == "4wheels") {
          //     if (motorSlot > 0) {
          //       motorSlot++;
          //     }
          //   } else if (vehicle_type == "2wheels") {
          //     if (carSlot > 0) {
          //       carSlot++;
          //     }
          //   }
          // }
          // if (sensorValue4 >= 300 && sensorValue3 <= 150) {  //intruder
          //   intruder();
          //   sendNotificationToPython("KURT KURT");
          // }
        }  //end while loop****************************************************************************************************************************
      }
    }
    Serial.println("Client disconnected");
  }  // ****************************************************************end if client


  // if (sensorValue3>=300 && sensorValue4<=150 && triggered==false){//intruder
  //   intruder();
  //   sendNotificationToPython("KURT KURT");

  // }
  // if (sensorValue4>=300 && sensorValue3<=150 && triggered==false) {//intruder
  //   intruder();
  //   sendNotificationToPython("KURT KURT");
  // }
  // Other logic for your system can go here
}
