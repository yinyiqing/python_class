

import sqlite3
import re
from datetime import datetime


# ===========================
# 自定义异常
# ===========================

class CustomerNotFound(Exception):
    """客户未找到异常"""
    pass


class CustomerValidationError(Exception):
    """客户数据验证异常"""
    pass


class CustomerDuplicateError(Exception):
    """手机号或身份证号重复异常"""
    pass


# ===========================
# 表结构初始化（只负责 customers）
# ===========================

def init_customer_module(db_path: str = 'hotel.db'):

    conn = sqlite3.connect(db_path)
    try:
        init_customer_tables(conn)
        conn.commit()
    finally:
        conn.close()


def init_customer_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL,               -- 姓名
        phone VARCHAR(20) UNIQUE NOT NULL,       -- 手机号（唯一）
        id_card VARCHAR(20) UNIQUE NOT NULL,     -- 身份证号（唯一）
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')


# ===========================
# Customer 实体类
# ===========================

class Customer:


    def __init__(self, db_connection: sqlite3.Connection = None,
                 customer_id=None, **kwargs):
        self.id = None
        self.name = None
        self.phone = None
        self.id_card = None
        self.created_at = None
        self.updated_at = None

        if db_connection and customer_id is not None:
            self._load_from_db(db_connection, customer_id)
        elif kwargs:
            self._init_from_kwargs(kwargs)

    def _init_from_kwargs(self, kwargs: dict):
        valid_attrs = ['id', 'name', 'phone', 'id_card', 'created_at', 'updated_at']
        for k, v in kwargs.items():
            if k in valid_attrs and v is not None:
                setattr(self, k, v)

    def _load_from_db(self, conn: sqlite3.Connection, customer_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (int(customer_id),))
        row = cursor.fetchone()
        if not row:
            raise CustomerNotFound(f"客户 id={customer_id} 未找到")
        self._map_row(row)

    def _map_row(self, row):
        cols = ['id', 'name', 'phone', 'id_card', 'created_at', 'updated_at']
        for i, c in enumerate(cols):
            setattr(self, c, row[i])

    # ---------- 数据校验 ----------

    def validate(self):
        errors = []

        if not self.name:
            errors.append("姓名为必填")

        if not self.phone:
            errors.append("手机号为必填")
        else:
            if not self._validate_phone():
                errors.append("手机号格式不正确")

        if not self.id_card:
            errors.append("身份证号为必填")
        else:
            if not self._validate_id_card():
                errors.append("身份证号格式不正确")

        return len(errors) == 0, errors

    def _validate_phone(self) -> bool:
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, self.phone) is not None

    def _validate_id_card(self) -> bool:
        pattern_18 = r'^\d{17}[\dXx]$'
        pattern_15 = r'^\d{15}$'
        return (re.match(pattern_18, self.id_card) is not None or
                re.match(pattern_15, self.id_card) is not None)

    # ---------- 写库操作：添加 / 更新 ----------

    def save(self, conn: sqlite3.Connection):
        is_valid, errors = self.validate()
        if not is_valid:
            raise CustomerValidationError("客户数据验证失败: " + "; ".join(errors))

        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.id is None:
            # 新增前检查手机号 / 身份证号是否重复
            cursor.execute("SELECT id FROM customers WHERE phone = ?", (self.phone,))
            if cursor.fetchone():
                raise CustomerDuplicateError(f"手机号 {self.phone} 已存在")

            cursor.execute("SELECT id FROM customers WHERE id_card = ?", (self.id_card,))
            if cursor.fetchone():
                raise CustomerDuplicateError(f"身份证号 {self.id_card} 已存在")

            sql = """
            INSERT INTO customers (name, phone, id_card, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """
            params = (self.name, self.phone, self.id_card, now, now)
            cursor.execute(sql, params)
            self.id = cursor.lastrowid
            self.created_at = now
            self.updated_at = now
        else:
            sql = """
            UPDATE customers
            SET name = ?, phone = ?, id_card = ?, updated_at = ?
            WHERE id = ?
            """
            params = (self.name, self.phone, self.id_card, now, self.id)
            cursor.execute(sql, params)
            self.updated_at = now

        conn.commit()
        return True

    # ---------- 查询功能 ----------

    @classmethod
    def get_all(cls, conn: sqlite3.Connection):
        """查询所有客户"""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY id DESC")
        rows = cursor.fetchall()

        customers = []
        for row in rows:
            c = cls()
            c._map_row(row)
            customers.append(c)
        return customers

    @classmethod
    def search(cls, conn: sqlite3.Connection, keyword: str):
        cursor = conn.cursor()
        pattern = f"%{keyword}%"
        sql = """
        SELECT * FROM customers
        WHERE name LIKE ? OR phone LIKE ? OR id_card LIKE ?
        ORDER BY id DESC
        """
        cursor.execute(sql, (pattern, pattern, pattern))
        rows = cursor.fetchall()

        customers = []
        for row in rows:
            c = cls()
            c._map_row(row)
            customers.append(c)
        return customers

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'id_card': self.id_card,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


# ===========================
# 交互式测试菜单
# ===========================

def test_customer_management():
    import os

    db_path = "interactive_test_customer.db"

    # 每次测试用一个干净的数据库
    if os.path.exists(db_path):
        os.remove(db_path)

    # 初始化客户表
    init_customer_module(db_path)

    conn = sqlite3.connect(db_path)

    try:
        print("=== Customer 类交互式测试（客户管理） ===\n")

        while True:
            print("\n" + "=" * 50)
            print("请选择要执行的操作:")
            print("1. 添加客户")
            print("2. 查询所有客户")
            print("3. 按关键字搜索客户")
            print("0. 退出测试")

            choice = input("\n请输入选择 (0-3): ").strip()

            if choice == "0":
                break

            # ---------- 1. 添加客户 ----------
            elif choice == "1":
                print("\n>>> 添加客户")
                print("-" * 30)

                name = input("姓名: ").strip()
                if not name:
                    name = "测试客户"

                phone = input("手机号: ").strip()
                if not phone:
                    print("手机号不能为空")
                    continue

                id_card = input("身份证号: ").strip()
                if not id_card:
                    print("身份证号不能为空")
                    continue

                try:
                    c = Customer(name=name, phone=phone, id_card=id_card)
                    c.save(conn)
                    print("\n添加成功！客户信息：")
                    print(f"ID: {c.id}")
                    print(f"姓名: {c.name}")
                    print(f"手机号: {c.phone}")
                    print(f"身份证号: {c.id_card}")
                except Exception as e:
                    print(f"添加失败: {e}")

            # ---------- 2. 查询所有客户 ----------
            elif choice == "2":
                print("\n>>> 查询所有客户")
                print("-" * 30)

                customers = Customer.get_all(conn)
                if not customers:
                    print("当前没有任何客户记录")
                    continue

                print(f"客户总数: {len(customers)}")
                for i, c in enumerate(customers, 1):
                    print(f"{i}. ID:{c.id} 姓名:{c.name} 手机:{c.phone} 身份证:{c.id_card}")

            # ---------- 3. 按关键字搜索客户 ----------
            elif choice == "3":
                print("\n>>> 按关键字搜索客户")
                print("-" * 30)

                keyword = input("请输入查询关键字(姓名/手机号/身份证号的一部分): ").strip()
                if not keyword:
                    print("关键字不能为空")
                    continue

                customers = Customer.search(conn, keyword)
                if not customers:
                    print("未找到符合条件的客户")
                    continue

                print(f"搜索结果，共 {len(customers)} 条：")
                for i, c in enumerate(customers, 1):
                    print(f"{i}. ID:{c.id} 姓名:{c.name} 手机:{c.phone} 身份证:{c.id_card}")

            else:
                print("无效选择，请重新输入")

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()
        print("\n数据库连接已关闭")

        keep_db = input("是否保留测试数据库? (y/n): ").strip().lower()
        if keep_db != 'y':
            if os.path.exists(db_path):
                os.remove(db_path)
                print("测试数据库已删除")
        else:
            print(f"测试数据库已保留: {db_path}")


if __name__ == "__main__":
    # 只做客户管理的交互测试，不影响你的主项目 hotel.db
    test_customer_management()
