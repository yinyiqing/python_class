import sqlite3
import re
from datetime import datetime, date


# ===========================
# 客房 / 订单相关异常
# ===========================

class RoomNotFound(Exception):
    """房间未找到异常"""
    pass


class RoomValidationError(Exception):
    """房间数据验证异常"""
    pass


class RoomDuplicateError(Exception):
    """房间号重复异常"""
    pass


class BookingNotFound(Exception):
    """订单未找到异常"""
    pass


class BookingValidationError(Exception):
    """订单数据验证异常"""
    pass


class BookingStatusError(Exception):
    """订单状态不合法（不能执行对应操作）"""
    pass


# ===========================
# 表结构初始化（只负责房间和订单）
# ===========================

def init_room_module(db_path: str = 'hotel.db'):
    conn = sqlite3.connect(db_path)
    try:
        init_room_tables(conn)
        conn.commit()
    finally:
        conn.close()


def init_room_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # 房间表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number VARCHAR(3) UNIQUE NOT NULL,   -- 三位数房间号，例如 101
        room_type VARCHAR(50) NOT NULL,          -- 房型，例如 单人间 / 双人间
        floor INTEGER,                           -- 楼层
        price DECIMAL(10,2) NOT NULL,            -- 每晚价格
        status VARCHAR(20) DEFAULT '空闲',       -- 空闲 / 已预约 / 已入住 / 停用 等
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 订单表（预约 / 入住 / 退房）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER NOT NULL,                -- 对应 rooms.id
        guest_name VARCHAR(50) NOT NULL,         -- 客人姓名
        guest_phone VARCHAR(20),                 -- 客人电话
        check_in_date DATE NOT NULL,             -- 计划入住日期
        check_out_date DATE NOT NULL,            -- 计划退房日期
        status VARCHAR(20) DEFAULT '已预约',      -- 已预约 / 已入住 / 已退房 / 已取消
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES rooms (id)
    )
    ''')


# ===========================
# Room 房间实体类
# ===========================

class Room:

    def __init__(self, db_connection: sqlite3.Connection = None,
                 room_identifier=None, **kwargs):
        self.id = None
        self.room_number = None   # 三位数房间号
        self.room_type = None     # 房型
        self.floor = None         # 楼层
        self.price = None         # 每晚价格
        self.status = '空闲'      # 空闲 / 已预约 / 已入住 / 停用
        self.description = None
        self.created_at = None
        self.updated_at = None

        if db_connection and room_identifier is not None:
            self._load_from_db(db_connection, room_identifier)
        elif kwargs:
            self._init_from_kwargs(kwargs)

    def _init_from_kwargs(self, kwargs: dict):
        """从关键字参数初始化房间对象"""
        valid_attrs = [
            'id', 'room_number', 'room_type', 'floor', 'price',
            'status', 'description', 'created_at', 'updated_at'
        ]
        for k, v in kwargs.items():
            if k in valid_attrs and v is not None:
                setattr(self, k, v)

        # 统一把房间号补齐为三位（例如 '1' -> '001'）
        if self.room_number is not None:
            self.room_number = str(self.room_number).zfill(3)

    def _load_from_db(self, conn: sqlite3.Connection, room_identifier):
        cursor = conn.cursor()

        if isinstance(room_identifier, int):
            cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_identifier,))
        else:
            room_no = str(room_identifier).zfill(3)
            cursor.execute("SELECT * FROM rooms WHERE room_number = ?", (room_no,))

        row = cursor.fetchone()
        if not row:
            raise RoomNotFound(f"房间 '{room_identifier}' 未找到")

        self._map_row(row)

    def _map_row(self, row):
        cols = [
            'id', 'room_number', 'room_type', 'floor', 'price',
            'status', 'description', 'created_at', 'updated_at'
        ]
        for i, c in enumerate(cols):
            setattr(self, c, row[i])

    def validate(self):
        errors = []

        # 房间号
        if not self.room_number:
            errors.append("房间号为必填")
        else:
            if not re.match(r'^\d{3}$', str(self.room_number)):
                errors.append("房间号必须为三位数字，例如 101")

        # 房型
        if not self.room_type:
            errors.append("房型为必填")

        # 价格
        if self.price is None:
            errors.append("房价为必填")
        else:
            try:
                p = float(self.price)
                if p < 0:
                    errors.append("房价不能为负数")
            except ValueError:
                errors.append("房价必须是数字")

        return len(errors) == 0, errors

    def save(self, conn: sqlite3.Connection):
        is_valid, errors = self.validate()
        if not is_valid:
            raise RoomValidationError("房间数据验证失败: " + "; ".join(errors))

        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.id is None:
            # 新增前检查房间号是否重复
            cursor.execute(
                "SELECT id FROM rooms WHERE room_number = ?",
                (self.room_number,)
            )
            if cursor.fetchone():
                raise RoomDuplicateError(f"房间号 {self.room_number} 已存在")

            sql = """
            INSERT INTO rooms
            (room_number, room_type, floor, price, status, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                self.room_number, self.room_type, self.floor, self.price,
                self.status, self.description, now, now
            )
            cursor.execute(sql, params)
            self.id = cursor.lastrowid
            self.created_at = now
            self.updated_at = now
        else:
            # 更新
            sql = """
            UPDATE rooms
            SET room_number = ?, room_type = ?, floor = ?, price = ?,
                status = ?, description = ?, updated_at = ?
            WHERE id = ?
            """
            params = (
                self.room_number, self.room_type, self.floor, self.price,
                self.status, self.description, now, self.id
            )
            cursor.execute(sql, params)
            self.updated_at = now

        conn.commit()
        return True

    def delete(self, conn: sqlite3.Connection):
        cursor = conn.cursor()

        if self.status not in ('空闲', '停用'):
            raise RoomValidationError("只有空闲或停用状态的房间可以删除")

        # 检查是否有未完成订单
        cursor.execute("""
        SELECT COUNT(1)
        FROM bookings
        WHERE room_id = ? AND status IN ('已预约', '已入住')
        """, (self.id,))
        cnt = cursor.fetchone()[0]
        if cnt > 0:
            raise RoomValidationError("该房间存在未完成的预约/入住记录，不能删除")

        cursor.execute("DELETE FROM rooms WHERE id = ?", (self.id,))
        conn.commit()

    def to_dict(self) -> dict:
        """转换为字典，方便调试 / 接口返回"""
        return {
            'id': self.id,
            'room_number': self.room_number,
            'room_type': self.room_type,
            'floor': self.floor,
            'price': float(self.price) if self.price is not None else None,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    # --------- 房间类方法（查询） ---------

    @classmethod
    def get_all(cls, conn: sqlite3.Connection, status: str = None):
        cursor = conn.cursor()
        sql = "SELECT * FROM rooms"
        params = []
        if status:
            sql += " WHERE status = ?"
            params.append(status)
        sql += " ORDER BY room_number"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        rooms = []
        for row in rows:
            r = cls()
            r._map_row(row)
            rooms.append(r)
        return rooms

    @classmethod
    def get_by_number(cls, conn: sqlite3.Connection, room_number: str):
        """按房间号获取房间对象"""
        return cls(conn, room_number)


# ===========================
# Booking 订单实体类
# ===========================

class Booking:
    def __init__(self, db_connection: sqlite3.Connection = None,
                 booking_id=None, **kwargs):
        self.id = None
        self.room_id = None
        self.guest_name = None
        self.guest_phone = None
        self.check_in_date = None
        self.check_out_date = None
        self.status = '已预约'    # 已预约 / 已入住 / 已退房 / 已取消
        self.created_at = None
        self.updated_at = None

        if db_connection and booking_id is not None:
            self._load_from_db(db_connection, booking_id)
        elif kwargs:
            self._init_from_kwargs(kwargs)

    def _init_from_kwargs(self, kwargs: dict):
        valid_attrs = [
            'id', 'room_id', 'guest_name', 'guest_phone',
            'check_in_date', 'check_out_date', 'status',
            'created_at', 'updated_at'
        ]
        for k, v in kwargs.items():
            if k in valid_attrs and v is not None:
                setattr(self, k, v)

    def _load_from_db(self, conn: sqlite3.Connection, booking_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id = ?", (int(booking_id),))
        row = cursor.fetchone()
        if not row:
            raise BookingNotFound(f"订单 '{booking_id}' 未找到")
        self._map_row(row)

    def _map_row(self, row):
        cols = [
            'id', 'room_id', 'guest_name', 'guest_phone',
            'check_in_date', 'check_out_date', 'status',
            'created_at', 'updated_at'
        ]
        for i, c in enumerate(cols):
            setattr(self, c, row[i])

    def validate(self):
        errors = []

        if not self.room_id:
            errors.append("room_id 必须指定")
        if not self.guest_name:
            errors.append("客人姓名为必填")
        if not self.check_in_date:
            errors.append("入住日期为必填")
        if not self.check_out_date:
            errors.append("退房日期为必填")

        # 日期格式
        for attr, name in [('check_in_date', '入住日期'), ('check_out_date', '退房日期')]:
            val = getattr(self, attr)
            if val:
                try:
                    if isinstance(val, str):
                        datetime.strptime(val, '%Y-%m-%d')
                except ValueError:
                    errors.append(f"{name}格式应为 YYYY-MM-DD")

        # 入住 <= 退房
        if self.check_in_date and self.check_out_date:
            ci = self.check_in_date
            co = self.check_out_date
            if isinstance(ci, str):
                ci = datetime.strptime(ci, '%Y-%m-%d').date()
            if isinstance(co, str):
                co = datetime.strptime(co, '%Y-%m-%d').date()
            if ci > co:
                errors.append("退房日期不能早于入住日期")

        return len(errors) == 0, errors

    def save(self, conn: sqlite3.Connection):
        """保存订单：新增 / 更新"""
        is_valid, errors = self.validate()
        if not is_valid:
            raise BookingValidationError("订单数据验证失败: " + "; ".join(errors))

        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.id is None:
            sql = """
            INSERT INTO bookings
            (room_id, guest_name, guest_phone, check_in_date, check_out_date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                self.room_id, self.guest_name, self.guest_phone,
                self.check_in_date, self.check_out_date,
                self.status, now, now
            )
            cursor.execute(sql, params)
            self.id = cursor.lastrowid
            self.created_at = now
            self.updated_at = now
        else:
            sql = """
            UPDATE bookings
            SET room_id = ?, guest_name = ?, guest_phone = ?,
                check_in_date = ?, check_out_date = ?, status = ?, updated_at = ?
            WHERE id = ?
            """
            params = (
                self.room_id, self.guest_name, self.guest_phone,
                self.check_in_date, self.check_out_date,
                self.status, now, self.id
            )
            cursor.execute(sql, params)
            self.updated_at = now

        conn.commit()
        return True

    # ========= 业务操作：1~4 功能 =========

    @classmethod
    def reserve_room(cls, conn: sqlite3.Connection,
                     room_number: str,
                     guest_name: str,
                     guest_phone: str,
                     check_in_date: str,
                     check_out_date: str):
        # 找房间
        room = Room(conn, room_number)
        if room.status != '空闲':
            raise BookingStatusError(f"房间当前状态为 {room.status}，不能预约")

        # 创建订单对象并保存
        booking = cls(
            room_id=room.id,
            guest_name=guest_name,
            guest_phone=guest_phone,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            status='已预约'
        )
        booking.save(conn)

        # 更新房间状态
        room.status = '已预约'
        room.save(conn)

        return booking

    def cancel(self, conn: sqlite3.Connection):
        if self.status != '已预约':
            raise BookingStatusError("只有已预约状态的订单可以取消")

        self.status = '已取消'
        self.save(conn)

        # 恢复房间状态为空闲
        room = Room(conn, self.room_id)
        room.status = '空闲'
        room.save(conn)

    def check_in(self, conn: sqlite3.Connection):
        if self.status != '已预约':
            raise BookingStatusError("只有已预约状态的订单可以办理入住")

        self.status = '已入住'
        self.save(conn)

        room = Room(conn, self.room_id)
        room.status = '已入住'
        room.save(conn)

    def check_out(self, conn: sqlite3.Connection):
        if self.status != '已入住':
            raise BookingStatusError("只有已入住状态的订单可以退房")

        self.status = '已退房'
        self.save(conn)

        room = Room(conn, self.room_id)
        room.status = '空闲'
        room.save(conn)

    @classmethod
    def get_active_bookings(cls, conn: sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM bookings
        WHERE status IN ('已预约', '已入住')
        ORDER BY id DESC
        """)
        rows = cursor.fetchall()

        bookings = []
        for row in rows:
            b = cls()
            b._map_row(row)
            bookings.append(b)
        return bookings

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'room_id': self.room_id,
            'guest_name': self.guest_name,
            'guest_phone': self.guest_phone,
            'check_in_date': self.check_in_date,
            'check_out_date': self.check_out_date,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

if __name__ == "__main__":
    import os

    db_path = "hotel_room_demo.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # 初始化房间 / 订单表
    init_room_module(db_path)

    conn = sqlite3.connect(db_path)

    # 先增加两个房间，演示 4/5/6 功能
    r1 = Room(room_number="101", room_type="单人间", floor=1, price=300)
    r1.save(conn)

    r2 = Room(room_number="102", room_type="双人间", floor=1, price=420)
    r2.save(conn)

    print("当前房间：")
    for r in Room.get_all(conn):
        print(r.to_dict())

    print("\n--- 测试预约 / 入住 / 退房 ---")
    booking = Booking.reserve_room(
        conn,
        room_number="101",
        guest_name="张三",
        guest_phone="13800000000",
        check_in_date="2025-01-01",
        check_out_date="2025-01-03"
    )
    print("预约成功：", booking.to_dict())

    # 入住
    booking.check_in(conn)
    print("入住后订单状态：", Booking(conn, booking.id).status)

    # 退房
    booking.check_out(conn)
    print("退房后订单状态：", Booking(conn, booking.id).status)

    conn.close()
    print("\n演示结束。")
