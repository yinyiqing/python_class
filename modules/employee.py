from datetime import datetime
import hashlib

class Employee:
    def __init__(self, db):
        self.db = db

    def create_employee(self, input_data: dict) -> dict:
        try:
            # 验证基本信息
            if not input_data.get('employee_name') or not input_data.get('gender'):
                return {
                    'success': False,
                    'message': '姓名和性别是必填项'
                }

            if input_data.get('gender') not in ['男', '女']:
                return {
                    'success': False,
                    'message': '性别必须是"男"或"女"'
                }

            # 生成工号
            hire_date = input_data.get('hire_date')
            year = hire_date[:4] if hire_date else str(datetime.now().year)

            max_id = self.get_max_id(year)
            if max_id:
                new_serial = int(max_id[-3:]) + 1
            else:
                new_serial = 1

            employee_id = f"{year}{str(new_serial).zfill(3)}"

            # 检查用户名是否已存在
            if input_data.get('username'):
                if self.check_username_exists(input_data['username']):
                    return {
                        'success': False,
                        'message': '用户名已存在'
                    }

            # 准备数据库数据
            db_data = {
                'employee_id': employee_id,
                'employee_name': input_data['employee_name'].strip(),
                'gender': input_data['gender']
            }

            # 处理可选字段
            for field in ['phone', 'email', 'department_id', 'position_name', 'username']:
                if input_data.get(field):
                    db_data[field] = input_data[field].strip()

            if input_data.get('salary'):
                try:
                    db_data['salary'] = float(input_data['salary'])
                except:
                    db_data['salary'] = 0.00

            # 密码处理
            if input_data.get('username') and input_data.get('password'):
                db_data['password_hash'] = hashlib.sha256(input_data['password'].encode()).hexdigest()

            # 设置默认值
            db_data['hire_date'] = input_data.get('hire_date') or datetime.now().strftime('%Y-%m-%d')
            db_data['status'] = input_data.get('status', '在职')

            # 插入数据库
            if self.insert_employee(db_data):
                # 获取完整信息返回
                employee_info = self.get_employee_by_id(employee_id)
                return {
                    'success': True,
                    'data': employee_info,
                    'message': f'员工创建成功，工号：{employee_id}'
                }
            else:
                return {
                    'success': False,
                    'message': '创建失败，请稍后重试'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'创建过程中发生错误：{str(e)}'
            }

    def update_employee(self, employee_id: str, update_data: dict) -> dict:
        try:
            existing = self.get_employee_by_id(employee_id)
            if not existing:
                return {
                    'success': False,
                    'message': '员工不存在'
                }

            if self.db_update_employee(employee_id, update_data):
                return {
                    'success': True,
                    'message': '员工信息更新成功'
                }
            else:
                return {
                    'success': False,
                    'message': '更新失败'
                }
        except Exception as e:
            return {'success': False, 'message': f'更新员工失败: {str(e)}'}

    def delete_employee(self, employee_id: str) -> dict:
        try:
            if self.db_delete_employee(employee_id):
                return {
                    'success': True,
                    'message': '员工删除成功'
                }
            else:
                return {
                    'success': False,
                    'message': '员工不存在或删除失败'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'删除员工失败: {str(e)}'
            }

    def get_employee_statistics(self) -> dict:
        print("执行 get_employee_statistics()")
        try:
            # 总员工数
            total_res = self.db.execute_query("SELECT COUNT(*) AS total FROM employees")
            print("total_res:", total_res)  # 调试输出
            total = total_res[0]['total'] if total_res else 0

            # 在职员工数
            active_res = self.db.execute_query("SELECT COUNT(*) AS active FROM employees WHERE TRIM(status) = '在职'")
            print("active_res:", active_res)  # 调试输出
            active = active_res[0]['active'] if active_res else 0

            # 离职员工数
            terminated_res = self.db.execute_query("SELECT COUNT(*) AS terminated FROM employees WHERE TRIM(status) = '离职'")
            print("terminated_res:", terminated_res)  # 调试输出
            terminated = terminated_res[0]['terminated'] if terminated_res else 0

            # 在职率
            active_rate = f"{(active / total * 100):.0f}%" if total else '0%'

            # 按部门统计在职员工
            dept_sql = '''
                SELECT d.department_name, COUNT(e.employee_id) AS count
                FROM departments d
                LEFT JOIN employees e
                    ON d.department_id = e.department_id AND TRIM(e.status) = '在职'
                GROUP BY d.department_id
                ORDER BY count DESC
            '''
            by_dept = self.db.execute_query(dept_sql) or []
            print("by_department:", by_dept)  # 调试输出

            return {
                'success': True,
                'total': total,
                'active': active,
                'terminated': terminated,
                'active_rate': active_rate,
                'by_department': by_dept
            }

        except Exception as e:
            print(f"统计失败: {e}")
            return {
                'success': False,
                'total': 0,
                'active': 0,
                'terminated': 0,
                'active_rate': '0%',
                'by_department': []
            }


    def get_all_employees(self) -> dict:
        try:
            sql = '''
                  SELECT e.*, d.department_name
                  FROM employees e
                      LEFT JOIN departments d ON e.department_id = d.department_id
                  ORDER BY e.employee_id
                  '''
            employees = self.db.execute_query(sql)
            return {
                'success': True,
                'data': employees or [],
                'message': f'获取到{len(employees) if employees else 0}名员工'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取员工列表失败: {str(e)}'
            }

    def get_max_id(self, year: str) -> str:
        sql = '''
              SELECT MAX(employee_id) as max_id
              FROM employees
              WHERE employee_id LIKE ?
              '''
        result = self.db.execute_query(sql, (f"{year}%",))
        return result[0]['max_id'] if result and result[0]['max_id'] else None

    def check_username_exists(self, username: str) -> bool:
        sql = '''
              SELECT COUNT(*) as count
              FROM employees
              WHERE username = ?
              '''
        result = self.db.execute_query(sql, (username,))
        return result[0]['count'] > 0 if result else False

    def insert_employee(self, employee_data: dict) -> bool:
        try:
            sql = '''
                  INSERT INTO employees (employee_id, employee_name, gender, phone, email,
                                         department_id, position_name, hire_date, status, salary,
                                         username, password_hash)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                  '''
            result = self.db.execute_update(sql, (
                employee_data.get('employee_id'),
                employee_data.get('employee_name'),
                employee_data.get('gender'),
                employee_data.get('phone'),
                employee_data.get('email'),
                employee_data.get('department_id'),
                employee_data.get('position_name'),
                employee_data.get('hire_date'),
                employee_data.get('status', '在职'),
                employee_data.get('salary', 0.00),
                employee_data.get('username'),
                employee_data.get('password_hash')
            ))
            return result is not None and result > 0
        except Exception as e:
            print(f"插入员工数据失败: {e}")
            return False

    def get_employee_by_id(self, employee_id: str) -> dict:
        try:
            sql = '''
                SELECT e.*, d.department_name
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.department_id
                WHERE e.employee_id = ?
                '''
            result = self.db.execute_query(sql, (employee_id,))
            print("get_employee_by_id result:", result)
            return result[0] if result else None
        except Exception as e:
            print(f"get_employee_by_id 出错: {e}")
            raise

    def db_update_employee(self, employee_id: str, update_data: dict) -> bool:
        try:
            set_fields = []
            params = []
            for field, value in update_data.items():
                if value is not None:
                    set_fields.append(f"{field} = ?")
                    params.append(value)

            if not set_fields: return False

            params.append(employee_id)
            sql = f"UPDATE employees SET {', '.join(set_fields)} WHERE employee_id = ?"
            result = self.db.execute_update(sql, tuple(params))
            return result is not None and result > 0
        except Exception as e:
            print(f"更新员工失败: {e}")
            return False

    def db_delete_employee(self, employee_id: str) -> bool:
        sql = "DELETE FROM employees WHERE employee_id = ?"
        result = self.db.execute_update(sql, (employee_id,))
        return result is not None and result > 0

    def get_employee_statistics(self) -> dict:
        try:
            total = 0
            active = 0
            terminated = 0

            total_res = self.db.execute_query("SELECT COUNT(*) as total FROM employees")
            if total_res: total = total_res[0]['total']

            active_res = self.db.execute_query("SELECT COUNT(*) as active FROM employees WHERE status = '在职'")
            if active_res: active = active_res[0]['active']

            term_res = self.db.execute_query("SELECT COUNT(*) as terminated FROM employees WHERE status = '离职'")
            if term_res: terminated = term_res[0]['terminated']

            active_rate = f"{(active / total * 100):.0f}%" if total > 0 else '0%'

            dept_sql = '''
                    SELECT d.department_name, COUNT(e.employee_id) as count
                    FROM departments d
                        LEFT JOIN employees e 
                    ON d.department_id = e.department_id AND e.status = '在职'
                    GROUP BY d.department_id
                    ORDER BY count DESC
                    '''
            by_dept = self.db.execute_query(dept_sql)

            return {
                'total': total,
                'active': active,
                'terminated': terminated,
                'active_rate': active_rate,
                'by_department': by_dept or []
            }
        except Exception as e:
            print(f"统计失败: {e}")
            return {'total': 0, 'active': 0, 'terminated': 0, 'active_rate': '0%', 'by_department': []}
