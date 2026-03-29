import cv2
from pyzbar.pyzbar import decode
from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
import time
import mysql.connector
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================= LCD =================
lcd = CharLCD('PCF8574', 0x27)  # change to 0x3F if needed

# ================= GPIO =================
ISSUE_PIN = 17
RETURN_PIN = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(ISSUE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RETURN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ================= CAMERA =================
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# ================= DATABASE =================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",  # 🔧 CHANGE
    database="library_db"
)
cursor = db.cursor()

# ================= EMAIL =================
EMAIL_USER = "your_email@gmail.com"     # 🔧 CHANGE
EMAIL_PASS = "your_app_password"        # 🔧 CHANGE

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(EMAIL_USER, EMAIL_PASS)

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    server.sendmail(EMAIL_USER, to_email, msg.as_string())

# ================= SCANNER =================
def scan_barcode(message, expected_type):
    lcd.clear()
    lcd.write_string(message)

    start = time.time()
    last = None

    while time.time() - start < 15:
        ret, frame = cap.read()
        if not ret:
            continue

        for barcode in decode(frame):
            data = barcode.data.decode('utf-8')

            if data == last:
                continue
            last = data

            if expected_type == "BOOK" and data.startswith("B"):
                return data
            elif expected_type == "USER" and data.startswith("U"):
                return data
            else:
                lcd.clear()
                lcd.write_string("Wrong ID")
                time.sleep(1)

    return None

# ================= DATABASE =================
def get_book(book_id):
    cursor.execute("SELECT * FROM bookdatabase WHERE uid=%s", (book_id,))
    return cursor.fetchone()

def get_user(user_id):
    cursor.execute("SELECT * FROM usersdatabase WHERE lid=%s", (user_id,))
    return cursor.fetchone()

# ================= MAIN LOOP =================
try:
    while True:
        lcd.clear()
        lcd.write_string("Place Hand...")
        time.sleep(1)

        # Detect mode
        if GPIO.input(ISSUE_PIN) == 0:
            mode = "ISSUE"
        elif GPIO.input(RETURN_PIN) == 0:
            mode = "RETURN"
        else:
            continue

        lcd.clear()
        lcd.write_string(mode + " MODE")
        time.sleep(2)

        # -------- Scan Book --------
        book_id = scan_barcode("Scan Book", "BOOK")
        if not book_id:
            lcd.clear()
            lcd.write_string("No Book")
            time.sleep(2)
            continue

        book = get_book(book_id)
        if not book:
            lcd.clear()
            lcd.write_string("Book Not Found")
            time.sleep(2)
            continue

        # -------- Scan User --------
        user_id = scan_barcode("Scan User", "USER")
        if not user_id:
            lcd.clear()
            lcd.write_string("No User")
            time.sleep(2)
            continue

        user = get_user(user_id)
        if not user:
            lcd.clear()
            lcd.write_string("User Not Found")
            time.sleep(2)
            continue

        user_email = user[2]

        # ================= ISSUE =================
        if mode == "ISSUE":
            if book[2] == 0:
                lcd.clear()
                lcd.write_string("Already Issued")
                time.sleep(2)
                continue

            issue_date = datetime.now()
            return_date = issue_date + timedelta(days=7)

            cursor.execute(
                "UPDATE bookdatabase SET available=0, issuedto=%s, issuedate=%s, returndate=%s WHERE uid=%s",
                (user_id, issue_date, return_date, book_id)
            )
            db.commit()

            send_email(
                user_email,
                "Book Issued",
                f"Book {book_id} issued.\nReturn before {return_date}"
            )

            lcd.clear()
            lcd.write_string("Issued")

        # ================= RETURN =================
        else:
            if book[2] == 1:
                lcd.clear()
                lcd.write_string("Not Issued")
                time.sleep(2)
                continue

            return_date = book[5]
            now = datetime.now()

            fine = 0
            if return_date and now > return_date:
                fine = 50

            cursor.execute(
                "UPDATE bookdatabase SET available=1, issuedto=NULL, issuedate=NULL, returndate=NULL WHERE uid=%s",
                (book_id,)
            )
            db.commit()

            if fine > 0:
                send_email(
                    user_email,
                    "Late Return",
                    f"Book {book_id} returned late.\nFine: Rs.{fine}"
                )
                lcd.clear()
                lcd.write_string(f"Fine Rs.{fine}")
            else:
                send_email(
                    user_email,
                    "Returned",
                    f"Book {book_id} returned successfully"
                )
                lcd.clear()
                lcd.write_string("Returned")

        time.sleep(3)

except KeyboardInterrupt:
    GPIO.cleanup()
    lcd.clear()
    cap.release()
    cv2.destroyAllWindows()
    cursor.close()
    db.close()
    server.quit()