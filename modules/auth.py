import configparser
import hashlib
import os

class Auth:
    def __init__(
            self,
            config_file: str = "config/admin.cfg",
            permission_file: str = "config/permission.cfg"
    ) -> None:
        self.config_file = config_file
        self.permission_file = permission_file

        self.permissions = {}
        self._load_permissions()

    def _load_admin(self) -> dict[str, str]:
        _config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            _config.read(self.config_file, encoding='utf-8')
            if 'admin' in _config:
                return {
                    'username': _config['admin'].get('username', 'admin'),
                    'password': _config['admin'].get('password', 'admin123')
                }
        return {'username': 'admin', 'password': 'admin123'}

    def _load_permissions(self):
        self.permissions = {}
        if os.path.exists(self.permission_file):
            config = configparser.ConfigParser()
            config.read(self.permission_file, encoding='utf-8')
            if 'departments' in config:
                for dept, perms in config['departments'].items():
                    # 将权限字符串转换为列表
                    perm_list = [p.strip() for p in perms.split(',') if p.strip()]
                    self.permissions[dept] = perm_list

    def verify_admin(self, username: str, password: str) -> bool:
        """
        验证管理员用户名和密码

        Args:
            username: 用户名
            password: 密码

        Returns:
            验证成功返回 True，否则返回 False
        """
        _admin_creds = self._load_admin()
        return username == _admin_creds['username'] and password == _admin_creds['password']

    def verify_employee(self, db, username: str, password: str) -> dict:
        """
        验证员工用户名和密码，并返回权限信息

        Args:
            db: 数据库连接
            username: 用户名
            password: 密码

        Returns:
            dict: 包含验证结果和权限信息
        """
        try:
            # 查询员工信息
            sql = '''
                  SELECT e.employee_id,
                         e.employee_name,
                         e.department_id,
                         d.department_name,
                         e.password_hash
                  FROM employees e
                           LEFT JOIN departments d ON e.department_id = d.department_id
                  WHERE e.username = ?
                    AND e.status = '在职'
                  '''

            result = db.execute_query(sql, (username,))

            if not result:
                return {'success': False, 'message': '用户名或密码错误'}

            employee = result[0]

            # 验证密码
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            if employee['password_hash'] != password_hash:
                return {'success': False, 'message': '用户名或密码错误'}

            # 获取部门权限
            department = employee.get('department_name', '')
            allowed_pages = self.permissions.get(department, [])

            return {
                'success': True,
                'message': '登录成功',
                'employee': {
                    'id': employee['employee_id'],
                    'name': employee['employee_name'],
                    'department': department
                },
                'allowed_pages': allowed_pages
            }

        except Exception as e:
            print(f"员工登录失败: {e}")
            return {'success': False, 'message': '登录失败，请稍后重试'}

    def update_password(self, current_password: str, new_password: str) -> tuple[bool, str]:
        """
        更新管理员密码

        Args:
            current_password: 当前密码
            new_password: 新密码

        Returns:
            (成功状态, 消息)
        """
        _admin_creds = self._load_admin()

        # 验证当前密码
        if current_password != _admin_creds['password']:
            return False, "当前密码错误"

        # 验证新密码长度
        if len(new_password) < 6:
            return False, "新密码长度至少6位"

        # 更新密码
        _config = configparser.ConfigParser()
        _config['admin'] = {
            'username': _admin_creds['username'],
            'password': new_password
        }

        try:
            with open(self.config_file, 'w', encoding='utf-8') as _configfile:
                _config.write(_configfile)
            return True, "密码修改成功"
        except Exception as _e:
            return False, f"密码修改失败: {str(_e)}"

    def check_permission(self, department: str, page: str) -> bool:
        """
        检查部门是否有权限访问某个页面

        Args:
            department: 部门名称
            page: 页面名称 (rooms, orders, customers)

        Returns:
            bool: 是否有权限
        """
        allowed_pages = self.permissions.get(department, [])
        return page in allowed_pages

    def get_department_permissions(self, department: str) -> list:
        """
        获取部门的所有权限

        Args:
            department: 部门名称

        Returns:
            list: 权限列表
        """
        return self.permissions.get(department, [])