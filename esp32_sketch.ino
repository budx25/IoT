/* esp32_sketch.ino
ESP32 sketch to read LDR and call /inference endpoint to get servo angle.
Adjust WIFI credentials and serverUrl before upload.
*/
#include <WiFi.h>
#include <HTTPClient.h>
#include <Servo.h>

const char* ssid = "YOUR_SSID";
const char* pass = "YOUR_PASS";
const char* serverUrl = "http://192.168.1.100:5000/inference"; // change to your server

Servo myservo;
int ldrPin = 34; // ADC1_CH6
int servoPin = 13;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, pass);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi connected");
  myservo.attach(servoPin);
}

void loop() {
  int ldrVal = analogRead(ldrPin); // 0..4095
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");
    String body = "{\"ldr\":" + String(ldrVal) + "}";
    int httpCode = http.POST(body);
    if (httpCode == 200) {
      String payload = http.getString();
      int idx = payload.indexOf("angle");
      if (idx >= 0) {
        int colon = payload.indexOf(":", idx);
        int endb = payload.indexOf("}", colon);
        String val = payload.substring(colon+1, endb);
        int angle = val.toInt();
        myservo.write(angle);
        Serial.printf("LDR=%d -> angle=%d\n", ldrVal, angle);
      }
    } else {
      // fallback rule: simple map
      int fallbackAngle = map(ldrVal, 0, 4095, 180, 0);
      myservo.write(fallbackAngle);
      Serial.printf("Fallback used: LDR=%d angle=%d (httpCode=%d)\n", ldrVal, fallbackAngle, httpCode);
    }
    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
  delay(300);
}
