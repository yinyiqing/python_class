import configparser
import os

class Auth():
    def __init__(self, config_file: str = "config/admin.cfg") -> None:
        self.config_file = config_file

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