
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime, timedelta
import sqlite3
import secrets
import random
import string
from flask_mail import Mail, Message


app = Flask(__name__)
mail = Mail(app)

# Flask Email Configuration
MAIL_USERNAME = 'michael.perkins.d@gmail.com'
MAIL_PASSWORD = 'Password'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

def send_coupon_email(recipient, coupon_code):
    msg = Message('Your Coupon Code',
                  sender=MAIL_USERNAME,
                  recipients=[recipient])
    msg.body = f'Here\'s your coupon code: {coupon_code}'
    mail.send(msg)

# Database setup
def initialize_database():
    conn = sqlite3.connect('coupons.db')
    cursor = conn.cursor()

    # Coupons table
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS coupons (
                        code TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        used BOOLEAN NOT NULL
                    )
                   ''')
    
    # Customers table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        phone TEXT,
                        opt_in BOOLEAN
                   )
                   ''')
    
    # Coupon type table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS coupon_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        description TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TEXT NOT NULL
                   )
                   ''')
    
    conn.commit()
    conn.close()

with app.app_context():
    initialize_database()


# Routes
@app.route('/')
def index():
    return redirect(url_for('validator'))

@app.route('/validator')
def validator():
    return render_template('validator.html')

@app.route('/api/coupons/validate/<code>', methods=['POST'])
def validate_coupon(code):
    
    data = request.get_json()

    conn = sqlite3.connect('coupons.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT * FROM coupons WHERE code = ?
        ''', (code,)) 
        coupon = cursor.fetchone()

        if not coupon:
            return jsonify({'error': 'Invalid coupon'}), 404
        
        if coupon[6]: # If 'used' = TRUE
            return jsonify({'error': 'This coupon has already been used'}), 400
        
        current_time = datetime.now().strftime('%H:%M:%S')
        current_date = datetime.now().strftime('%Y-%m-%d')
        print("Current time: " + current_time)
        print("Between: " + coupon[2] + " and " + coupon[3] + '? \n')

        print("Current date: " + current_date)
        print("Between: " + coupon[4] + " and " + coupon[5] + '? \n')

        # Check if current time and date are within coupon time and date range
        if not (coupon[4] <= current_date <= coupon[5]):      # If current date is outside coupon date range
            return jsonify({'error': 'Coupon has expired or is outside of the allotted timeframe'}), 400

        if not (coupon[2] <= current_time <= coupon[3]):      # If current time is outside coupon time range
            return jsonify({'error': 'Coupon has expired or is outside of the allotted timeframe'}), 400    
        
        # Otherwise, coupon is valid; mark it as used
        cursor.execute('''
            UPDATE coupons SET used = TRUE WHERE code = ?               
        ''', (data['code'],))

        conn.commit()

        return jsonify({
            'type': coupon[1]
        })

    except sqlite3.Error as e:
        print(e)
        return jsonify({'error': 'Error validating coupon'}), 500  
     
    finally:
        conn.close()    

@app.route('/generator')
def generator():
    return render_template('generator.html')

@app.route('/api/coupons/generate', methods=['POST'])
def generate_coupon():
    data = request.get_json()

    conn = sqlite3.connect('coupons.db')
    cursor = conn.cursor()

    try:
        # Delete expired coupons
        curr_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            DELETE FROM coupons WHERE end_date < ?
            ''', (curr_date,))

        # Generate new coupons
        cursor.execute('SELECT * FROM customers')
        rows = cursor.fetchall()

        for row in rows:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            name = row[1]
            email = row[2]
            phone = row[3]

            # Send coupon to customers via Email (TODO: SMS)
            send_coupon_email(email, code)

            # Insert coupon into database
            cursor.execute('''
                INSERT INTO coupons (code, type, start_time, end_time, start_date, end_date, used)
                VALUES (?, ?, ?, ?, ?, ?, FALSE)              
                            ''', (code, data['type'], data['start_time'], data['end_time'], data['start_date'], data['end_date']))



        # cursor.execute('''
        #     INSERT INTO coupons (code, type, start_time, end_time, start_date, end_date, used)
        #     VALUES (?, ?, ?, ?, ?, ?, FALSE)              
        # ''', (code, data['type'], data['start_time'], data['end_time'], data['start_date'], data['end_date']))

        conn.commit()

        return jsonify({
            'code': code,
            'type': data['type'],
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'start_date': data['start_date'],
            'end_date': data['end_date']
        }), 201
    
    except sqlite3.Error as e:
        print(e)
        return jsonify({'error': 'Error generating coupon'}), 500
    
    finally:
        conn.close()

@app.route('/customers')
def customers():
    return render_template('customers.html')

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.get_json()

    if not data or not data['name'] or not data['email']:
        return jsonify({'error': 'Invalid or missing customer data'}), 400
    
    conn = sqlite3.connect('coupons.db')
    cursor = conn.cursor()

    try: 
        cursor.execute('''
                       INSERT INTO customers (name, email, phone, opt_in) VALUES (?, ?, ?, ?)
                       ''', (data['name'], data['email'], data['phone'], data['opt_in']))
        conn.commit()
        return jsonify({'message': 'Customer created successfully'}), 201
    except sqlite3.Error as e:
        print(e)
        return jsonify({'error': 'Error creating customer'}), 500
    finally:
        conn.close()
    
@app.route('/api/coupon_types', methods=['POST'])
def add_coupon_type():
    data = request.get_json()
    description = data.get('description')

    if not description:
        return jsonify({'error': 'Invalid or missing coupon type data'}), 400
    
    conn = sqlite3.connect('coupons.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
                        INSERT INTO coupon_types (description, created_at) VALUES (?, ?)
                       ''', (description, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        return jsonify({'message': 'Coupon type created successfully'}), 201
    except sqlite3.Error as e:
        print(e)
        return jsonify({'error': 'Error creating coupon type'}), 500
    finally:
        conn.close()

@app.route('/api/coupon_types', methods=['GET'])
def get_coupon_types():
    conn = sqlite3.connect('coupons.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
                        SELECT * FROM coupon_types
                       ''')
        coupon_types = cursor.fetchall()
        return jsonify([{'description': row[1]} for row in coupon_types])
    except sqlite3.Error as e:
        print(e)
        return jsonify({'error': 'Error retrieving coupon types'}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
