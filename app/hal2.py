import gpiod
import time
from datetime import timedelta
from gpiod.line import Direction, Bias, Value, Edge
from gpiod import LineSettings

# --- Konfiguration ---
CHIP_NAME = "/dev/gpiochip0"
SENSOR_A_PIN = 2  # Sensor für "links"
SENSOR_B_PIN = 3  # Sensor für "rechts"

# !!! WICHTIG: Messen Sie den Abstand zwischen den Sensormittelpunkten in Metern !!!
SENSOR_DISTANCE_M = 0.05  # Beispiel: 5 cm = 0.05 Meter

# Timeout in Sekunden. Wenn nach dem ersten Sensor so lange nichts passiert,
# wird die Messung zurückgesetzt.
MEASUREMENT_TIMEOUT_S = 2.0

# --- Initialisierung ---
try:
    chip = gpiod.Chip(CHIP_NAME)
except Exception as e:
    print(f"Fehler beim Öffnen des GPIO-Chips '{CHIP_NAME}': {e}")
    print("Stellen Sie sicher, dass der Chip-Pfad korrekt ist und Sie die nötigen Berechtigungen haben (ggf. 'sudo' verwenden).")
    exit(1)

# Konfiguration für beide GPIO-Leitungen
settings = LineSettings(
    direction=Direction.INPUT,
    bias=Bias.PULL_UP,
    edge_detection=Edge.FALLING  # Löst aus, wenn der Magnet erkannt wird (Signal geht auf LOW)
)

# Leitungen anfordern
lines = gpiod.request_lines(
    path=CHIP_NAME,
    consumer="direction_speed_sensor",
    config={
        SENSOR_A_PIN: settings,
        SENSOR_B_PIN: settings
    }
)

# Variablen zur Speicherung des Zustands der Messung
first_event_pin = None
first_event_time_ns = 0

print("Sensor-Setup erfolgreich.")
print(f"Sensor A (links) an GPIO {SENSOR_A_PIN}, Sensor B (rechts) an GPIO {SENSOR_B_PIN}")
print(f"Gemessener Abstand: {SENSOR_DISTANCE_M * 100:.2f} cm")
print("Warte auf Bewegung des Magneten... (CTRL+C zum Beenden)")

try:
    while True:
        # Warten auf ein Edge-Event mit einem Timeout.
        # Dies ist besser als read_edge_events(), da es nicht ewig blockiert.
        if lines.wait_edge_events(timedelta(seconds=MEASUREMENT_TIMEOUT_S)):
            # Wenn ein Event aufgetreten ist, lies es aus
            events = lines.read_edge_events()
            
            for event in events:
                current_pin = event.line_offset
                current_time_ns = event.timestamp_ns
                
                # Prüfen, ob dies das ERSTE Event einer neuen Messung ist
                if first_event_pin is None:
                    first_event_pin = current_pin
                    first_event_time_ns = current_time_ns
                    print(f"Erster Kontakt an Sensor {'A' if current_pin == SENSOR_A_PIN else 'B'}...")
                
                # Prüfen, ob dies das ZWEITE Event ist und von einem ANDEREN Sensor kommt
                elif current_pin != first_event_pin:
                    # Zeitdifferenz in Sekunden berechnen
                    time_delta_ns = current_time_ns - first_event_time_ns
                    time_delta_s = time_delta_ns / 1_000_000_000.0

                    if time_delta_s == 0: continue # Ignoriere, falls die Zeitdifferenz 0 ist

                    # Geschwindigkeit berechnen (m/s)
                    speed_mps = SENSOR_DISTANCE_M / time_delta_s
                    speed_kmh = speed_mps * 3.6

                    # Richtung bestimmen
                    direction = "Unbekannt"
                    if first_event_pin == SENSOR_A_PIN and current_pin == SENSOR_B_PIN:
                        direction = "Links nach Rechts (A -> B)"
                    elif first_event_pin == SENSOR_B_PIN and current_pin == SENSOR_A_PIN:
                        direction = "Rechts nach Links (B -> A)"
                    
                    # Ergebnis ausgeben
                    print("-" * 30)
                    print(f"Richtung: {direction}")
                    print(f"Zeitdifferenz: {time_delta_s:.4f} s")
                    print(f"Geschwindigkeit: {speed_mps:.2f} m/s ({speed_kmh:.2f} km/h)")
                    print("-" * 30)

                    # Messung zurücksetzen für den nächsten Durchlauf
                    first_event_pin = None
                    first_event_time_ns = 0

        # Dieser Block wird ausgeführt, wenn wait_edge_events() einen Timeout hatte
        else:
            # Wenn wir auf ein zweites Event gewartet haben, aber keins kam,
            # setzen wir die Messung zurück.
            if first_event_pin is not None:
                print("Timeout! Messung wurde abgebrochen und zurückgesetzt.")
                first_event_pin = None
                first_event_time_ns = 0


except KeyboardInterrupt:
    print("\nProgramm wird beendet.")

finally:
    # Ressourcen sauber freigeben
    if 'lines' in locals() and lines:
        lines.release()
    if 'chip' in locals() and chip:
        chip.close()
    print("GPIO-Ressourcen freigegeben.")