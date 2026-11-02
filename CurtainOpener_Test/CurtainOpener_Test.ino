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

bool rotateSteps(int totalSteps, bool clockwise, int stepDelayUs, bool interruptible = true) {
  static int lastBtn = HIGH;
  for (int s = 0; s < totalSteps; s++) {
    if (interruptible) {
      int btn = digitalRead(PIN_BUTTON);
      if (btn == LOW && lastBtn == HIGH) {
        delay(20);
        if (digitalRead(PIN_BUTTON) == LOW) {
          stopMotor();
          Serial.println("\n[STOP] Button pressed during motion! Motor halted immediately.");
          while (digitalRead(PIN_BUTTON) == LOW) {
            delay(10);
          }
          delay(100);
          lastBtn = HIGH;
          return false;
        }
      }
      lastBtn = btn;
    }

    if (clockwise) {
      stepIndex = (stepIndex + 1) % 8;
    } else {
      stepIndex = (stepIndex + 7) % 8;
    }
    digitalWrite(PIN_IN1, stepSequence[stepIndex][0]);
    digitalWrite(PIN_IN2, stepSequence[stepIndex][1]);
    digitalWrite(PIN_IN3, stepSequence[stepIndex][2]);
    digitalWrite(PIN_IN4, stepSequence[stepIndex][3]);
    delayMicroseconds(stepDelayUs);
  }
  stopMotor();
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n======================================");
  Serial.println("  Curtain Opener - Hardware Test v1.1 ");
  Serial.println("======================================");

  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  // Button configured with internal pullup (Pin 27 -> Button -> GND)
  pinMode(PIN_BUTTON, INPUT_PULLUP);

  stopMotor();

  Serial.println("Running self-test: Rotating 1 revolution FORWARD (clockwise)...");
  rotateSteps(4096, true, 1200, false); // Self-test at boot
  delay(1000);

  Serial.println("Running self-test: Rotating 1 revolution BACKWARD (counter-clockwise)...");
  rotateSteps(4096, false, 1200, false);
  delay(500);

  Serial.println("\nSelf-test COMPLETE! Standing by.");
  Serial.println("-> Press the physical button to start/stop the motor anytime!");
}

void loop() {
  // Non-blocking button edge detection
  static int lastSteadyButtonState = HIGH;
  static int lastFlickerableReading = HIGH;
  static unsigned long lastDebounceTime = 0;
  const unsigned long DEBOUNCE_DELAY_MS = 35;

  int currentReading = digitalRead(PIN_BUTTON);
  if (currentReading != lastFlickerableReading) {
    lastDebounceTime = millis();
    lastFlickerableReading = currentReading;
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
    if (currentReading != lastSteadyButtonState) {
      lastSteadyButtonState = currentReading;

      if (lastSteadyButtonState == LOW) {
        Serial.println("\n[BUTTON] Pressed -> Running test cycle (press again anytime to stop)...");
        if (rotateSteps(2048, true, 1200, true)) {
          delay(500);
          rotateSteps(2048, false, 1200, true);
        }
        Serial.println("[STANDBY] Standing by.");
      }
    }
  }
}
