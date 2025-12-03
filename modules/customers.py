# modules/customers.py
from datetime import datetime


class Customers:
    def __init__(self, db):
        self.db = db
        self.create_table_if_not_exists()
        # [新增] 每次启动程序时，自动修复断层的 ID，确保从 1 开始
        self.reorder_all_ids()

    def create_table_if_not_exists(self):
        """初始化表结构"""
        sql = '''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY, 
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                id_card TEXT NOT NULL,
                created_at TEXT
            )
        '''
        try:
            self.db.execute_update(sql)
        except Exception as e:
            print(f"系统自检警告：初始化客户表失败: {str(e)}")

    def reorder_all_ids(self):
        """
        [核心修复逻辑]
        强制重排整个客户表的所有 ID，使其变成连续的 1, 2, 3...
        例如：数据库里有 ID [2, 5, 8]，执行后会变成 [1, 2, 3]
        """
        try:
            # 1. 获取所有客户，按当前 ID 从小到大排序
            sql_get_all = "SELECT id FROM customers ORDER BY id ASC"
            rows = self.db.execute_query(sql_get_all)

            if not rows:
                return

            # 2. 像报数一样，给每个客户分配正确的“行号”
            expected_id = 1
            for row in rows:
                current_id = row['id']

                # 如果当前 ID 不等于它应该在的位置 (比如它是 2，但应该在第 1 位)
                if current_id != expected_id:
                    # 更新 ID
                    sql_update = "UPDATE customers SET id = ? WHERE id = ?"
                    self.db.execute_update(sql_update, (expected_id, current_id))
                    print(f"系统自检：已自动修正客户 ID {current_id} -> {expected_id}")

                expected_id += 1

        except Exception as e:
            print(f"重排 ID 失败: {str(e)}")

    def get_next_id(self):
        """获取下一个 ID"""
        try:
            sql = "SELECT COUNT(*) as count FROM customers"
            result = self.db.execute_query(sql)
            count = result[0]['count'] if result else 0
            return count + 1
        except:
            return 1

    def create_customer(self, input_data: dict) -> dict:
        try:
            # 1. 验证
            if not input_data.get('name'): return {'success': False, 'message': '姓名不能为空'}
            if not input_data.get('phone'): return {'success': False, 'message': '手机号不能为空'}
            if not input_data.get('id_card'): return {'success': False, 'message': '身份证不能为空'}

            if self.check_exists(input_data['phone'], input_data['id_card']):
                return {'success': False, 'message': '手机号或身份证已存在'}

            # 2. 插入前先重排一次，确保环境干净
            self.reorder_all_ids()

            # 3. 计算新 ID
            new_id = self.get_next_id()
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            sql = "INSERT INTO customers (id, name, phone, id_card, created_at) VALUES (?, ?, ?, ?, ?)"
            params = (
            new_id, input_data['name'].strip(), input_data['phone'].strip(), input_data['id_card'].strip(), created_at)

            res = self.db.execute_update(sql, params)
            if res is not None:
                return {'success': True, 'message': f'添加成功，ID: {new_id}'}
            else:
                return {'success': False, 'message': '添加失败'}

        except Exception as e:
            return {'success': False, 'message': f'错误: {str(e)}'}

    def delete_customer(self, customer_id: str) -> dict:
        """删除客户后，立即执行全表重排"""
        try:
            cid = int(customer_id)
            sql = "DELETE FROM customers WHERE id = ?"
            result = self.db.execute_update(sql, (cid,))

            if result is not None and result > 0:
                # [关键步骤] 删除后立即重排，填补空缺
                self.reorder_all_ids()
                return {'success': True, 'message': '删除成功，ID已自动重新排序'}
            else:
                return {'success': False, 'message': '删除失败'}
        except Exception as e:
            return {'success': False, 'message': f'错误: {str(e)}'}

    def update_customer(self, customer_id: str, input_data: dict) -> dict:
        try:
            if not self.get_customer_by_id(customer_id):
                return {'success': False, 'message': '客户不存在'}

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

            if not set_fields: return {'success': False, 'message': '无修改内容'}

            params.append(customer_id)
            sql = f"UPDATE customers SET {', '.join(set_fields)} WHERE id = ?"

            if self.db.execute_update(sql, tuple(params)) is not None:
                return {'success': True, 'message': '更新成功'}
            else:
                return {'success': False, 'message': '更新失败'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def get_all_customers(self) -> dict:
        try:
            # 每次获取列表前，也可以尝试重排（为了保险），但一般删除/增加时处理就够了
            # self.reorder_all_ids()
            sql = "SELECT * FROM customers ORDER BY id ASC"
            data = self.db.execute_query(sql)
            return {'success': True, 'data': data if data else []}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def get_customer_by_id(self, customer_id: str) -> dict:
        try:
            sql = "SELECT * FROM customers WHERE id = ?"
            res = self.db.execute_query(sql, (customer_id,))
            if res: return {'success': True, 'data': res[0]}
            return {'success': False, 'message': '未找到'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def search_customers(self, keyword: str) -> dict:
        try:
            p = [f"%{keyword}%"] * 3
            sql_parts = ["name LIKE ?", "phone LIKE ?", "id_card LIKE ?"]
            if keyword.isdigit():
                sql_parts.append("id = ?")
                p.append(int(keyword))

            sql = f"SELECT * FROM customers WHERE {' OR '.join(sql_parts)} ORDER BY id ASC"
            data = self.db.execute_query(sql, tuple(p))
            return {'success': True, 'data': data if data else []}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def check_exists(self, phone, id_card):
        try:
            sql = "SELECT COUNT(*) as count FROM customers WHERE phone = ? OR id_card = ?"
            res = self.db.execute_query(sql, (phone, id_card))
            return res[0]['count'] > 0 if res else False
        except:
            return False