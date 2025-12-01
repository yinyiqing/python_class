import sqlite3

class Database:
    def __init__(self, db_path: str = "hotel.db"):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        conn = self._get_connection()
        try:
            # 创建部门表
            conn.execute('''
                         CREATE TABLE IF NOT EXISTS departments(
                             department_id VARCHAR(20) PRIMARY KEY,
                             department_name VARCHAR(50) NOT NULL UNIQUE,
                             manager VARCHAR(50),
                             description TEXT,
                             created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                             updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
                         ''')

            # 创建触发器，当部门表有信息更新时，更新 updated_at 字段
            conn.execute('''
                         CREATE TRIGGER IF NOT EXISTS update_departments_timestamp
                             AFTER UPDATE ON departments
                             FOR EACH ROW
                             BEGIN
                                 UPDATE departments
                                 SET updated_at = CURRENT_TIMESTAMP
                                 WHERE department_id = NEW.department_id;
                             END;
                         ''')

            # 创建员工表
            conn.execute('''
                         CREATE TABLE IF NOT EXISTS employees(
                             employee_id VARCHAR(20) PRIMARY KEY,
                             employee_name VARCHAR(50) NOT NULL,
                             gender VARCHAR(10) CHECK(gender IN ('男', '女')),
                             phone VARCHAR(20),
                             email VARCHAR(50),
                             department_id VARCHAR(20),
                             position_name VARCHAR(50),
                             hire_date DATE,
                             termination_date DATE,
                             status VARCHAR(20) DEFAULT '在职' CHECK(status IN('在职', '离职')),
                             salary DECIMAL(10, 2),
                             username VARCHAR(50) UNIQUE,
                             password_hash VARCHAR(255),
                             created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                             updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                             FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
                             )
                         ''')

            # 创建触发器，当员工表有信息更新时，更新 updated_at 字段
            conn.execute('''
                         CREATE TRIGGER IF NOT EXISTS update_employees_timestamp
                         AFTER UPDATE ON employees
                         FOR EACH ROW
                         BEGIN
                             UPDATE employees
                             SET updated_at = CURRENT_TIMESTAMP
                             WHERE employee_id = NEW.employee_id;
                         END;
                         ''')

            # 创建触发器，当员工状态更新为离职时，自动设置离职时间为当前日期
            conn.execute('''
                         CREATE TRIGGER IF NOT EXISTS set_termination_date
                             AFTER UPDATE OF status ON employees
                             FOR EACH ROW
                             WHEN NEW.status = '离职' AND OLD.status != '离职' AND NEW.termination_date IS NULL
                             BEGIN
                                 UPDATE employees
                                 SET termination_date = DATE ('now'), updated_at = CURRENT_TIMESTAMP
                                 WHERE employee_id = NEW.employee_id;
                             END;
                         ''')

            conn.commit()
            print("数据库初始化成功！")

        except Exception as e:
            print(f"数据库初始化失败: {e}")
        finally:
            conn.close()

    def execute_query(self, sql: str, params: tuple = None):
        """执行查询并返回结果"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            if sql.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            print(f"数据库操作失败: {e}")
            raise e
        finally:
            conn.close()

    def execute_update(self, sql: str, params: tuple = None):
        """执行更新操作"""
        return self.execute_query(sql, params)