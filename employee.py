from datetime import datetime, date
import hashlib
import os
import re
import sqlite3

class EmployeeNotFound(Exception):
    # 员工未找到异常
    pass

class EmployeeValidationError(Exception):
    # 员工数据验证异常
    pass

class EmployeeDuplicateError(Exception):
    # 员工重复异常
    pass

class Employee:
    def __init__(self, db_connection=None, employee_id=None, **kwargs):
        # 基本属性初始化
        self.id = None
        self.employee_id = None
        self.name = None
        self.gender = None
        self.phone = None
        self.email = None
        self.department = None
        self.position = None
        self.hire_date = None
        self.status = '在职'
        self.salary = None
        self.username = None
        self.password_hash = None
        self.created_at = None
        self.updated_at = None

        # 实例化逻辑
        if db_connection and employee_id:
            self._load_from_db(db_connection, employee_id)
        elif kwargs:
            self._init_from_kwargs(kwargs)

    def _load_from_db(self, conn, employee_id):
        cursor = conn.cursor()

        # 修复参数绑定逻辑
        if isinstance(employee_id, int):
            # 如果是整数，按主键ID查询
            query = "SELECT * FROM employees WHERE id = ?"
            params = (employee_id,)
        elif isinstance(employee_id, str) and employee_id.isdigit():
            # 如果是数字字符串，可以按ID或employee_id查询
            query = "SELECT * FROM employees WHERE id = ? OR employee_id = ?"
            params = (int(employee_id), employee_id)
        else:
            # 其他情况按员工编号查询
            query = "SELECT * FROM employees WHERE employee_id = ?"
            params = (str(employee_id),)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if not result:
            raise EmployeeNotFound(f"员工ID '{employee_id}' 未找到")

        # 将数据库结果映射到对象属性
        self._map_db_result_to_attributes(result)

    def _map_db_result_to_attributes(self, result):
        # 数据库查询结果映射到对象属性
        columns = ['id', 'employee_id', 'name', 'gender', 'phone', 'email',
                   'department', 'position', 'hire_date', 'status', 'salary',
                   'username', 'password_hash', 'created_at', 'updated_at']

        for i, column in enumerate(columns):
            if i < len(result):
                setattr(self, column, result[i])

    def _init_from_kwargs(self, kwargs):
        # 从关键字参数初始化属性
        valid_attributes = ['id', 'employee_id', 'name', 'gender', 'phone',
                            'email', 'department', 'position', 'hire_date',
                            'status', 'salary', 'username', 'password_hash',
                            'created_at', 'updated_at']

        for key, value in kwargs.items():
            if key in valid_attributes and value is not None:
                setattr(self, key, value)

    def save(self, conn):
        # 保存员工信息到数据库
        is_valid, errors = self.validate()
        if not is_valid:
            raise EmployeeValidationError(f"数据验证失败: {', '.join(errors)}")

        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.id is None:
            # 新增员工
            if not self.employee_id:
                self.employee_id = self._generate_employee_id(conn)

            # 检查员工编号是否重复
            cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (self.employee_id,))
            if cursor.fetchone():
                raise EmployeeDuplicateError(f"员工编号 '{self.employee_id}' 已存在")

            # 检查用户名是否重复
            if self.username:
                cursor.execute("SELECT id FROM employees WHERE username = ?", (self.username,))
                if cursor.fetchone():
                    raise EmployeeDuplicateError(f"用户名 '{self.username}' 已存在")

            query = """
            INSERT INTO employees
            (employee_id, name, gender, phone, email, department, position,
             hire_date, status, salary, username, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                self.employee_id, self.name, self.gender, self.phone, self.email,
                self.department, self.position, self.hire_date, self.status,
                self.salary, self.username, self.password_hash, current_time, current_time
            )

            cursor.execute(query, params)
            self.id = cursor.lastrowid
            self.created_at = current_time
            self.updated_at = current_time
        else:
            # 更新员工信息
            query = """
            UPDATE employees 
            SET name=?, gender=?, phone=?, email=?, department=?, position=?,
                hire_date=?, status=?, salary=?, username=?, password_hash=?, updated_at=?
            WHERE id=?
            """
            params = (
                self.name, self.gender, self.phone, self.email,
                self.department, self.position, self.hire_date, self.status,
                self.salary, self.username, self.password_hash, current_time, self.id
            )

            cursor.execute(query, params)
            self.updated_at = current_time

        conn.commit()
        return True

    def _generate_employee_id(self, conn):
        # 生成员工编号
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(employee_id) FROM employees WHERE employee_id LIKE 'EMP%'")
        result = cursor.fetchone()

        if result and result[0]:
            last_id = result[0]
            number = int(last_id[3:]) + 1
        else:
            number = 1

        return f"EMP{number:05d}"

    def validate(self):
        # 验证员工数据完整性
        errors = []

        # 检查必填字段
        required_fields = {
            'name': '姓名',
            'department': '部门',
            'position': '职位',
            'hire_date': '入职日期'
        }

        for field, field_name in required_fields.items():
            if not getattr(self, field):
                errors.append(f"{field_name}是必填字段")

        # 检查员工编号格式
        if self.employee_id and not re.match(r'^EMP\d{5}$', self.employee_id):
            errors.append("员工编号格式不正确，应为EMP后跟5位数字")

        # 检查手机号格式
        if self.phone and not self._validate_phone_format():
            errors.append("手机号格式不正确")

        # 检查邮箱格式
        if self.email and not self._validate_email_format():
            errors.append("邮箱格式不正确")

        # 检查日期格式
        if self.hire_date:
            try:
                if isinstance(self.hire_date, str):
                    datetime.strptime(self.hire_date, '%Y-%m-%d')
            except ValueError:
                errors.append("入职日期格式不正确，应为YYYY-MM-DD")

        return len(errors) == 0, errors

    def _validate_phone_format(self):
        # 验证手机号格式
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, self.phone) is not None

    def _validate_email_format(self):
        # 验证邮箱格式
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, self.email) is not None

    def set_password(self, password):
        # 设置密码并哈希处理
        self.password_hash = self._hash_password(password)

    def _hash_password(self, password):
        # 密码哈希处理
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        # 检查密码是否正确
        if not self.password_hash:
            return False
        return self.password_hash == self._hash_password(password)

    def get_roles(self, conn):
        # 获取员工的所有角色
        cursor = conn.cursor()
        query = """
        SELECT r.id, r.name, r.permissions
        FROM roles r
        JOIN employee_roles er ON r.id = er.role_id
        WHERE er.employee_id = ?
        """
        cursor.execute(query, (self.id,))
        return cursor.fetchall()

    def has_permission(self, conn, permission):
        # 检查员工是否拥有指定权限
        roles = self.get_roles(conn)
        for role in roles:
            permissions = role[2]  # permissions 字段
            if permissions and permission in permissions:
                return True
        return False

    def delete(self, conn, soft_delete=True):
        # 删除员工
        cursor = conn.cursor()

        if soft_delete:
            # 软删除 -> 将状态改为离职
            self.status = '离职'
            self.save(conn)
        else:
            # 硬删除 -> 从数据库彻底删除
            cursor.execute("DELETE FROM employees WHERE id = ?", (self.id,))
            cursor.execute("DELETE FROM employee_roles WHERE employee_id = ?", (self.id,))
            conn.commit()

    @property
    def work_years(self):
        # 计算工作年限
        if self.hire_date:
            if isinstance(self.hire_date, str):
                hire_date = datetime.strptime(self.hire_date, '%Y-%m-%d').date()
            else:
                hire_date = self.hire_date

            today = date.today()
            years = today.year - hire_date.year

            # 如果今年的入职日期还没到，则减1年
            if today.month < hire_date.month or (today.month == hire_date.month and today.day < hire_date.day):
                years -= 1

            return max(0, years)
        return 0

    @property
    def is_active(self):
        # 检查员工是否在职
        return self.status == '在职'

    def to_dict(self):
        # 将对象转换为字典
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'name': self.name,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'department': self.department,
            'position': self.position,
            'hire_date': self.hire_date,
            'status': self.status,
            'salary': float(self.salary) if self.salary else None,
            'username': self.username,
            'work_years': self.work_years,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    # 类方法
    @classmethod
    def create_new(cls, db_connection, employee_data):
        # 创建新员工
        employee = cls(**employee_data)
        employee.save(db_connection)
        return employee

    @classmethod
    def get_all(cls, db_connection, department=None, status=None):
        # 获取员工列表
        cursor = db_connection.cursor()

        query = "SELECT * FROM employees"
        params = []

        conditions = []
        if department:
            conditions.append("department = ?")
            params.append(department)
        if status:
            conditions.append("status = ?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY id DESC"

        cursor.execute(query, params)
        results = cursor.fetchall()

        employees = []
        for result in results:
            emp = cls()
            emp._map_db_result_to_attributes(result)
            employees.append(emp)

        return employees

    @classmethod
    def get_by_department(cls, db_connection, department):
        # 按部门查询员工
        return cls.get_all(db_connection, department=department)

    @classmethod
    def search(cls, db_connection, keyword):
        # 搜索员工
        cursor = db_connection.cursor()

        query = """
        SELECT * 
        FROM employees
        WHERE name LIKE ? 
           OR employee_id LIKE ? 
           OR phone LIKE ? 
           OR email LIKE ?
        ORDER BY id DESC
        """
        search_pattern = f"%{keyword}%"
        params = [search_pattern] * 4

        cursor.execute(query, params)
        results = cursor.fetchall()

        employees = []
        for result in results:
            emp = cls()
            emp._map_db_result_to_attributes(result)
            employees.append(emp)

        return employees

# 数据库初始化函数
def init_database(db_path='hotel.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建员工表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id VARCHAR(20) UNIQUE NOT NULL,
        name VARCHAR(50) NOT NULL,
        gender VARCHAR(10),
        phone VARCHAR(20),
        email VARCHAR(100),
        department VARCHAR(50) NOT NULL,
        position VARCHAR(50) NOT NULL,
        hire_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT '在职',
        salary DECIMAL(10,2),
        username VARCHAR(50) UNIQUE,
        password_hash VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 创建部门表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) UNIQUE NOT NULL,
        description TEXT,
        manager_id INTEGER
    )
    ''')

    # 创建角色表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) UNIQUE NOT NULL,
        permissions TEXT
    )
    ''')

    # 创建员工角色关联表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employee_roles
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees (id),
        FOREIGN KEY (role_id) REFERENCES roles (id)
    )
    ''')

    # 插入初始数据
    cursor.execute('''
    INSERT OR IGNORE INTO departments (name, description) 
    VALUES 
    ('前台', '客户接待和服务'),
    ('客房部', '客房清洁和维护'),
    ('餐饮部', '餐厅和酒吧服务'),
    ('管理层', '酒店管理')
    ''')

    cursor.execute('''
    INSERT OR IGNORE INTO roles (name, permissions) 
    VALUES 
    ('admin', '["create", "read", "update", "delete", "manage_users"]'),
    ('manager', '["create", "read", "update", "view_reports"]'),
    ('staff', '["read", "update_own"]')
    ''')

    conn.commit()
    conn.close()

def test_employee():
    # 初始化数据库
    db_path = 'interactive_test_hotel.db'
    if os.path.exists(db_path):
        os.remove(db_path)

    init_database(db_path)
    conn = sqlite3.connect(db_path)

    current_employee = None  # 当前操作的员工对象

    try:
        print("=== Employee类交互式测试 ===")
        print("每次操作完成后，您可以选择下一步要执行的操作\n")

        while True:
            print("\n" + "=" * 50)
            print("请选择要执行的操作:")
            print("1. 创建新员工")
            print("2. 加载员工")
            print("3. 更新员工信息")
            print("4. 查看所有员工")
            print("5. 按部门查看员工")
            print("6. 搜索员工")
            print("7. 验证密码")
            print("8. 删除员工")
            print("9. 数据验证测试")
            print("10. 查看当前员工详情")
            print("0. 退出测试")

            choice = input("\n请输入选择 (0-10): ").strip()

            if choice == "0":
                break

            elif choice == "1":
                print("\n>>> 创建新员工")
                print("-" * 30)

                emp_data = {}
                emp_data['name'] = input("姓名: ") or "测试员工"
                emp_data['gender'] = input("性别(男/女): ") or "男"
                emp_data['phone'] = input("手机号: ") or "13800138000"
                emp_data['email'] = input("邮箱: ") or "test@hotel.com"
                emp_data['department'] = input("部门: ") or "前台"
                emp_data['position'] = input("职位: ") or "接待员"
                emp_data['hire_date'] = input("入职日期(YYYY-MM-DD): ") or "2024-01-01"

                salary_input = input("薪资: ") or "5000"
                emp_data['salary'] = float(salary_input)

                emp_data['username'] = input("用户名: ") or "testuser"

                try:
                    new_emp = Employee.create_new(conn, emp_data)
                    password = input("设置密码: ") or "123456"
                    new_emp.set_password(password)
                    new_emp.save(conn)

                    current_employee = new_emp
                    print(f"\n创建成功!")
                    print(f"员工编号: {new_emp.employee_id}")
                    print(f"员工ID: {new_emp.id}")

                except Exception as e:
                    print(f"创建失败: {e}")

            elif choice == "2":
                print("\n>>> 加载员工")
                print("-" * 30)

                if not current_employee:
                    print("提示: 当前没有选中员工，请输入要加载的员工信息")

                load_by = input("按什么加载? (1-ID, 2-员工编号): ") or "2"

                if load_by == "1":
                    emp_id = input("请输入员工ID: ")
                    if emp_id:
                        try:
                            current_employee = Employee(conn, int(emp_id))
                        except ValueError:
                            print("ID必须是数字")
                            continue
                else:
                    emp_code = input("请输入员工编号: ") or (current_employee.employee_id if current_employee else "")
                    if emp_code:
                        current_employee = Employee(conn, emp_code)

                if current_employee:
                    print(f"\n加载成功!")
                    print(f"姓名: {current_employee.name}")
                    print(f"员工编号: {current_employee.employee_id}")
                    print(f"部门: {current_employee.department}")
                    print(f"职位: {current_employee.position}")
                else:
                    print("加载失败")

            elif choice == "3":
                if not current_employee:
                    print("请先加载一个员工")
                    continue

                print(f"\n>>> 更新员工信息: {current_employee.name}")
                print("-" * 30)

                print("当前信息:")
                print(f"姓名: {current_employee.name}")
                print(f"性别: {current_employee.gender}")
                print(f"手机: {current_employee.phone}")
                print(f"邮箱: {current_employee.email}")
                print(f"部门: {current_employee.department}")
                print(f"职位: {current_employee.position}")
                print(f"薪资: {current_employee.salary}")

                print("\n输入新信息(直接回车保持原值):")

                new_name = input(f"姓名 [{current_employee.name}]: ")
                if new_name: current_employee.name = new_name

                new_gender = input(f"性别 [{current_employee.gender}]: ")
                if new_gender: current_employee.gender = new_gender

                new_phone = input(f"手机 [{current_employee.phone}]: ")
                if new_phone: current_employee.phone = new_phone

                new_email = input(f"邮箱 [{current_employee.email}]: ")
                if new_email: current_employee.email = new_email

                new_dept = input(f"部门 [{current_employee.department}]: ")
                if new_dept: current_employee.department = new_dept

                new_position = input(f"职位 [{current_employee.position}]: ")
                if new_position: current_employee.position = new_position

                new_salary = input(f"薪资 [{current_employee.salary}]: ")
                if new_salary: current_employee.salary = float(new_salary)

                try:
                    current_employee.save(conn)
                    print("更新成功!")
                except Exception as e:
                    print(f"更新失败: {e}")

            elif choice == "4":
                print("\n>>> 所有员工列表")
                print("-" * 30)

                employees = Employee.get_all(conn)
                print(f"员工总数: {len(employees)}")

                for i, emp in enumerate(employees, 1):
                    print(f"{i}. {emp.name} ({emp.employee_id})")
                    print(f"   部门: {emp.department}, 职位: {emp.position}, 状态: {emp.status}")

            elif choice == "5":
                print("\n>>> 按部门查看员工")
                print("-" * 30)

                department = input("请输入部门名称: ") or "前台"
                employees = Employee.get_by_department(conn, department)

                print(f"{department}部门员工: {len(employees)}人")
                for i, emp in enumerate(employees, 1):
                    print(f"{i}. {emp.name} - {emp.position} - {emp.status}")

            elif choice == "6":
                print("\n>>> 搜索员工")
                print("-" * 30)

                keyword = input("请输入搜索关键词: ") or "测试"
                results = Employee.search(conn, keyword)

                print(f"搜索 '{keyword}' 结果: {len(results)}人")
                for i, emp in enumerate(results, 1):
                    print(f"{i}. {emp.name} - {emp.department} - {emp.position} - {emp.employee_id}")

            elif choice == "7":
                if not current_employee:
                    print("请先加载一个员工")
                    continue

                print(f"\n>>> 验证密码: {current_employee.name}")
                print("-" * 30)

                password = input("请输入密码: ")
                if password:
                    result = current_employee.check_password(password)
                    print(f"密码验证: {'正确' if result else '错误'}")
                else:
                    print("未输入密码")

            elif choice == "8":
                print("\n>>> 删除员工")
                print("-" * 30)

                # 先显示所有员工
                employees = Employee.get_all(conn)
                print("所有员工:")
                for i, emp in enumerate(employees, 1):
                    print(f"{i}. {emp.name} ({emp.employee_id}) - {emp.status}")

                emp_index = input(f"\n选择要删除的员工编号(1-{len(employees)}): ")
                if emp_index and emp_index.isdigit():
                    index = int(emp_index) - 1
                    if 0 <= index < len(employees):
                        emp_to_delete = employees[index]
                        print(f"准备操作: {emp_to_delete.name} ({emp_to_delete.employee_id})")

                        delete_type = input("删除类型 (1-软删除, 2-硬删除): ") or "1"

                        if delete_type == "1":
                            emp_to_delete.delete(conn, soft_delete=True)
                            print("软删除完成，员工状态改为'离职'")
                        else:
                            confirm = input("确认硬删除? 此操作不可逆! (y/n): ")
                            if confirm.lower() == 'y':
                                emp_to_delete.delete(conn, soft_delete=False)
                                print("硬删除完成")
                            else:
                                print("取消删除")
                    else:
                        print("无效的编号")
                else:
                    print("无效输入")

            elif choice == "9":
                print("\n>>> 数据验证测试")
                print("-" * 30)

                print("创建测试员工对象进行验证:")
                test_emp = Employee(
                    name=input("姓名: ") or "测试用户",
                    phone=input("手机号: ") or "123456",
                    email=input("邮箱: ") or "invalid-email",
                    department=input("部门: ") or "",
                    position=input("职位: ") or "",
                    hire_date=input("入职日期: ") or "invalid-date"
                )

                is_valid, errors = test_emp.validate()
                print(f"\n验证结果: {'通过' if is_valid else '失败'}")
                if errors:
                    print("错误信息:")
                    for error in errors:
                        print(f"  - {error}")

            elif choice == "10":
                if not current_employee:
                    print("当前没有选中的员工")
                    continue

                print(f"\n>>> 当前员工详情: {current_employee.name}")
                print("-" * 30)

                emp_dict = current_employee.to_dict()
                for key, value in emp_dict.items():
                    print(f"{key}: {value}")

            else:
                print("无效选择，请重新输入")

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()
        print(f"\n数据库连接已关闭")

        keep_db = input("是否保留测试数据库? (y/n): ")
        if keep_db.lower() != 'y':
            if os.path.exists(db_path):
                os.remove(db_path)
                print("测试数据库已删除")
        else:
            print(f"数据库已保留: {db_path}")

if __name__ == "__main__":
    test_employee()