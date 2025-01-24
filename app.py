
from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime, timedelta
import sqlite3
import secrets
import random
import string


app = Flask(__name__)

# Database setup
def initialize_database():
    conn = sqlite3.connect('coupons.db')
    cursor = conn.cursor()

    # Coupons table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS coupons (
                        code TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        valid_from TEXT NOT NULL,
                        valid_until TEXT NOT NULL,
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
            SELECT * FROM coupons WHERE code = ? AND used = FALSE
        ''', (code,)) 
        coupon = cursor.fetchone()

        if not coupon:
            return jsonify({'error': 'Invalid coupon'}), 404
        
        if coupon[4]: # 'used' = TRUE
            return jsonify({'error': 'Coupon already used'}), 400
        
        current_time = datetime.now().strftime('%I:%M %p')
        if current_time <= coupon[2] or current_time >= coupon[3]:
            return jsonify({'error': 'Coupon has expired'}), 400
        
        # Coupon is valid; mark it as used
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
    
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    conn = sqlite3.connect('coupons.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO coupons (code, type, valid_from, valid_until, used)
            VALUES (?, ?, ?, ?, FALSE)              
        ''', (code, data['type'], data['valid_from'], data['valid_until']))

        conn.commit()

        return jsonify({
            'code': code,
            'type': data['type'],
            'valid_from': data['valid_from'],
            'valid_until': data['valid_until']
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
def create_customer():
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
    

if __name__ == '__main__':
    app.run(debug=True)
