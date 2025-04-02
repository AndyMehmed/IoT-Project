# email_handler.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_email_notification(subject, message, recipient="andy.mehmedovic@gmail.com"):
    sender_email = "test@test.com"
    password = "xxxx xxxx xxxx xxxx"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        print(f"E-post skickad: {subject}")
        return {"success": True, "message": "E-post skickad"}
    except Exception as e:
        print(f"Fel vid e-postskickning: {e}")
        return {"success": False, "message": str(e)}
    finally:
        server.quit()

def generate_email_content(sensor_data, current_color):
    message = (
        f"Smart Home Control Data:\n\n"
        f"Temperature: {sensor_data['temperature']}\u00b0C\n"
        f"Humidity: {sensor_data['humidity']}%\n"
        f"Light Level: {sensor_data['lightSensor']}\n"
        f"Light Condition: {sensor_data['lightCondition']}\n"
        f"Servo Status: {'Open' if sensor_data['servo'] > 90 else 'Closed'}\n"
        f"Active LED: {sensor_data['activeLED']}\n"
        f"NeoPixel Color: #{current_color}\n"
    )
    return message

def send_light_change_email(previous, current, recipient="andy.mehmedovic@gmail.com"):
    subject = "Förändring i ljusförhållanden"
    message = f"Ljusförhållandena har ändrats från {previous} till {current} vid {datetime.now()}."
    status = send_email_notification(subject, message, recipient)
    if status["success"]:
        print("E-post om ljusförändring skickad.")
    else:
        print(f"Fel vid e-post om ljusförändring: {status['message']}")
