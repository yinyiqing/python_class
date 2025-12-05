import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from modules.analytics import Analytics
from modules.auth import Auth
from modules.config import Config
from modules.customers import Customers
from modules.database import Database
from modules.departments import Departments
from modules.employee import Employee
from modules.orders import Orders
from modules.rooms import Rooms
from modules.security import Security
from modules.weather import Weather

app = Flask(__name__)
app.secret_key = os.urandom(24)

config_manager = Config()
db = Database()
security_manager = Security()

analytics_manager = Analytics(db)
auth_manager = Auth()
customer_manager = Customers(db)
department_manager = Departments(db)
employee_manager = Employee(db)
orders_manager = Orders(db)
room_manager = Rooms(db)
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

@app.route('/rooms')
def rooms():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('rooms.html', username=session.get('username'))

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

# 订单管理API路由
@app.route('/api/orders', methods=['GET'])
def api_get_orders():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        payment_status = request.args.get('payment_status', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        # 调用 orders_manager 获取订单
        # 由于 orders_manager 目前没有分页功能，先获取所有订单
        result = orders_manager.get_all_orders()

        if result['success']:
            orders_data = result['data']

            # 应用筛选
            filtered_orders = orders_data

            if search:
                search_lower = search.lower()
                filtered_orders = [
                    order for order in filtered_orders
                    if (search_lower in order.get('order_id', '').lower() or
                        search_lower in order.get('customer_name', '').lower() or
                        search_lower in order.get('room_number', '').lower() or
                        search_lower in order.get('customer_phone', '').lower())
                ]

            if status:
                filtered_orders = [
                    order for order in filtered_orders
                    if order.get('order_status') == status
                ]

            if payment_status:
                filtered_orders = [
                    order for order in filtered_orders
                    if order.get('payment_status') == payment_status
                ]

            if start_date:
                filtered_orders = [
                    order for order in filtered_orders
                    if order.get('check_in_date') >= start_date
                ]

            if end_date:
                filtered_orders = [
                    order for order in filtered_orders
                    if order.get('check_out_date') <= end_date
                ]

            # 简单分页（每次10条）
            page_size = 10
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paged_orders = filtered_orders[start_idx:end_idx]

            return jsonify({
                'success': True,
                'data': paged_orders,
                'total': len(filtered_orders),
                'page': page,
                'page_size': page_size,
                'message': f'获取到{len(paged_orders)}个订单'
            })
        else:
            return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取订单列表失败: {str(e)}'
        })

@app.route('/api/orders/<order_id>', methods=['GET'])
def api_get_order(order_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = orders_manager.get_order(order_id)
    return jsonify(result)

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        data = request.json
        result = orders_manager.create_order(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建订单失败: {str(e)}'
        })

@app.route('/api/orders/<order_id>', methods=['PUT'])
def api_update_order(order_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        data = request.json
        result = orders_manager.update_order(order_id, data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新订单失败: {str(e)}'
        })

@app.route('/api/orders/<order_id>', methods=['DELETE'])
def api_delete_order(order_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = orders_manager.delete_order(order_id)
    return jsonify(result)

@app.route('/api/orders/statistics', methods=['GET'])
def api_get_order_statistics():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        statistics = orders_manager.get_order_statistics()
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

@app.route('/api/orders/check-availability', methods=['GET'])
def api_check_room_availability():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        room_number = request.args.get('room_number')
        check_in = request.args.get('check_in')
        check_out = request.args.get('check_out')
        exclude_order_id = request.args.get('exclude_order_id', '')

        if not all([room_number, check_in, check_out]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            })

        result = orders_manager.check_room_availability(
            room_number, check_in, check_out, exclude_order_id
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查房间可用性失败: {str(e)}'
        })

@app.route('/api/orders/<order_id>/payment', methods=['POST'])
def api_process_payment(order_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        data = request.json
        payment_amount = data.get('payment_amount', 0)

        if payment_amount <= 0:
            return jsonify({
                'success': False,
                'message': '支付金额必须大于0'
            })

        result = orders_manager.calculate_payment(order_id, payment_amount)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'支付处理失败: {str(e)}'
        })

@app.route('/api/orders/export', methods=['GET'])
def api_export_orders():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        # 获取筛选参数（与获取订单列表相同）
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        payment_status = request.args.get('payment_status', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        # 获取所有订单
        result = orders_manager.get_all_orders()

        if not result['success']:
            return jsonify(result)

        orders_data = result['data']

        # 应用筛选
        filtered_orders = orders_data

        if search:
            search_lower = search.lower()
            filtered_orders = [
                order for order in filtered_orders
                if (search_lower in order.get('order_id', '').lower() or
                    search_lower in order.get('customer_name', '').lower() or
                    search_lower in order.get('room_number', '').lower() or
                    search_lower in order.get('customer_phone', '').lower())
            ]

        if status:
            filtered_orders = [
                order for order in filtered_orders
                if order.get('order_status') == status
            ]

        if payment_status:
            filtered_orders = [
                order for order in filtered_orders
                if order.get('payment_status') == payment_status
            ]

        if start_date:
            filtered_orders = [
                order for order in filtered_orders
                if order.get('check_in_date') >= start_date
            ]

        if end_date:
            filtered_orders = [
                order for order in filtered_orders
                if order.get('check_out_date') <= end_date
            ]

        # 返回筛选后的数据
        return jsonify({
            'success': True,
            'data': filtered_orders,
            'message': f'导出{len(filtered_orders)}条订单数据'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'导出订单失败: {str(e)}'
        })

@app.route('/analytics')
def analytics():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('analytics.html', username=session.get('username'))

@app.route('/api/analytics/dashboard', methods=['GET'])
def api_get_dashboard():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = analytics_manager.get_dashboard_summary()
    return jsonify(result)

@app.route('/api/analytics/employees', methods=['GET'])
def api_get_employee_stats():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = analytics_manager.get_employee_statistics()
    return jsonify(result)

@app.route('/api/analytics/orders', methods=['GET'])
def api_get_order_stats():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = analytics_manager.get_order_statistics()
    return jsonify(result)

@app.route('/api/analytics/customers', methods=['GET'])
def api_get_customer_stats():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = analytics_manager.get_customer_statistics()
    return jsonify(result)

@app.route('/api/analytics/rooms', methods=['GET'])
def api_get_room_stats():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = analytics_manager.get_room_statistics()
    return jsonify(result)

@app.route('/api/analytics/revenue', methods=['GET'])
def api_get_revenue_analysis():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = analytics_manager.get_revenue_analysis(start_date, end_date)
    return jsonify(result)

@app.route('/api/analytics/chart', methods=['GET'])
def api_generate_chart():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    chart_type = request.args.get('type', '')
    if not chart_type:
        return jsonify({'success': False, 'message': '图表类型不能为空'}), 400

    # 解析额外参数
    params = {}
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    result = analytics_manager.generate_chart_data(chart_type, params)
    return jsonify(result)

@app.route('/api/analytics/export', methods=['GET'])
def api_export_stats():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    export_type = request.args.get('type', 'json')

    result = analytics_manager.export_statistics(export_type)
    return jsonify(result)

@app.route('/api/analytics/report', methods=['GET'])
def api_get_full_report():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 获取所有统计数据
    dashboard_result = analytics_manager.get_dashboard_summary()

    if not dashboard_result['success']:
        return jsonify(dashboard_result)

    # 生成报告
    report = {
        'success': True,
        'data': dashboard_result['data'],
        'charts': {
            'employee_dept': analytics_manager.generate_chart_data('employee_dept'),
            'order_status': analytics_manager.generate_chart_data('order_status'),
            'room_type': analytics_manager.generate_chart_data('room_type'),
            'revenue_trend': analytics_manager.generate_chart_data('revenue_trend')
        },
        'message': '综合报告生成完成'
    }

    return jsonify(report)

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