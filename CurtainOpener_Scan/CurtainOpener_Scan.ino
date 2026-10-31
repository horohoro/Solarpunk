#include <WiFi.h>

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n--- Scanning 2.4GHz Wi-Fi Networks ---");
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);

  int n = WiFi.scanNetworks();
  Serial.printf("Found %d networks:\n", n);
  for (int i = 0; i < n; ++i) {
    Serial.printf("%2d: %-32s (%d dBm) %s\n", i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i), (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "Open" : "Encrypted");
    delay(10);
  }
  Serial.println("--- Scan Complete ---");
}

void loop() {
  delay(10000);
}
