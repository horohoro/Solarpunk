/*
 * CurtainOpener_Test.ino
 * Basic Motor & Button Verification Test for ESP32 + 28BYJ-48 + ULN2003
 */

const int PIN_IN1 = 26;
const int PIN_IN2 = 25;
const int PIN_IN3 = 33;
const int PIN_IN4 = 32;
const int PIN_BUTTON = 27;

// 8-step half-stepping sequence for 28BYJ-48 (delivers maximum torque & smoothness)
const int stepSequence[8][4] = {
  {1, 0, 0, 0},
  {1, 1, 0, 0},
  {0, 1, 0, 0},
  {0, 1, 1, 0},
  {0, 0, 1, 0},
  {0, 0, 1, 1},
  {0, 0, 0, 1},
  {1, 0, 0, 1}
};

int stepIndex = 0;

void stopMotor() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
}

void rotateSteps(int totalSteps, bool clockwise, int stepDelayUs) {
  for (int s = 0; s < totalSteps; s++) {
    if (clockwise) {
      stepIndex++;
      if (stepIndex >= 8) stepIndex = 0;
    } else {
      stepIndex--;
      if (stepIndex < 0) stepIndex = 7;
    }
    digitalWrite(PIN_IN1, stepSequence[stepIndex][0]);
    digitalWrite(PIN_IN2, stepSequence[stepIndex][1]);
    digitalWrite(PIN_IN3, stepSequence[stepIndex][2]);
    digitalWrite(PIN_IN4, stepSequence[stepIndex][3]);
    delayMicroseconds(stepDelayUs);
  }
  stopMotor();
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n======================================");
  Serial.println("  Curtain Opener - Hardware Test v1.0 ");
  Serial.println("======================================");

  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  // Button configured with internal pullup (Pin 27 -> Button -> GND)
  pinMode(PIN_BUTTON, INPUT_PULLUP);

  stopMotor();

  Serial.println("Running self-test: Rotating 1 revolution FORWARD (clockwise)...");
  rotateSteps(4096, true, 1200); // 4096 half-steps = 1 full revolution (1200 us delay)
  delay(1000);

  Serial.println("Running self-test: Rotating 1 revolution BACKWARD (counter-clockwise)...");
  rotateSteps(4096, false, 1200);
  delay(500);

  Serial.println("\nSelf-test COMPLETE! Standing by.");
  Serial.println("-> Press the physical button to spin half a turn forward and backward!");
}

void loop() {
  // Button is active LOW
  if (digitalRead(PIN_BUTTON) == LOW) {
    delay(50); // Debounce
    if (digitalRead(PIN_BUTTON) == LOW) {
      Serial.println("\n[BUTTON PRESSED] Running half-revolution cycle...");
      rotateSteps(2048, true, 1200);
      delay(500);
      rotateSteps(2048, false, 1200);
      Serial.println("[CYCLE FINISHED] Waiting for button release.");
      
      while (digitalRead(PIN_BUTTON) == LOW) {
        delay(10);
      }
      delay(150); // Debounce release
    }
  }
  delay(20);
}
