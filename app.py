
from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime, timedelta
import sqlite3
import secrets
import random
import string

app = Flask(__name__)

# Routes
@app.route('/validator')
def validator():
    return render_template('validator.html')

@app.route('/validate_coupon', methods=['POST'])
def validate_coupon():
    data = request.get_json()
    coupon_code = data['coupon_code']
    # TODO: Coupon validation logic
    return

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
            INERT INTO coupons (code, type, valid_from, valid_until, used)
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

if __name__ == '__main__':
    app.run(debug=True)
