import sqlite3
import os


def fix_database():
    db_path = 'hotel.db'

    if not os.path.exists(db_path):
        print("未找到 hotel.db，无需修复。")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("正在连接数据库...")

        # 1. 删除相关的触发器 (防止残留)
        triggers = ['update_employees_timestamp', 'set_termination_date']
        for trigger in triggers:
            try:
                cursor.execute(f"DROP TRIGGER IF EXISTS {trigger}")
                print(f"已清理触发器: {trigger}")
            except Exception as e:
                print(f"清理触发器 {trigger} 失败: {e}")

        # 2. 删除出问题的 employees 表
        # 注意：这只会删除员工数据，客户(customers)和部门(departments)数据不受影响
        try:
            cursor.execute("DROP TABLE IF EXISTS employees")
            print("已成功删除损坏的 employees 表。")
        except Exception as e:
            print(f"删除表失败: {e}")

        conn.commit()
        conn.close()
        print("\n=== 修复完成 ===")
        print("请现在运行 app.py，系统会自动重建正确的员工表。")

    except Exception as e:
        print(f"连接数据库出错: {e}")


if __name__ == '__main__':
    fix_database()