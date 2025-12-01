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
                if self.db.check_username_exists(input_data['username']):
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

            # 添加可选字段
            if input_data.get('phone'):
                db_data['phone'] = input_data['phone'].strip()

            if input_data.get('email'):
                db_data['email'] = input_data['email'].strip()

            if input_data.get('department_id'):
                db_data['department_id'] = input_data['department_id']

            if input_data.get('position_name'):
                db_data['position_name'] = input_data['position_name'].strip()

            if input_data.get('salary'):
                try:
                    db_data['salary'] = float(input_data['salary'])
                except:
                    db_data['salary'] = 0.00

            if input_data.get('username'):
                db_data['username'] = input_data['username'].strip()

            # 密码处理
            if input_data.get('username') and input_data.get('password'):
                db_data['password_hash'] = hashlib.sha256(input_data['password'].encode()).hexdigest()

            # 设置默认值
            db_data['hire_date'] = input_data.get('hire_date') or datetime.now().strftime('%Y-%m-%d')
            db_data['status'] = input_data.get('status', '在职')

            # 插入数据库
            if self.insert_employee(db_data):
                # 获取完整信息
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
        """更新员工信息"""
        try:
            # 检查员工是否存在
            existing = self.get_employee_by_id(employee_id)
            if not existing:
                return {'success': False, 'message': '员工不存在'}

            # 简单的更新逻辑
            if self.db_update_employee(employee_id, update_data):
                return {'success': True, 'message': '员工信息更新成功'}
            else:
                return {'success': False, 'message': '更新失败'}
        except Exception as e:
            return {'success': False, 'message': f'更新员工失败: {str(e)}'}

    def delete_employee(self, employee_id: str) -> dict:
        """删除员工"""
        try:
            if self.db_delete_employee(employee_id):
                return {'success': True, 'message': '员工删除成功'}
            else:
                return {'success': False, 'message': '员工不存在或删除失败'}
        except Exception as e:
            return {'success': False, 'message': f'删除员工失败: {str(e)}'}

    def get_employee(self, employee_id: str) -> dict:
        """获取单个员工信息"""
        try:
            employee = self.get_employee_by_id(employee_id)
            if employee:
                return {'success': True, 'data': employee}
            else:
                return {'success': False, 'message': '员工不存在'}
        except Exception as e:
            return {'success': False, 'message': f'获取员工信息失败: {str(e)}'}

    def get_all_employees(self) -> dict:
        """获取所有员工列表"""
        try:
            sql = '''
                  SELECT e.*, d.department_name
                  FROM employees e
                           LEFT JOIN departments d ON e.department_id = d.department_id
                  ORDER BY e.employee_id \
                  '''
            employees = self.db.execute_query(sql)

            return {
                'success': True,
                'data': employees,
                'message': f'获取到{len(employees)}名员工'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取员工列表失败: {str(e)}'
            }

    def get_max_id(self, year: str) -> str:
        """获取指定年份的最大工号"""
        sql = "SELECT MAX(employee_id) as max_id FROM employees WHERE employee_id LIKE ?"
        result = self.db.execute_query(sql, (f"{year}%",))
        return result[0]['max_id'] if result and result[0]['max_id'] else None

    def check_username_exists(self, username: str) -> bool:
        """检查用户名是否已存在"""
        sql = "SELECT COUNT(*) as count FROM employees WHERE username = ?"
        result = self.db.execute_query(sql, (username,))
        return result[0]['count'] > 0 if result else False

    def insert_employee(self, employee_data: dict) -> bool:
        """插入员工数据到数据库"""
        try:
            sql = '''
                  INSERT INTO employees (employee_id, employee_name, gender, phone, email,
                                         department_id, position_name, hire_date, status, salary,
                                         username, password_hash)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
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
        """根据工号获取员工信息"""
        sql = '''
              SELECT e.*, d.department_name
              FROM employees e
                       LEFT JOIN departments d ON e.department_id = d.department_id
              WHERE e.employee_id = ? \
              '''
        result = self.db.execute_query(sql, (employee_id,))
        return result[0] if result else None

    def db_update_employee(self, employee_id: str, update_data: dict) -> bool:
        """更新员工信息（数据库层面）"""
        try:
            # 构建更新语句
            set_fields = []
            params = []

            for field, value in update_data.items():
                if value is not None:
                    set_fields.append(f"{field} = ?")
                    params.append(value)

            if not set_fields:
                return False

            params.append(employee_id)
            sql = f"UPDATE employees SET {', '.join(set_fields)} WHERE employee_id = ?"

            result = self.db.execute_update(sql, tuple(params))
            return result is not None and result > 0
        except Exception as e:
            print(f"更新员工失败: {e}")
            return False

    def db_delete_employee(self, employee_id: str) -> bool:
        """删除员工（数据库层面）"""
        sql = "DELETE FROM employees WHERE employee_id = ?"
        result = self.db.execute_update(sql, (employee_id,))
        return result is not None and result > 0

    def get_employee_statistics(self) -> dict:
        """获取员工统计信息"""
        try:
            # 获取总人数
            total_sql = "SELECT COUNT(*) as total FROM employees"
            total_result = self.db.execute_query(total_sql)
            total = total_result[0]['total'] if total_result else 0

            # 获取在职人数
            active_sql = "SELECT COUNT(*) as active FROM employees WHERE status = '在职'"
            active_result = self.db.execute_query(active_sql)
            active = active_result[0]['active'] if active_result else 0

            # 获取离职人数
            terminated_sql = "SELECT COUNT(*) as terminated FROM employees WHERE status = '离职'"
            terminated_result = self.db.execute_query(terminated_sql)
            terminated = terminated_result[0]['terminated'] if terminated_result else 0

            # 计算在职率
            active_rate = (active / total * 100) if total > 0 else 0

            # 按部门统计
            dept_sql = '''
                       SELECT d.department_name, COUNT(e.employee_id) as count
                       FROM departments d
                           LEFT JOIN employees e \
                       ON d.department_id = e.department_id AND e.status = '在职'
                       GROUP BY d.department_id
                       ORDER BY count DESC \
                       '''
            by_department = self.db.execute_query(dept_sql)

            return {
                'total': total,
                'active': active,
                'terminated': terminated,
                'active_rate': active_rate,
                'by_department': by_department if by_department else []
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {
                'total': 0,
                'active': 0,
                'terminated': 0,
                'active_rate': 0,
                'by_department': []
            }