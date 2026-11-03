/*
 * CurtainOpener.ino
 * Complete Smart Curtain System for ESP32
 * Features:
 *  - Dual-band Wi-Fi connection
 *  - Automatic Japan Standard Time (NTP) sync
 *  - Mobile Web Dashboard (set wake-up time, trigger open, tune distance)
 *  - Flash storage (Preferences): Settings survive power cuts & reboots
 *  - Non-blocking stepper motion with automatic slack release
 *  - Physical wardrobe push-button integration
 *  - mDNS: access via http://curtain.local
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <ArduinoOTA.h>
#include <Update.h>
#include <time.h>

// --- Wi-Fi Configuration ---
// If secrets.h exists, it will load your private credentials.
// Otherwise, define your credentials here or copy secrets.h.example -> secrets.h
#if __has_include("secrets.h")
  #include "secrets.h"
#else
  const char* WIFI_SSID     = "YOUR_WIFI_SSID";
  const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
#endif

// --- Pin Definitions ---
const int PIN_IN1    = 26;
const int PIN_IN2    = 25;
const int PIN_IN3    = 33;
const int PIN_IN4    = 32;
const int PIN_BUTTON = 27;

// --- 8-Step Half-Stepping Sequence ---
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

// --- Motor & State Machine Variables ---
enum MotorState {
  STATE_IDLE,
  STATE_OPENING,
  STATE_PAUSE,
  STATE_RELEASING
};

MotorState motorState = STATE_IDLE;
int stepIndex = 0;
long currentStep = 0;
long targetSteps = 0;
unsigned long lastStepMicros = 0;
unsigned long pauseStartMs = 0;
const int STEP_DELAY_US = 1200; // Microseconds per half-step (~15 RPM)

// --- User Settings (Saved in Flash) ---
Preferences prefs;
int alarmHour = 7;
int alarmMinute = 0;
bool alarmEnabled = true;
int curtainRevolutions = 12; // 12 revs ≈ 0.75m (avoids fabric packing stall)
int lastTriggeredDay = -1;
int lastTriggeredHour = -1;
int lastTriggeredMinute = -1;

WebServer server(80);

void stopMotor() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
}

void stepMotor(bool forward) {
  if (forward) {
    stepIndex = (stepIndex + 1) % 8;
  } else {
    stepIndex = (stepIndex + 7) % 8;
  }
  digitalWrite(PIN_IN1, stepSequence[stepIndex][0]);
  digitalWrite(PIN_IN2, stepSequence[stepIndex][1]);
  digitalWrite(PIN_IN3, stepSequence[stepIndex][2]);
  digitalWrite(PIN_IN4, stepSequence[stepIndex][3]);
}

void startCurtainCycle() {
  if (motorState != STATE_IDLE) return;
  targetSteps = (long)curtainRevolutions * 4096L;
  currentStep = 0;
  motorState = STATE_OPENING;
  lastStepMicros = micros();
  Serial.printf("[ACTION] Curtain cycle STARTED. Moving %d revolutions (%ld steps)...\n", curtainRevolutions, targetSteps);
}

void cancelCurtainCycle() {
  motorState = STATE_IDLE;
  currentStep = 0;
  stopMotor();
  Serial.println("[ACTION] Curtain cycle STOPPED by user.");
}

// --- HTML Dashboard ---
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart Curtain</title>
<style>
  :root { --primary: #ff9800; --bg: #121820; --card: #1e2632; --text: #e6edf3; --muted: #8b949e; --green: #2ea043; }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: var(--bg); color: var(--text); display: flex; justify-content: center; padding: 20px 12px; min-height: 100vh; }
  .app { width: 100%; max-width: 440px; }
  .header { text-align: center; margin-bottom: 24px; }
  .header h1 { font-size: 24px; color: var(--primary); display: flex; align-items: center; justify-content: center; gap: 8px; }
  .clock { font-size: 42px; font-weight: 700; margin: 12px 0 4px; letter-spacing: 1px; }
  .date { color: var(--muted); font-size: 14px; }
  .card { background: var(--card); border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.3); }
  .card h2 { font-size: 16px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }
  .status-badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
  .status-idle { background: rgba(46,160,67,0.2); color: #3fb950; }
  .status-busy { background: rgba(255,152,0,0.2); color: var(--primary); animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
  .form-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .form-row label { font-size: 15px; }
  .time-input { background: #121820; border: 1px solid #30363d; color: var(--text); font-size: 20px; font-weight: 600; padding: 8px 12px; border-radius: 8px; }
  .num-input { background: #121820; border: 1px solid #30363d; color: var(--text); font-size: 16px; width: 70px; padding: 8px; border-radius: 8px; text-align: center; }
  .switch { position: relative; display: inline-block; width: 50px; height: 28px; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #30363d; transition: .3s; border-radius: 28px; }
  .slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 4px; bottom: 4px; background-color: white; transition: .3s; border-radius: 50%; }
  input:checked + .slider { background-color: var(--primary); }
  input:checked + .slider:before { transform: translateX(22px); }
  .btn-main { width: 100%; padding: 16px; border: none; border-radius: 12px; font-size: 18px; font-weight: 700; cursor: pointer; transition: 0.2s; background: linear-gradient(135deg, #ff9800, #f57c00); color: #121820; margin-bottom: 8px; }
  .btn-main:active { transform: scale(0.98); }
  .btn-secondary { width: 100%; padding: 12px; border: 1px solid #30363d; border-radius: 12px; font-size: 15px; font-weight: 600; background: transparent; color: var(--muted); cursor: pointer; }
  .btn-stop { background: #da3633; color: white; border: none; }
  .btn-save { width: 100%; padding: 12px; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; background: #238636; color: white; cursor: pointer; }
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <h1>☀️ Smart Curtain</h1>
    <div class="clock" id="clock">--:--:--</div>
    <div class="date" id="date">Connecting...</div>
  </div>

  <div class="card">
    <h2>Status <span class="status-badge status-idle" id="badge">IDLE</span></h2>
    <div id="status-desc" style="color:var(--muted); font-size:14px; margin-bottom:16px;">Curtain is standing by.</div>
    <button class="btn-main" id="btn-action" onclick="triggerOpen()">🌅 OPEN CURTAIN NOW</button>
  </div>

  <div class="card">
    <h2>Wake-up Alarm</h2>
    <div class="form-row">
      <label>Alarm Enabled</label>
      <label class="switch">
        <input type="checkbox" id="alarm-en" onchange="saveSettings()">
        <span class="slider"></span>
      </label>
    </div>
    <div class="form-row">
      <label>Wake-up Time (JST)</label>
      <input type="time" class="time-input" id="alarm-time" onchange="saveSettings()">
    </div>
    <div class="form-row" style="margin-bottom:0;">
      <label>Curtain Distance (Revs)<br><span style="font-size:12px; color:var(--muted);">12 revs ≈ 0.75m (pull & unwind)</span></label>
      <input type="number" class="num-input" id="rotations" min="1" max="40" onchange="saveSettings()">
    </div>
  </div>
</div>

<script>
function updateStatus() {
  fetch('/api/status')
    .then(r => r.json())
    .then(d => {
      document.getElementById('clock').innerText = d.time;
      document.getElementById('date').innerText = d.date;
      const b = document.getElementById('badge');
      const desc = document.getElementById('status-desc');
      const act = document.getElementById('btn-action');
      if (d.state === "IDLE") {
        b.className = "status-badge status-idle";
        b.innerText = "IDLE";
        desc.innerText = d.alarm_en ? `Alarm set for ${d.alarm_time}` : "Alarm is disabled";
        act.innerText = "🌅 OPEN CURTAIN NOW";
        act.className = "btn-main";
        act.onclick = triggerOpen;
      } else {
        b.className = "status-badge status-busy";
        b.innerText = d.state;
        desc.innerText = d.state === "OPENING" ? "Opening curtain..." : (d.state === "PAUSE" ? "Curtain open. Preparing slack..." : "Releasing string slack...");
        act.innerText = "🛑 STOP MOTOR";
        act.className = "btn-main btn-stop";
        act.onclick = triggerStop;
      }
      if (!window.loadedSettings) {
        document.getElementById('alarm-en').checked = d.alarm_en;
        document.getElementById('alarm-time').value = d.alarm_time;
        document.getElementById('rotations').value = d.rotations;
        window.loadedSettings = true;
      }
    });
}
function triggerOpen() { fetch('/api/open', {method:'POST'}); }
function triggerStop() { fetch('/api/stop', {method:'POST'}); }
function saveSettings() {
  const en = document.getElementById('alarm-en').checked;
  const time = document.getElementById('alarm-time').value;
  const rot = document.getElementById('rotations').value;
  fetch(`/api/settings?en=${en}&time=${time}&rot=${rot}`, {method:'POST'});
}
setInterval(updateStatus, 1000);
updateStatus();
</script>
</body>
</html>
)rawliteral";

void handleRoot() {
  server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  server.sendHeader("Pragma", "no-cache");
  server.sendHeader("Expires", "-1");
  server.send(200, "text/html", INDEX_HTML);
}

void handleStatus() {
  struct tm timeinfo;
  char timeStr[16] = "--:--:--";
  char dateStr[32] = "NTP Syncing...";
  if (getLocalTime(&timeinfo, 50)) {
    strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);
    strftime(dateStr, sizeof(dateStr), "%A, %b %d", &timeinfo);
  }

  char alarmStr[8];
  snprintf(alarmStr, sizeof(alarmStr), "%02d:%02d", alarmHour, alarmMinute);

  String stateStr = "IDLE";
  if (motorState == STATE_OPENING) stateStr = "OPENING";
  else if (motorState == STATE_PAUSE) stateStr = "PAUSE";
  else if (motorState == STATE_RELEASING) stateStr = "RELEASING";

  String json = "{";
  json += "\"time\":\"" + String(timeStr) + "\",";
  json += "\"date\":\"" + String(dateStr) + "\",";
  json += "\"state\":\"" + stateStr + "\",";
  json += "\"alarm_en\":" + String(alarmEnabled ? "true" : "false") + ",";
  json += "\"alarm_time\":\"" + String(alarmStr) + "\",";
  json += "\"rotations\":" + String(curtainRevolutions);
  json += "}";

  server.send(200, "application/json", json);
}

void handleOpen() {
  startCurtainCycle();
  server.send(200, "text/plain", "OK");
}

void handleStop() {
  cancelCurtainCycle();
  server.send(200, "text/plain", "OK");
}

void handleSettings() {
  bool alarmChanged = false;
  if (server.hasArg("en")) {
    bool en = (server.arg("en") == "true");
    if (en != alarmEnabled) {
      alarmEnabled = en;
      alarmChanged = true;
    }
  }
  if (server.hasArg("time")) {
    String t = server.arg("time");
    int colon = t.indexOf(':');
    if (colon > 0) {
      int h = t.substring(0, colon).toInt();
      int m = t.substring(colon + 1).toInt();
      if (h != alarmHour || m != alarmMinute) {
        alarmHour = h;
        alarmMinute = m;
        alarmChanged = true;
      }
    }
  }
  if (server.hasArg("rot")) {
    int r = server.arg("rot").toInt();
    if (r >= 1 && r <= 50) {
      curtainRevolutions = r;
    }
  }

  // Re-arm trigger whenever alarm time or state is modified
  if (alarmChanged) {
    lastTriggeredDay = -1;
    lastTriggeredHour = -1;
    lastTriggeredMinute = -1;
  }

  prefs.putInt("hour", alarmHour);
  prefs.putInt("min", alarmMinute);
  prefs.putBool("en", alarmEnabled);
  prefs.putInt("revs", curtainRevolutions);

  Serial.printf("[SETTINGS SAVED] Alarm: %02d:%02d (Enabled: %d), Revs: %d\n",
                alarmHour, alarmMinute, alarmEnabled, curtainRevolutions);
  server.send(200, "text/plain", "OK");
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n===========================================");
  Serial.println("  Smart Curtain Controller v2.0 (ESP32)   ");
  Serial.println("===========================================");

  // Pin setup
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  stopMotor();

  // Load preferences from flash
  prefs.begin("curtain", false);
  alarmHour = prefs.getInt("hour", 7);
  alarmMinute = prefs.getInt("min", 0);
  alarmEnabled = prefs.getBool("en", true);
  curtainRevolutions = prefs.getInt("revs", 12);
  Serial.printf("[INIT] Loaded settings -> Alarm: %02d:%02d, Enabled: %d, Revs: %d\n",
                alarmHour, alarmMinute, alarmEnabled, curtainRevolutions);

  // Connect to Wi-Fi
  Serial.printf("[WIFI] Connecting to '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] CONNECTED!");
    Serial.printf("[WIFI] IP Address: http://%s\n", WiFi.localIP().toString().c_str());

    // Start mDNS: http://curtain.local
    if (MDNS.begin("curtain")) {
      Serial.println("[MDNS] Web dashboard ready at: http://curtain.local");
    }

    // Sync NTP Time (Japan Standard Time = UTC + 9 hours)
    configTime(9 * 3600, 0, "ntp.nict.jp", "pool.ntp.org", "time.google.com");
    Serial.println("[TIME] Synchronizing with Japan Atomic Time (NTP)...");

    // Configure Over-The-Air (OTA) Wireless Updates
    ArduinoOTA.setHostname("curtain");
    ArduinoOTA.onStart([]() {
      stopMotor();
      Serial.println("[OTA] Wireless firmware update starting...");
    });
    ArduinoOTA.onEnd([]() {
      Serial.println("\n[OTA] Update complete! Rebooting...");
    });
    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
      Serial.printf("[OTA] Progress: %u%%\r", (progress / (total / 100)));
    });
    ArduinoOTA.onError([](ota_error_t error) {
      Serial.printf("[OTA] Error[%u]\n", error);
    });
    ArduinoOTA.begin();
    Serial.println("[OTA] Wireless flashing enabled! Ready for Wi-Fi updates.");
  } else {
    Serial.println("\n[WIFI] FAILED to connect. Check 2.4GHz network name. Operating in offline/button mode.");
  }

  // Web routes
  server.on("/", handleRoot);
  server.on("/api/status", handleStatus);
  server.on("/api/open", HTTP_POST, handleOpen);
  server.on("/api/stop", HTTP_POST, handleStop);
  server.on("/api/settings", HTTP_POST, handleSettings);

  // Browser-based Wireless Firmware Update Route (/update)
  server.on("/update", HTTP_GET, []() {
    server.send(200, "text/html",
      "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>"
      "<title>Wireless Update</title>"
      "<style>body{background:#121820;color:#e6edf3;font-family:sans-serif;padding:30px 15px;text-align:center;}"
      ".box{max-width:400px;margin:0 auto;background:#1e2632;padding:25px;border-radius:16px;box-shadow:0 4px 16px rgba(0,0,0,0.3);}"
      "h2{color:#ff9800;margin-bottom:15px;}"
      "input[type=file]{margin:15px 0;color:#8b949e;}"
      "input[type=submit]{background:#2ea043;color:white;border:none;padding:12px 24px;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;}"
      "</style></head><body>"
      "<div class='box'><h2>Wireless Firmware Update</h2>"
      "<p style='color:#8b949e;font-size:14px;margin-bottom:15px;'>Select compiled .bin file to flash wirelessly:</p>"
      "<form method='POST' action='/update' enctype='multipart/form-data'>"
      "<input type='file' name='update' accept='.bin'><br>"
      "<input type='submit' value='Upload & Flash Wireless'>"
      "</form></div></body></html>");
  });
  server.on("/update", HTTP_POST, []() {
    server.sendHeader("Connection", "close");
    server.send(200, "text/plain", (Update.hasError()) ? "UPDATE FAILED" : "UPDATE SUCCESS! Rebooting...");
    ESP.restart();
  }, []() {
    HTTPUpload& upload = server.upload();
    if (upload.status == UPLOAD_FILE_START) {
      stopMotor();
      Serial.printf("[OTA Web] Flashing: %s\n", upload.filename.c_str());
      if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
        Update.printError(Serial);
      }
    } else if (upload.status == UPLOAD_FILE_WRITE) {
      if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
        Update.printError(Serial);
      }
    } else if (upload.status == UPLOAD_FILE_END) {
      if (Update.end(true)) {
        Serial.printf("[OTA Web] Success: %u bytes\n", upload.totalSize);
      } else {
        Update.printError(Serial);
      }
    }
  });

  server.begin();
  Serial.println("[SYSTEM] Ready! Startup complete (motor remains idle until triggered).");
}

void loop() {
  server.handleClient();
  ArduinoOTA.handle();

  // 1. Check Physical Button (Active LOW) with non-blocking edge latch
  // Behavior: Idle -> Press -> Running. Running -> Press -> Idle (immediate stop).
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

      // Trigger ONCE strictly on button PRESS (falling edge: HIGH -> LOW)
      if (lastSteadyButtonState == LOW) {
        if (motorState == STATE_IDLE) {
          Serial.println("[BUTTON] Press detected -> Starting curtain cycle!");
          startCurtainCycle();
        } else {
          Serial.println("[BUTTON] Press detected while running -> STOPPING IMMEDIATELY!");
          cancelCurtainCycle();
        }
      }
    }
  }

  // 2. Check Scheduled Morning Alarm (Every 10 seconds)
  static unsigned long lastTimeCheck = 0;
  if (millis() - lastTimeCheck >= 10000) {
    lastTimeCheck = millis();
    struct tm timeinfo;
    if (getLocalTime(&timeinfo, 50)) {
      if (alarmEnabled && motorState == STATE_IDLE) {
        if (timeinfo.tm_hour == alarmHour && timeinfo.tm_min == alarmMinute) {
          bool alreadyFired = (timeinfo.tm_mday == lastTriggeredDay &&
                               timeinfo.tm_hour == lastTriggeredHour &&
                               timeinfo.tm_min == lastTriggeredMinute);
          if (!alreadyFired) {
            lastTriggeredDay = timeinfo.tm_mday;
            lastTriggeredHour = timeinfo.tm_hour;
            lastTriggeredMinute = timeinfo.tm_min;
            Serial.printf("[ALARM] Scheduled alarm matched (%02d:%02d JST)! Opening curtain...\n", alarmHour, alarmMinute);
            startCurtainCycle();
          }
        }
      }
    }
  }

  // 3. Non-blocking Motor State Machine
  if (motorState == STATE_OPENING) {
    if (micros() - lastStepMicros >= STEP_DELAY_US) {
      lastStepMicros = micros();
      stepMotor(true); // Pull curtain open
      currentStep++;
      if (currentStep >= targetSteps) {
        currentStep = 0;
        motorState = STATE_PAUSE;
        pauseStartMs = millis();
        stopMotor();
        Serial.printf("[CYCLE] Curtain fully open (%d revs). Pausing 2s before unwinding...\n", curtainRevolutions);
      }
    }
  } else if (motorState == STATE_PAUSE) {
    if (millis() - pauseStartMs >= 2000) {
      motorState = STATE_RELEASING;
      currentStep = 0;
      lastStepMicros = micros();
      Serial.printf("[CYCLE] Unwinding exactly %d revs (zero net drift)...\n", curtainRevolutions);
    }
  } else if (motorState == STATE_RELEASING) {
    if (micros() - lastStepMicros >= STEP_DELAY_US) {
      lastStepMicros = micros();
      stepMotor(false); // Rotate reverse to give slack
      currentStep++;
      if (currentStep >= targetSteps) {
        cancelCurtainCycle();
        Serial.println("[CYCLE] Completed! Symmetrical unwind finished. Zero drift.");
      }
    }
  }
}
