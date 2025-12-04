# modules/rooms.py
import sqlite3
import random


class Rooms:
    def __init__(self, db):
        self.db = db
        # 1. 确保表存在
        self.create_table_if_not_exists()
        # 2. 检查旧表结构，如果缺少新字段则自动添加 (数据库迁移)
        self.check_and_update_schema()
        # 3. 如果是完全的新库，才生成演示数据
        self.init_sample_data()

    def create_table_if_not_exists(self):
        # 基础建表语句
        sql = '''
            CREATE TABLE IF NOT EXISTS rooms (
                room_number TEXT PRIMARY KEY,
                room_type TEXT NOT NULL,
                has_window INTEGER,
                has_breakfast INTEGER,
                price REAL,
                status TEXT DEFAULT '空闲',
                description TEXT
            )
        '''
        self.db.execute_update(sql)

    def check_and_update_schema(self):
        """自动检测并升级数据库表结构，添加面积和人数列"""
        try:
            # 尝试查询新字段，如果报错说明字段不存在
            self.db.execute_query("SELECT area FROM rooms LIMIT 1")
        except:
            print("正在升级数据库: 添加 area (面积) 字段...")
            try:
                self.db.execute_update("ALTER TABLE rooms ADD COLUMN area INTEGER DEFAULT 23")
            except Exception as e:
                print(f"添加字段失败: {e}")

        try:
            self.db.execute_query("SELECT capacity FROM rooms LIMIT 1")
        except:
            print("正在升级数据库: 添加 capacity (人数) 字段...")
            try:
                self.db.execute_update("ALTER TABLE rooms ADD COLUMN capacity INTEGER DEFAULT 2")
            except Exception as e:
                print(f"添加字段失败: {e}")

    def init_sample_data(self):
        """如果房间表为空，自动生成演示数据"""
        try:
            check_sql = "SELECT COUNT(*) as count FROM rooms"
            result = self.db.execute_query(check_sql)
            if result and result[0]['count'] == 0:
                print("正在初始化演示客房数据...")
                for floor in range(1, 6):  # 1-5层
                    for i in range(1, 21):  # 每层20个
                        room_num = f"{floor}{str(i).zfill(2)}"  # 三位数房号

                        # 随机属性
                        r_type = random.choice(["单人房", "双人房", "豪华大床房"])
                        has_win = random.choice([0, 1])

                        # 根据房型设置面积和人数
                        if r_type == "单人房":
                            area = 23
                            capacity = 1
                            price = 180
                        elif r_type == "双人房":
                            area = 40
                            capacity = 2
                            price = 280
                        else:
                            area = 50
                            capacity = 3
                            price = 450

                        status = '空闲'  # 默认空闲

                        sql = '''INSERT INTO rooms (room_number, room_type, has_window, capacity, area, price, status) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?)'''
                        self.db.execute_update(sql, (room_num, r_type, has_win, capacity, area, price, status))
                print("房间数据生成完毕。")
        except Exception as e:
            print(f"生成房间数据失败: {e}")

    def get_all_rooms(self):
        try:
            # 按房号排序
            sql = "SELECT * FROM rooms ORDER BY room_number ASC"
            data = self.db.execute_query(sql)
            return {'success': True, 'data': data if data else []}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def add_room(self, data):
        try:
            # 插入所有字段
            sql = '''INSERT INTO rooms (room_number, room_type, has_window, capacity, area, price, description, status) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, '空闲')'''
            params = (
                data['room_number'],
                data['room_type'],
                int(data.get('has_window', 0)),
                int(data.get('capacity', 1)),
                int(data.get('area', 23)),
                float(data.get('price', 0)),
                data.get('description', '')
            )
            self.db.execute_update(sql, params)
            return {'success': True, 'message': '房间添加成功'}
        except sqlite3.IntegrityError:
            return {'success': False, 'message': '房间号已存在'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def update_room(self, room_number, data):
        try:
            sql = '''UPDATE rooms SET room_type=?, has_window=?, capacity=?, area=?, price=?, description=? 
                     WHERE room_number=?'''
            params = (
                data['room_type'],
                int(data.get('has_window', 0)),
                int(data.get('capacity', 1)),
                int(data.get('area', 23)),
                float(data.get('price', 0)),
                data.get('description', ''),
                room_number
            )
            self.db.execute_update(sql, params)
            return {'success': True, 'message': '房间信息更新成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def delete_room(self, room_number):
        try:
            check = self.db.execute_query("SELECT status FROM rooms WHERE room_number=?", (room_number,))
            if check and check[0]['status'] != '空闲':
                return {'success': False, 'message': '只能删除空闲状态的房间'}

            self.db.execute_update("DELETE FROM rooms WHERE room_number=?", (room_number,))
            return {'success': True, 'message': '房间已删除'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def update_status(self, room_number, action):
        try:
            room = self.db.execute_query("SELECT status FROM rooms WHERE room_number=?", (room_number,))
            if not room: return {'success': False, 'message': '房间不存在'}

            current_status = room[0]['status']
            new_status = current_status

            if action == 'reserve':
                if current_status != '空闲': return {'success': False, 'message': '房间非空闲'}
                new_status = '已预订'
            elif action == 'checkin':
                new_status = '已入住'
            elif action == 'checkout':
                new_status = '空闲'
            elif action == 'cancel':
                new_status = '空闲'

            self.db.execute_update("UPDATE rooms SET status=? WHERE room_number=?", (new_status, room_number))
            return {'success': True, 'message': f'状态已更新为：{new_status}'}

        except Exception as e:
            return {'success': False, 'message': str(e)}