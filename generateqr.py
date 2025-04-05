from flask import Flask, render_template, request, send_file, jsonify
import qrcode
import time
import os
import sqlite3

app = Flask(__name__)

# Global variables to store QR code data and expiration
current_qr_data = None
qr_expiration_time = None
QR_LIFETIME = 900  # 15 minutes in seconds

# Function to generate QR code
def generate_qr_code():
    global current_qr_data, qr_expiration_time
    # Unique data for QR code (timestamp-based)
    current_qr_data = f"Attendance_{int(time.time())}"
    qr = qrcode.make(current_qr_data)
    qr_path = "static/qr.png"  # Save in 'static' folder for web access
    qr.save(qr_path)
    qr_expiration_time = time.time() + QR_LIFETIME  # Set expiration
    return qr_path

# Route for the main page
@app.route('/')
def index():
    qr_path = generate_qr_code()  # Generate initial QR code
    return render_template('index.html', qr_path=qr_path, expired=False)

# Route to generate a new QR code
@app.route('/generate', methods=['POST'])
def generate_new_qr():
    qr_path = generate_qr_code()
    return render_template('index.html', qr_path=qr_path, expired=False)

# Route to check QR code validity (for scanning logic later)
@app.route('/check_qr')
def check_qr():
    if current_qr_data and time.time() < qr_expiration_time:
        time_left = int(qr_expiration_time - time.time())
        return {"valid": True, "data": current_qr_data, "time_left": time_left}
    else:
        return {"valid": False, "data": None, "time_left": 0}

if __name__ == '__main__':
    # Create 'static' folder if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)





    # Initialize database
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    # Create students table (for simplicity, just ID and Name)
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id TEXT PRIMARY KEY, name TEXT)''')
    # Create attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (student_id TEXT, qr_data TEXT, timestamp REAL, 
                  FOREIGN KEY(student_id) REFERENCES students(id))''')
    conn.commit()
    conn.close()

# Call this when the app starts
if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    init_db()  # Initialize DB
    app.run(host='0.0.0.0', port=5000, debug=True)





    # Add this after your existing routes
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    qr_data = data.get('qr_data')
    student_id = data.get('student_id')

    # Check if QR is valid
    if qr_data != current_qr_data or time.time() > qr_expiration_time:
        return jsonify({"success": False, "message": "Invalid or expired QR code!"})

    # Connect to database
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    # Check if student exists (for simplicity, add if not found)
    c.execute("INSERT OR IGNORE INTO students (id, name) VALUES (?, ?)", (student_id, f"Student_{student_id}"))
    
    # Check if already marked for this QR
    c.execute("SELECT * FROM attendance WHERE student_id = ? AND qr_data = ?", (student_id, qr_data))
    if c.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Attendance already marked!"})

    # Mark attendance
    c.execute("INSERT INTO attendance (student_id, qr_data, timestamp) VALUES (?, ?, ?)",
              (student_id, qr_data, time.time()))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Attendance marked successfully!"})

# Update the index route to include a scan link
@app.route('/')
def index():
    qr_path = generate_qr_code()
    return render_template('index.html', qr_path=qr_path, expired=False)

# Add scan page route
@app.route('/scan')
def scan():
    return render_template('scan.html')
