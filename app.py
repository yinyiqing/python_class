import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from modules.auth import Auth
from modules.config import Config
from modules.weather import Weather

app = Flask(__name__)
app.secret_key = os.urandom(24)

config_manager = Config()

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

@app.route('/change-password', methods=['POST'])
def change_password():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    current_password = request.form.get('currentPassword')
    new_password = request.form.get('newPassword')
    confirm_password = request.form.get('confirmPassword')

    # 验证参数
    if not all([current_password, new_password, confirm_password]):
        return jsonify({'success': False, 'message': '请填写所有字段'})

    # 验证新密码和确认密码是否匹配
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': '新密码和确认密码不匹配'})

    # 更新密码
    success, message = auth_manager.update_password(current_password, new_password)
    return jsonify({'success': success, 'message': message})

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
        return redirect(url_for('login'))
    return render_template('customers.html', username=session.get('username'))

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

    # 检查是否是配置请求
    if request.args.get('action') == 'get_config':
        # 返回当前配置
        config = weather_service.get_weather_config()
        return jsonify(config)

    # 检查是否是保存配置请求
    if request.args.get('action') == 'save_config':
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': '请先登录'}), 401

        api_host = request.args.get('api_host', '').strip()
        api_key = request.args.get('api_key', '').strip()

        if not api_host or not api_key:
            return jsonify({'success': False, 'message': 'API主机名和密钥不能为空'})

        if not api_host.endswith('.re.qweatherapi.com'):
            return jsonify({'success': False, 'message': 'API主机名格式不正确'})

        success = weather_service.update_weather_config(api_host, api_key)

        if success:
            return jsonify({'success': True, 'message': '配置更新成功'})
        else:
            return jsonify({'success': False, 'message': '配置更新失败'})

    # 正常的天气查询
    weather_data = weather_service.get_weather_data(city, 7)
    if weather_data:
        return jsonify(weather_data)
    else:
        return jsonify({'error': '天气数据获取失败'})

if __name__ == '__main__':
    app.run(port=5000, debug=True)