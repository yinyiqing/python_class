from flask import Flask, request, jsonify, render_template
from weather import Weather

app = Flask(__name__)
weather_service = Weather()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/employees')
def employees():
    return render_template('employees.html')

@app.route('/rooms')
def rooms():
    return render_template('rooms.html')

@app.route('/customers')
def customers():
    return render_template('customers.html')

@app.route('/orders')
def orders():
    return render_template('orders.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/weather')
def weather():
    return render_template('weather.html')

@app.route('/api/weather')
def get_weather():
    city = request.args.get('city', '北京')
    weather_data = weather_service.get_weather_data(city, 7)
    return jsonify(weather_data)

if __name__ == '__main__':
    app.run(port=5000, debug=True)