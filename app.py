
from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime, timedelta
import sqlite3
import secrets

app = Flask(__name__)

# @app.route('/success/<name>')
# def success(name):
#     return 'Welcome %s!' % name

# @app.route('/login', methods=['POST', 'GET'])
# def login():
#     if request.method == 'POST':
#         user = request.form['nm']
#         return redirect(url_for('success', name=user))
#     else:
#         return render_template('login.html')

'''
Project code below:
'''

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

@app.route('/generate_coupon', methods=['POST'])
def generate_coupon():
    data = request.get_json()
    coupon_data = data['coupon_data']
    # TODO: Coupon generation logic
    return

if __name__ == '__main__':
    app.run(debug=True)
