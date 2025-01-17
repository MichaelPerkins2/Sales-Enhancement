
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
@app.route('/')
def index():
    return render_template('validator.html')

if __name__ == '__main__':
    app.run(debug=True)
