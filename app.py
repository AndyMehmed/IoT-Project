# app.py
from flask import Flask, jsonify, request, render_template
import serial
import threading
import json
from datetime import datetime
import schedule
import time
from email_handler import send_email_notification, generate_email_content, send_light_change_email

app = Flask(__name__)

# Seriell kommunikation
try:
    arduino = serial.Serial('/dev/cu.usbmodem14101', 9600, timeout=1)
    print("Ansluten till Arduino ")
except serial.SerialException as e:
    print(f"Kan inte ansluta till Arduino: {e}")
    arduino = None

# Globala variabler
sensor_data = {
    "temperature": "N/A",
    "humidity": "N/A",
    "lightSensor": "N/A",
    "lightCondition": "N/A",
    "activeLED": "N/A",
    "servo": 90
}
temp_threshold = 30  # Tröskelvärde för temperatur
light_threshold = 400  # Tröskelvärde för ljusnivå

previous_light_condition = None  # Tidigare ljusförhållande
current_color = "FFFFFF"  # Standardfärg: vit

temperature_readings = []  # För att lagra temperaturvärden för beräkning av genomsnitt

# Läs kontinuerligt från Arduino
def read_from_arduino():
    global sensor_data, previous_light_condition
    while arduino and arduino.is_open:
        try:
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()
                if line.startswith("{") and line.endswith("}"):
                    parsed_data = json.loads(line)
                    sensor_data.update(parsed_data)

                    # Uppdatera ljusförhållanden
                    current_light_condition = (
                        "Bright" if int(parsed_data.get("lightSensor", 0)) >= light_threshold else "Dark"
                    )
                    sensor_data["lightCondition"] = current_light_condition

                    # Kontrollera förändringar i ljusförhållanden
                    if previous_light_condition and previous_light_condition != current_light_condition:
                        send_light_change_email(previous_light_condition, current_light_condition)

                        # Öppna servo om ljusförhållandet ändras från "Dark" till "Bright"
                        if previous_light_condition == "Dark" and current_light_condition == "Bright":
                            control_servo_angle(180)  # Öppna servon
                        elif previous_light_condition == "Bright" and current_light_condition == "Dark":
                            control_servo_angle(0)  # Stäng servon

                    previous_light_condition = current_light_condition
                else:
                    print("Meddelande från Arduino:", line)
        except json.JSONDecodeError:
            print("Felaktig JSON-data från Arduino:", line)
        except Exception as e:
            print(f"Fel vid läsning från Arduino: {e}")

def control_servo_angle(angle):
    global arduino, sensor_data
    if not arduino or not arduino.is_open:
        print("Arduino är inte ansluten.")
        return

    try:
        # Begränsa vinkeln mellan 0 och 180 grader
        angle = max(0, min(180, int(angle)))

        command = f"SERVO:{angle}\n"
        arduino.write(command.encode())
        sensor_data['servo'] = angle  # Uppdatera sensordata
        print(f"Servo vinkel inställd till {angle}")
    except Exception as e:
        print(f"Fel vid kontroll av servo: {e}")

# Hantera regnbågseffekt
@app.route('/neopixel/rainbow', methods=['POST'])
def set_rainbow_effect():
    global arduino
    if not arduino or not arduino.is_open:
        return jsonify({"error": "Arduino is not connected"}), 500

    try:
        data = request.json
        delay = int(data.get('delay', 20))  # Standardfördröjning: 20 ms
        delay = max(0, min(delay, 100))  # Begränsa fördröjning mellan 0 och 100 ms
        command = f"RAINBOW:{delay}\n"
        arduino.write(command.encode())
        return jsonify({"message": f"Rainbow effect started with delay {delay} ms"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Hantera färgcykling
@app.route('/neopixel/cycle', methods=['POST'])
def set_color_cycle():
    global arduino
    if not arduino or not arduino.is_open:
        return jsonify({"error": "Arduino is not connected"}), 500

    try:
        data = request.json
        delay = int(data.get('delay', 50))  # Standardfördröjning: 50 ms
        delay = max(0, min(delay, 100))  # Begränsa fördröjning mellan 0 och 100 ms
        command = f"CYCLE:{delay}\n"
        arduino.write(command.encode())
        return jsonify({"message": f"Color cycle effect started with delay {delay} ms"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update-notifications', methods=['POST'])
def update_notifications():
    global temp_threshold
    try:
        data = request.json
        temp_threshold = int(data.get('tempThreshold', temp_threshold))
        return jsonify({"message": f"Notifications updated. Temperature Threshold: {temp_threshold}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Hantera NeoPixel-ljusstyrka
@app.route('/neopixel/brightness', methods=['POST'])
def set_brightness():
    global arduino
    if not arduino or not arduino.is_open:
        return jsonify({"error": "Arduino is not connected"}), 500

    try:
        data = request.json
        brightness = int(data.get('brightness', 128))  # Standardljusstyrka: 128 (0-255)
        brightness = max(0, min(brightness, 255))  # Begränsa värde mellan 0 och 255
        command = f"BRIGHTNESS:{brightness}\n"
        arduino.write(command.encode())
        return jsonify({"message": f"Brightness set to {brightness}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Hantera NeoPixel-färger
@app.route('/neopixel/color', methods=['POST'])
def set_color():
    global arduino, current_color
    if not arduino or not arduino.is_open:
        return jsonify({"error": "Arduino is not connected"}), 500

    try:
        data = request.json
        color = data.get('color', 'FFFFFF')  # Standardfärg: vit
        command = f"COLOR:{color}\n"
        arduino.write(command.encode())
        current_color = color
        return jsonify({"message": f"Color set to #{color}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Hantera Servo
@app.route('/servo', methods=['POST'])
def control_servo():
    global arduino
    if not arduino or not arduino.is_open:
        return jsonify({"error": "Arduino is not connected"}), 500

    try:
        angle = request.json.get('angle')
        if angle is None:
            return jsonify({"error": "Angle is required"}), 400

        # Begränsa vinkeln mellan 0 och 180 grader
        angle = max(0, min(180, int(angle)))

        command = f"SERVO:{angle}\n"
        arduino.write(command.encode())
        sensor_data['servo'] = angle  # Uppdatera sensordata
        return jsonify({"message": f"Servo vinkel inställd till {angle}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API-rutter
@app.route('/sensor-data')
def get_sensor_data():
    return jsonify(sensor_data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update-temp-threshold', methods=['POST'])
def update_temp_threshold():
    global temp_threshold, sensor_data, current_color
    try:
        data = request.json
        email = data.get('email')
        temp_threshold = int(data.get('tempThreshold', temp_threshold))
        
        # Generera e-postinnehåll
        message = generate_email_content(sensor_data, current_color)
        subject = "Aktuella sensordata från Smart Home Control"
        
        # Skicka e-post
        email_status = send_email_notification(subject, message, email)
        if email_status["success"]:
            return jsonify({"message": f"Temperature threshold updated and email sent to {email}"}), 200
        else:
            return jsonify({"error": email_status["message"]}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Starta trådar
if arduino:
    thread_arduino = threading.Thread(target=read_from_arduino)
    thread_arduino.daemon = True
    thread_arduino.start()

thread_schedule = threading.Thread(target=lambda: schedule.run_pending() or time.sleep(1))
thread_schedule.daemon = True
thread_schedule.start()

if __name__ == '__main__':
    try:
        app.run(debug=False, host='0.0.0.0', port=5001)  # Byt port till 5001
    except OSError as e:
        if "Address already in use" in str(e):
            print("Porten är redan upptagen. Kontrollera om en annan process använder den eller välj en annan port.")
        else:
            print(f"Fel vid serverstart: {e}")
    except KeyboardInterrupt:
        print("\nServer avslutad av användaren.")
    except Exception as e:
        print(f"Fel vid serverstart: {e}")
