# modules/customers.py
from datetime import datetime


class Customers:
    def __init__(self, db):
        self.db = db
        # [核心修复] 初始化类时，自动执行建表操作
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        """如果 customers 表不存在，则自动创建它"""
        sql = '''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                id_card TEXT NOT NULL,
                created_at TEXT
            )
        '''
        try:
            # 尝试执行建表语句
            # 注意：这里调用的是 db.execute_update，确保你的 Database 类支持执行 CREATE 语句
            self.db.execute_update(sql)
            print("系统自检：客户表检查完毕（已存在或已创建）。")
        except Exception as e:
            print(f"系统自检警告：初始化客户表失败: {str(e)}")

    def create_customer(self, input_data: dict) -> dict:
        try:
            # 1. 验证必填字段
            if not input_data.get('name'):
                return {'success': False, 'message': '客户姓名不能为空'}
            if not input_data.get('phone'):
                return {'success': False, 'message': '手机号不能为空'}
            if not input_data.get('id_card'):
                return {'success': False, 'message': '身份证号不能为空'}

            # 2. 检查手机号或身份证是否重复
            if self.check_exists(input_data['phone'], input_data['id_card']):
                return {'success': False, 'message': '该手机号或身份证号已存在'}

            # 3. 准备数据
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            sql = '''
                INSERT INTO customers (name, phone, id_card, created_at)
                VALUES (?, ?, ?, ?)
            '''

            params = (
                input_data['name'].strip(),
                input_data['phone'].strip(),
                input_data['id_card'].strip(),
                created_at
            )

            # 4. 执行插入
            customer_id = self.db.execute_update(sql, params)

            if customer_id is not None:
                return {'success': True, 'message': '客户添加成功'}
            else:
                return {'success': False, 'message': '添加失败，数据库操作未返回ID'}

        except Exception as e:
            # 如果此时还是报错 no such table，说明建表函数没有成功执行
            return {'success': False, 'message': f'创建客户失败: {str(e)}'}

    def update_customer(self, customer_id: str, input_data: dict) -> dict:
        try:
            # 验证是否存在
            if not self.get_customer_by_id(customer_id):
                return {'success': False, 'message': '客户不存在'}

            # 构建更新语句
            set_fields = []
            params = []

            if input_data.get('name'):
                set_fields.append("name = ?")
                params.append(input_data['name'].strip())

            if input_data.get('phone'):
                set_fields.append("phone = ?")
                params.append(input_data['phone'].strip())

            if input_data.get('id_card'):
                set_fields.append("id_card = ?")
                params.append(input_data['id_card'].strip())

            if not set_fields:
                return {'success': False, 'message': '没有检测到需要修改的数据'}

            params.append(customer_id)
            sql = f"UPDATE customers SET {', '.join(set_fields)} WHERE id = ?"

            result = self.db.execute_update(sql, tuple(params))

            if result is not None:
                return {'success': True, 'message': '客户信息更新成功'}
            else:
                return {'success': False, 'message': '更新失败'}

        except Exception as e:
            return {'success': False, 'message': f'更新客户失败: {str(e)}'}

    def delete_customer(self, customer_id: str) -> dict:
        try:
            sql = "DELETE FROM customers WHERE id = ?"
            result = self.db.execute_update(sql, (customer_id,))

            if result is not None and result > 0:
                return {'success': True, 'message': '客户删除成功'}
            else:
                return {'success': False, 'message': '删除失败或客户不存在'}
        except Exception as e:
            return {'success': False, 'message': f'删除客户失败: {str(e)}'}

    def get_all_customers(self) -> dict:
        try:
            sql = "SELECT * FROM customers ORDER BY created_at DESC"
            customers = self.db.execute_query(sql)
            # 防止数据库返回 None 导致报错
            customers = customers if customers else []
            return {
                'success': True,
                'data': customers,
                'message': f'获取到 {len(customers)} 位客户'
            }
        except Exception as e:
            return {'success': False, 'message': f'获取列表失败: {str(e)}'}

    def get_customer_by_id(self, customer_id: str) -> dict:
        try:
            sql = "SELECT * FROM customers WHERE id = ?"
            result = self.db.execute_query(sql, (customer_id,))
            if result:
                return {'success': True, 'data': result[0]}
            else:
                return {'success': False, 'message': '未找到该客户'}
        except Exception as e:
            return {'success': False, 'message': f'获取详情失败: {str(e)}'}

    def search_customers(self, keyword: str) -> dict:
        try:
            keyword = f"%{keyword}%"
            sql = "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? OR id_card LIKE ?"
            customers = self.db.execute_query(sql, (keyword, keyword, keyword))

            customers = customers if customers else []
            return {
                'success': True,
                'data': customers
            }
        except Exception as e:
            return {'success': False, 'message': f'搜索失败: {str(e)}'}

    def check_exists(self, phone, id_card):
        """检查是否存在重复数据"""
        try:
            sql = "SELECT COUNT(*) as count FROM customers WHERE phone = ? OR id_card = ?"
            result = self.db.execute_query(sql, (phone, id_card))
            return result[0]['count'] > 0 if result else False
        except:
            return False