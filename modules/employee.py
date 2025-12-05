# modules/employee.py
from datetime import datetime
import hashlib


class Employee:
    def __init__(self, db):
        self.db = db
        # 初始化表结构
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        """初始化员工表及相关触发器"""
        try:
            # 1. 创建员工表
            sql_table = '''
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id VARCHAR(20) PRIMARY KEY,
                    employee_name VARCHAR(50) NOT NULL,
                    gender VARCHAR(10),
                    phone VARCHAR(20),
                    email VARCHAR(50),
                    department_id VARCHAR(20),
                    position_name VARCHAR(50),
                    hire_date DATE,
                    termination_date DATE,
                    status VARCHAR(20) DEFAULT '在职',
                    salary DECIMAL(10, 2),
                    username VARCHAR(50) UNIQUE,
                    password_hash VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
                )
            '''
            self.db.execute_update(sql_table)

            # 2. 创建更新时间戳触发器
            sql_trigger_update = '''
                CREATE TRIGGER IF NOT EXISTS update_employees_timestamp
                AFTER UPDATE ON employees
                FOR EACH ROW
                BEGIN
                    UPDATE employees
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE employee_id = NEW.employee_id;
                END
            '''
            self.db.execute_update(sql_trigger_update)

            # 3. 创建自动设置离职日期触发器
            sql_trigger_term = '''
                CREATE TRIGGER IF NOT EXISTS set_termination_date
                AFTER UPDATE OF status ON employees
                FOR EACH ROW
                WHEN NEW.status = '离职' AND OLD.status != '离职' AND NEW.termination_date IS NULL
                BEGIN
                    UPDATE employees
                    SET termination_date = DATE('now'), updated_at = CURRENT_TIMESTAMP
                    WHERE employee_id = NEW.employee_id;
                END
            '''
            self.db.execute_update(sql_trigger_term)

        except Exception as e:
            print(f"初始化员工表失败: {e}")

    def create_employee(self, input_data: dict) -> dict:
        try:
            # 1. 基础验证
            if not input_data.get('employee_name') or not input_data.get('gender'):
                return {'success': False, 'message': '姓名和性别是必填项'}

            if input_data.get('gender') not in ['男', '女']:
                return {'success': False, 'message': '性别必须是"男"或"女"'}

            # 2. 生成工号
            hire_date = input_data.get('hire_date')
            year = hire_date[:4] if hire_date else str(datetime.now().year)

            max_id = self.get_max_id(year)
            if max_id:
                try:
                    new_serial = int(max_id[-3:]) + 1
                except ValueError:
                    new_serial = 1
            else:
                new_serial = 1

            employee_id = f"{year}{str(new_serial).zfill(3)}"

            # 3. 检查用户名唯一性
            if input_data.get('username'):
                if self.check_username_exists(input_data['username']):
                    return {'success': False, 'message': '用户名已存在'}

            # 4. 准备数据库数据 (明确映射，避免脏数据)
            db_data = {
                'employee_id': employee_id,
                'employee_name': input_data['employee_name'].strip(),
                'gender': input_data['gender'],
                'hire_date': input_data.get('hire_date') or datetime.now().strftime('%Y-%m-%d'),
                'status': input_data.get('status', '在职')
            }

            # 处理可选的文本字段
            optional_fields = ['phone', 'email', 'department_id', 'position_name', 'username']
            for field in optional_fields:
                val = input_data.get(field)
                if val is not None and str(val).strip() != '':
                    db_data[field] = str(val).strip()
                else:
                    db_data[field] = None

            # 处理薪资 (安全转换)
            if input_data.get('salary'):
                try:
                    db_data['salary'] = float(input_data['salary'])
                except (ValueError, TypeError):
                    db_data['salary'] = 0.00
            else:
                db_data['salary'] = 0.00

            # 处理密码 (将 password 转换为 password_hash)
            if input_data.get('username') and input_data.get('password'):
                db_data['password_hash'] = hashlib.sha256(input_data['password'].encode()).hexdigest()
            else:
                db_data['password_hash'] = None

            # 5. 执行插入
            if self.insert_employee(db_data):
                return {
                    'success': True,
                    'data': self.get_employee_by_id(employee_id),
                    'message': f'员工创建成功，工号：{employee_id}'
                }
            else:
                return {'success': False, 'message': '创建失败，数据库写入错误'}

        except Exception as e:
            print(f"创建员工异常: {e}")
            return {'success': False, 'message': f'系统错误：{str(e)}'}

    def update_employee(self, employee_id: str, update_data: dict) -> dict:
        try:
            existing = self.get_employee_by_id(employee_id)
            if not existing:
                return {'success': False, 'message': '员工不存在'}

            # [核心修复] 过滤字段，只允许更新数据库存在的列
            valid_columns = {
                'employee_name', 'gender', 'phone', 'email', 'department_id',
                'position_name', 'hire_date', 'status', 'salary', 'username',
                'termination_date'
            }

            safe_data = {}

            # 1. 提取有效字段
            for key, value in update_data.items():
                if key in valid_columns:
                    # 处理空字符串为 None
                    if value == '':
                        safe_data[key] = None
                    else:
                        safe_data[key] = value

            # 2. 特殊处理密码字段
            # 如果前端传了 password 且不为空，则更新 password_hash
            new_password = update_data.get('password')
            if new_password and str(new_password).strip():
                safe_data['password_hash'] = hashlib.sha256(str(new_password).encode()).hexdigest()

            # 3. 特殊处理薪资类型
            if 'salary' in safe_data and safe_data['salary'] is not None:
                try:
                    safe_data['salary'] = float(safe_data['salary'])
                except:
                    safe_data['salary'] = 0.00

            # 如果没有有效字段需要更新，直接返回成功
            if not safe_data:
                return {'success': True, 'message': '没有检测到数据变更'}

            if self.db_update_employee(employee_id, safe_data):
                return {'success': True, 'message': '员工信息更新成功'}
            else:
                return {'success': False, 'message': '更新失败，数据库操作未生效'}

        except Exception as e:
            print(f"更新员工异常: {e}")
            return {'success': False, 'message': f'更新员工失败: {str(e)}'}

    def delete_employee(self, employee_id: str) -> dict:
        try:
            if self.db_delete_employee(employee_id):
                return {'success': True, 'message': '员工删除成功'}
            else:
                return {'success': False, 'message': '员工不存在或删除失败'}
        except Exception as e:
            return {'success': False, 'message': f'删除员工失败: {str(e)}'}

    def get_employee(self, employee_id: str) -> dict:
        try:
            employee = self.get_employee_by_id(employee_id)
            if employee:
                # 移除敏感信息
                if 'password_hash' in employee:
                    del employee['password_hash']
                return {'success': True, 'data': employee}
            else:
                return {'success': False, 'message': '员工不存在'}
        except Exception as e:
            return {'success': False, 'message': f'获取员工信息失败: {str(e)}'}

    def get_all_employees(self) -> dict:
        try:
            sql = '''
                  SELECT e.employee_id, e.employee_name, e.gender, e.phone, e.email,
                         e.department_id, e.position_name, e.hire_date, e.status, e.salary,
                         e.username, d.department_name
                  FROM employees e
                           LEFT JOIN departments d ON e.department_id = d.department_id
                  ORDER BY e.employee_id DESC
                  '''
            employees = self.db.execute_query(sql)
            return {
                'success': True,
                'data': employees or [],
                'message': f'获取到{len(employees) if employees else 0}名员工'
            }
        except Exception as e:
            return {'success': False, 'message': f'获取员工列表失败: {str(e)}'}

    # --- 数据库底层操作 ---

    def get_max_id(self, year: str) -> str:
        try:
            sql = "SELECT MAX(employee_id) as max_id FROM employees WHERE employee_id LIKE ?"
            result = self.db.execute_query(sql, (f"{year}%",))
            return result[0]['max_id'] if result and result[0]['max_id'] else None
        except:
            return None

    def check_username_exists(self, username: str) -> bool:
        try:
            sql = "SELECT COUNT(*) as count FROM employees WHERE username = ?"
            result = self.db.execute_query(sql, (username,))
            return result[0]['count'] > 0 if result else False
        except:
            return False

    def insert_employee(self, data: dict) -> bool:
        try:
            sql = '''
                  INSERT INTO employees (
                      employee_id, employee_name, gender, phone, email,
                      department_id, position_name, hire_date, status, salary,
                      username, password_hash
                  )
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                  '''
            # 使用元组确保顺序正确
            params = (
                data.get('employee_id'),
                data.get('employee_name'),
                data.get('gender'),
                data.get('phone'),
                data.get('email'),
                data.get('department_id'),
                data.get('position_name'),
                data.get('hire_date'),
                data.get('status'),
                data.get('salary'),
                data.get('username'),
                data.get('password_hash')
            )

            result = self.db.execute_update(sql, params)
            return result is not None and result > 0
        except Exception as e:
            print(f"插入员工SQL失败: {e}")
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
            return result[0] if result else None
        except:
            return None

    def db_update_employee(self, employee_id: str, update_data: dict) -> bool:
        try:
            set_fields = []
            params = []

            for field, value in update_data.items():
                set_fields.append(f"{field} = ?")
                params.append(value)

            if not set_fields:
                return False

            params.append(employee_id)

            # 动态构建 SQL
            sql = f"UPDATE employees SET {', '.join(set_fields)} WHERE employee_id = ?"

            # 调试日志
            # print(f"Execute Update: {sql}, Params: {params}")

            result = self.db.execute_update(sql, tuple(params))
            return result is not None and result > 0
        except Exception as e:
            print(f"更新员工SQL失败: {e}")
            return False

    def db_delete_employee(self, employee_id: str) -> bool:
        try:
            sql = "DELETE FROM employees WHERE employee_id = ?"
            result = self.db.execute_update(sql, (employee_id,))
            return result is not None and result > 0
        except:
            return False

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

            active_rate = (active / total * 100) if total > 0 else 0

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
            return {'total': 0, 'active': 0, 'terminated': 0, 'active_rate': 0, 'by_department': []}