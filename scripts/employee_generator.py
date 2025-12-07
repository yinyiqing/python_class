"""
生成员工数据
"""

import sqlite3
import random
import csv
from datetime import datetime, timedelta
import hashlib
import os
from pathlib import Path
import string
import sys
from typing import Dict, List, Tuple

current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

db_path = str(project_root / "hotel.db")

def date_offset(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

def random_date_range(start: int, end: int) -> str:
    days = random.randint(start, end)
    return date_offset(days)

def random_phone() -> str:
    prefix = random.choice(['13', '15', '17', '18', '19'])
    return f"{prefix}{random.randint(100000000, 999999999):09d}"

def random_email(username: str) -> str:
    return f"{username}@hotel.com"

def generate_password(length: int = 8) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_departments() -> List[Dict]:
    return [
        {'department_id': 'D001', 'department_name': '前厅部', 'description': '前台接待服务'},
        {'department_id': 'D002', 'department_name': '客房部', 'description': '客房清洁服务'},
        {'department_id': 'D003', 'department_name': '餐饮部', 'description': '餐厅餐饮服务'},
        {'department_id': 'D004', 'department_name': '财务部', 'description': '财务资金管理'},
        {'department_id': 'D005', 'department_name': '人事部', 'description': '负责员工招聘'}
    ]

def generate_employees(departments: List[Dict], count: int = 50) -> Tuple[List[Dict], List[Dict]]:
    department_positions = {
        'D001': ['前厅经理', '前台接待', '礼宾员'],
        'D002': ['客房经理', '客房服务员', '楼层主管'],
        'D003': ['餐饮经理', '服务员', '厨师'],
        'D004': ['财务经理', '会计', '出纳'],
        'D005': ['人事经理', '人事专员', '招聘专员']
    }

    dept_names = {
        'D001': '前厅',
        'D002': '客房',
        'D003': '餐饮',
        'D004': '财务',
        'D005': '人事'
    }

    employees = []
    passwords = []
    current_year = datetime.now().year
    year_sequences = {}

    for i, dept in enumerate(departments, 1):
        dept_id = dept['department_id']
        hire_year = current_year - random.randint(3, 5)
        hire_date = random_date_range(-365 * 5, -365 * 3)

        if hire_year not in year_sequences:
            year_sequences[hire_year] = 1
        seq = year_sequences[hire_year]
        year_sequences[hire_year] += 1

        employee_id = f"{hire_year}{str(seq).zfill(3)}"
        password = generate_password(8)
        password_hash = hash_password(password)
        employee_name = f"{dept_names[dept_id]}经理{i:02d}"

        manager = {
            'employee_id': employee_id,
            'employee_name': employee_name,
            'gender': random.choice(['男', '女']),
            'phone': random_phone(),
            'email': random_email(f"user{employee_id}"),
            'department_id': dept_id,
            'position_name': department_positions[dept_id][0],
            'hire_date': hire_date,
            'status': '在职',
            'salary': round(random.uniform(15000, 25000), 2),
            'username': f"user{employee_id}",
            'password_hash': password_hash,
        }
        employees.append(manager)

        passwords.append({
            'employee_id': employee_id,
            'employee_name': employee_name,
            'username': f"user{employee_id}",
            'password': password,
            'position': department_positions[dept_id][0],
            'department': dept['department_name']
        })

    for i in range(count - len(departments)):
        hire_year = current_year - random.randint(0, 3)
        hire_date = random_date_range(-365 * 3, -30)

        if hire_year not in year_sequences:
            year_sequences[hire_year] = 1
        seq = year_sequences[hire_year]
        year_sequences[hire_year] += 1

        employee_id = f"{hire_year}{str(seq).zfill(3)}"
        dept = random.choice(departments)
        dept_id = dept['department_id']
        positions = department_positions[dept_id]

        password = generate_password(8)
        password_hash = hash_password(password)
        position = random.choice(positions[1:])
        employee_name = f"{dept_names[dept_id]}员工{i + 1:03d}"

        employee = {
            'employee_id': employee_id,
            'employee_name': employee_name,
            'gender': random.choice(['男', '女']),
            'phone': random_phone(),
            'email': random_email(f"user{employee_id}"),
            'department_id': dept_id,
            'position_name': position,
            'hire_date': hire_date,
            'status': random.choices(['在职', '离职'], weights=[0.9, 0.1])[0],
            'salary': round(random.uniform(4000, 12000), 2),
            'username': f"user{employee_id}",
            'password_hash': password_hash,
        }

        if employee['status'] == '离职':
            hire_date_obj = datetime.strptime(employee['hire_date'], '%Y-%m-%d')
            termination_days = random.randint(30, 365)
            termination_date = hire_date_obj + timedelta(days=termination_days)
            employee['termination_date'] = termination_date.strftime('%Y-%m-%d')

        employees.append(employee)

        passwords.append({
            'employee_id': employee_id,
            'employee_name': employee_name,
            'username': f"user{employee_id}",
            'password': password,
            'position': position,
            'department': dept['department_name']
        })

    return employees, passwords

def create_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def check_tables_exist(conn: sqlite3.Connection) -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
    employees_exists = cursor.fetchone() is not None
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='departments'")
    departments_exists = cursor.fetchone() is not None
    return employees_exists and departments_exists

def clear_tables(conn: sqlite3.Connection) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM employees")
        cursor.execute("DELETE FROM departments")
        conn.commit()
        return True
    except:
        conn.rollback()
        return False

def insert_departments(conn: sqlite3.Connection, departments: List[Dict]) -> int:
    cursor = conn.cursor()
    count = 0
    for dept in departments:
        sql = "INSERT INTO departments (department_id, department_name, description) VALUES (?, ?, ?)"
        cursor.execute(sql, (dept['department_id'], dept['department_name'], dept['description']))
        count += 1
    conn.commit()
    return count

def insert_employees(conn: sqlite3.Connection, employees: List[Dict]) -> int:
    cursor = conn.cursor()
    count = 0
    for emp in employees:
        if 'termination_date' in emp:
            sql = """
                  INSERT INTO employees (employee_id, employee_name, gender, phone, email, department_id, \
                                         position_name, hire_date, termination_date, status, salary, username, \
                                         password_hash) \
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                  """
            params = (
                emp['employee_id'], emp['employee_name'], emp['gender'], emp['phone'],
                emp['email'], emp['department_id'], emp['position_name'], emp['hire_date'],
                emp['termination_date'], emp['status'], emp['salary'], emp['username'],
                emp['password_hash']
            )
        else:
            sql = """
                  INSERT INTO employees (employee_id, employee_name, gender, phone, email, department_id, \
                                         position_name, hire_date, status, salary, username, password_hash) \
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                  """
            params = (
                emp['employee_id'], emp['employee_name'], emp['gender'], emp['phone'],
                emp['email'], emp['department_id'], emp['position_name'], emp['hire_date'],
                emp['status'], emp['salary'], emp['username'], emp['password_hash']
            )
        cursor.execute(sql, params)
        count += 1
    conn.commit()
    return count

def export_passwords_to_csv(passwords: List[Dict], filename: str) -> str:
    filepath = Path(filename)
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['employee_id', 'employee_name', 'username', 'password', 'position', 'department']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in passwords:
            writer.writerow(item)
    return str(filepath)

def main():
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return

    conn = create_db_connection(db_path)
    if not check_tables_exist(conn):
        print("数据库表不存在")
        conn.close()
        return

    count = 50

    departments = generate_departments()
    employees, passwords = generate_employees(departments, count)

    if not clear_tables(conn):
        print("清空表失败")
        conn.close()
        return

    dept_count = insert_departments(conn, departments)
    emp_count = insert_employees(conn, employees)

    csv_file = export_passwords_to_csv(passwords, str(project_root / "employee_passwords.csv"))

    print(f"部门:{dept_count},员工:{emp_count},密码文件:{csv_file}")

    conn.close()

if __name__ == "__main__":
    main()