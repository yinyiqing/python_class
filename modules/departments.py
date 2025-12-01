class Departments:
    def __init__(self, db):
        self.db = db

    def get_all_departments(self) -> dict:
        """获取所有部门列表"""
        try:
            sql = '''
                  SELECT department_id, \
                         department_name, \
                         description,
                         created_at, \
                         updated_at
                  FROM departments
                  ORDER BY department_id \
                  '''
            departments = self.db.execute_query(sql)

            return {
                'success': True,
                'data': departments,
                'message': f'获取到{len(departments)}个部门'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取部门列表失败: {str(e)}'
            }

    def create_department(self, department_data: dict) -> tuple:
        """
        创建新部门
        返回: (success: bool, message: str)
        """
        try:
            sql = '''
                  INSERT INTO departments (department_id, department_name, description)
                  VALUES (?, ?, ?) \
                  '''

            self.db.execute_update(sql, (
                department_data.get('department_id'),
                department_data.get('department_name'),
                department_data.get('description', '')
            ))

            return True, "部门创建成功"
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE constraint failed" in error_msg:
                if "departments.department_id" in error_msg:
                    return False, "部门ID已存在"
                elif "departments.department_name" in error_msg:
                    return False, "部门名称已存在"
            return False, f"创建部门失败：{error_msg}"

    def update_department(self, department_id: str, update_data: dict) -> tuple:
        """
        更新部门信息
        返回: (success: bool, message: str)
        """
        try:
            # 检查部门是否存在
            check_sql = "SELECT department_id FROM departments WHERE department_id = ?"
            result = self.db.execute_query(check_sql, (department_id,))
            if not result:
                return False, "部门不存在"

            # 构建更新语句
            set_fields = []
            params = []

            for field, value in update_data.items():
                if value is not None:
                    set_fields.append(f"{field} = ?")
                    params.append(value)

            if not set_fields:
                return False, "没有需要更新的数据"

            params.append(department_id)
            sql = f"UPDATE departments SET {', '.join(set_fields)} WHERE department_id = ?"

            result = self.db.execute_update(sql, tuple(params))

            if result and result > 0:
                return True, "部门更新成功"
            else:
                return False, "部门更新失败"
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE constraint failed" in error_msg and "departments.department_name" in error_msg:
                return False, "部门名称已存在"
            return False, f"更新部门失败：{error_msg}"

    def delete_department(self, department_id: str) -> tuple:
        """
        删除部门
        返回: (success: bool, message: str)
        """
        try:
            # 检查部门是否存在
            check_sql = "SELECT department_id FROM departments WHERE department_id = ?"
            result = self.db.execute_query(check_sql, (department_id,))
            if not result:
                return False, "部门不存在"

            # 检查是否有员工属于该部门
            count_sql = "SELECT COUNT(*) as count FROM employees WHERE department_id = ?"
            result = self.db.execute_query(count_sql, (department_id,))

            if result and result[0]['count'] > 0:
                return False, "该部门下还有员工，无法删除。请先转移或删除相关员工。"

            # 删除部门
            delete_sql = "DELETE FROM departments WHERE department_id = ?"
            result = self.db.execute_update(delete_sql, (department_id,))

            if result and result > 0:
                return True, "部门删除成功"
            else:
                return False, "部门删除失败"
        except Exception as e:
            return False, f"删除部门失败：{str(e)}"

    def get_department_by_id(self, department_id: str) -> dict:
        """根据ID获取部门信息"""
        sql = '''
              SELECT department_id, department_name, description, created_at, updated_at
              FROM departments
              WHERE department_id = ? \
              '''
        result = self.db.execute_query(sql, (department_id,))
        return result[0] if result else None