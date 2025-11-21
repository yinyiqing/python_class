import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from module.auth import Auth
from module.weather import Weather

app = Flask(__name__)
app.secret_key = os.urandom(24)
auth_manager = Auth()
weather_service = Weather()

@app.route('/')
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if auth_manager.verify_admin(username, password):
        session['logged_in'] = True
        session['username'] = username
        return jsonify({'success': True, 'message': '登录成功'})
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login') + '?logout=true')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/employees')
def employees():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('employees.html', username=session.get('username'))

@app.route('/rooms')
def rooms():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('rooms.html', username=session.get('username'))

@app.route('/customers')
def customers():
    if not session.get('logged_in'):
        return redirect(url_for('login'), username=session.get('username'))
    return render_template('customers.html')

@app.route('/orders')
def orders():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('orders.html', username=session.get('username'))

@app.route('/analytics')
def analytics():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('analytics.html', username=session.get('username'))

@app.route('/weather')
def weather():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('weather.html', username=session.get('username'))

@app.route('/api/weather')
def get_weather():
    city = request.args.get('city', '北京')
    weather_data = weather_service.get_weather_data(city, 7)
    return jsonify(weather_data)

if __name__ == '__main__':
    app.run(port=5000, debug=True)