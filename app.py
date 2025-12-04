import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from modules.auth import Auth
from modules.config import Config
from modules.database import Database
from modules.departments import Departments
from modules.employee import Employee
# [新增] 导入客户模块
from modules.customers import Customers
from modules.weather import Weather
from modules.rooms import Rooms

app = Flask(__name__)
app.secret_key = os.urandom(24)

config_manager = Config()
db = Database()
security_manager = Security()

room_manager = Rooms(db)     # [新增]
auth_manager = Auth()
department_manager = Departments(db)
employee_manager = Employee(db)
# [新增] 初始化客户管理器
customer_manager = Customers(db)
weather_service = Weather()


@app.route('/')
def login():
    is_valid, corrupted_files = security_manager.verify_integrity()
    if not is_valid:
        return render_template('security.html', corrupted_files=corrupted_files)
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


# 部门管理路由
@app.route('/api/department/list', methods=['GET'])
def api_get_departments():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = department_manager.get_all_departments()  # 改为调用 department_manager
    return jsonify(result)


@app.route('/api/department/create', methods=['POST'])
def api_create_department():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.json
    success, message = department_manager.create_department(data)  # 改为调用 department_manager
    return jsonify({'success': success, 'message': message})


@app.route('/api/department/update/<department_id>', methods=['PUT'])
def api_update_department(department_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.json
    success, message = department_manager.update_department(department_id, data)  # 改为调用 department_manager
    return jsonify({'success': success, 'message': message})


@app.route('/api/department/delete/<department_id>', methods=['DELETE'])
def api_delete_department(department_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    success, message = department_manager.delete_department(department_id)  # 改为调用 department_manager
    return jsonify({'success': success, 'message': message})


# 员工管理路由
@app.route('/api/employee/create', methods=['POST'])
def api_create_employee():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.json
    result = employee_manager.create_employee(data)
    return jsonify(result)


@app.route('/api/employee/list', methods=['GET'])
def api_get_employees():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 这里可以添加过滤参数，目前先返回所有员工
    result = employee_manager.get_all_employees()
    return jsonify(result)


@app.route('/api/employee/<employee_id>', methods=['GET'])
def api_get_employee(employee_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = employee_manager.get_employee(employee_id)
    return jsonify(result)


@app.route('/api/employee/update/<employee_id>', methods=['PUT'])
def api_update_employee(employee_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.json
    result = employee_manager.update_employee(employee_id, data)
    return jsonify(result)


@app.route('/api/employee/delete/<employee_id>', methods=['DELETE'])
def api_delete_employee(employee_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = employee_manager.delete_employee(employee_id)
    return jsonify(result)


# 员工相关统计信息
@app.route('/api/employee/statistics', methods=['GET'])
def api_get_employee_statistics():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        statistics = employee_manager.get_employee_statistics()
        return jsonify({
            'success': True,
            'data': statistics,
            'message': '统计信息获取成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        })


# ==========================================
# [新增] 客户管理 API 路由 (Customer Routes)
# ==========================================

@app.route('/api/customer/list', methods=['GET'])
def api_get_customers():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 调用 Customers 类的 get_all_customers 方法
    result = customer_manager.get_all_customers()
    return jsonify(result)


@app.route('/api/customer/<customer_id>', methods=['GET'])
def api_get_customer(customer_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 调用 customer_manager 获取单个客户详情
    result = customer_manager.get_customer_by_id(customer_id)
    return jsonify(result)


@app.route('/api/customer/create', methods=['POST'])
def api_create_customer():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.json
    result = customer_manager.create_customer(data)
    return jsonify(result)


@app.route('/api/customer/update/<customer_id>', methods=['PUT'])
def api_update_customer(customer_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.json
    result = customer_manager.update_customer(customer_id, data)
    return jsonify(result)


@app.route('/api/customer/delete/<customer_id>', methods=['DELETE'])
def api_delete_customer(customer_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = customer_manager.delete_customer(customer_id)
    return jsonify(result)


@app.route('/api/customer/search', methods=['GET'])
def api_search_customers():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    keyword = request.args.get('keyword', '')
    result = customer_manager.search_customers(keyword)
    return jsonify(result)


# ==========================================
# 结束客户管理 API 路由
# ==========================================

@app.route('/rooms')
def rooms():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('rooms.html', username=session.get('username'))

# ==========================================
# [新增] 客房管理 API 路由
# ==========================================

@app.route('/api/rooms/list', methods=['GET'])
def api_get_rooms():
    if not session.get('logged_in'): return jsonify({'success': False}), 401
    return jsonify(room_manager.get_all_rooms())

@app.route('/api/rooms/add', methods=['POST'])
def api_add_room():
    if not session.get('logged_in'): return jsonify({'success': False}), 401
    return jsonify(room_manager.add_room(request.json))

@app.route('/api/rooms/update/<room_number>', methods=['PUT'])
def api_update_room(room_number):
    if not session.get('logged_in'): return jsonify({'success': False}), 401
    return jsonify(room_manager.update_room(room_number, request.json))

@app.route('/api/rooms/delete/<room_number>', methods=['DELETE'])
def api_delete_room(room_number):
    if not session.get('logged_in'): return jsonify({'success': False}), 401
    return jsonify(room_manager.delete_room(room_number))

@app.route('/api/rooms/status', methods=['POST'])
def api_room_status():
    if not session.get('logged_in'): return jsonify({'success': False}), 401
    # data: { room_number: "101", action: "checkin" }
    return jsonify(room_manager.update_status(request.json.get('room_number'), request.json.get('action')))

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


@app.route('/theme')
def theme():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('theme.html', username=session.get('username'))


if __name__ == '__main__':
    app.run(port=5000, debug=True)