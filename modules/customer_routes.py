from flask import Blueprint, request, jsonify, session
from modules.database import Database
from modules.customers import Customers
import sqlite3

# 定义蓝图
customer_bp = Blueprint('customer', __name__)

# 初始化数据库和管理器
# 注意：在实际 Flask 应用中，建议使用 current_app 或 g 对象，
# 但为了保持与你现有 app.py 结构一致（在文件顶部初始化），我们在这里创建实例
db = Database()
customer_manager = Customers(db)


def init_customer_module(db_path):
    """
    初始化客户模块数据库表
    被 app.py 调用
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            id_card TEXT NOT NULL,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


# 1. 获取客户列表
@customer_bp.route('/api/customer/list', methods=['GET'])
def api_get_customers():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = customer_manager.get_all_customers()
    return jsonify(result)


# 2. 搜索客户
@customer_bp.route('/api/customer/search', methods=['GET'])
def api_search_customers():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return api_get_customers()

    result = customer_manager.search_customers(keyword)
    return jsonify(result)


# 3. 获取单个客户详情
@customer_bp.route('/api/customer/<customer_id>', methods=['GET'])
def api_get_customer(customer_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = customer_manager.get_customer_by_id(customer_id)
    return jsonify(result)


# 4. 创建客户
@customer_bp.route('/api/customer/create', methods=['POST'])
def api_create_customer():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.json
    result = customer_manager.create_customer(data)
    return jsonify(result)


# 5. 更新客户
@customer_bp.route('/api/customer/update/<customer_id>', methods=['PUT'])
def api_update_customer(customer_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    data = request.json
    result = customer_manager.update_customer(customer_id, data)
    return jsonify(result)


# 6. 删除客户
@customer_bp.route('/api/customer/delete/<customer_id>', methods=['DELETE'])
def api_delete_customer(customer_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': '请先登录'}), 401

    result = customer_manager.delete_customer(customer_id)
    return jsonify(result)