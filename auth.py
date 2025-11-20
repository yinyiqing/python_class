import configparser
import os

class Auth():
    def __init__(self, config_file: str = "admin.cfg"):
        self.config_file = config_file
        self._check_config()

    def _check_config(self):
        if not os.path.exists(self.config_file):
            _config = configparser.ConfigParser()
            _config['admin'] = {
                'username': 'admin',
                'password': 'admin123'
            }

            with open(self.config_file, 'w', encoding='utf-8') as _configfile:
                _config.write(_configfile)

    def _load_admin(self):
        _config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            _config.read(self.config_file, encoding='utf-8')
            if 'admin' in _config:
                return {
                    'username': _config['admin'].get('username', 'admin'),
                    'password': _config['admin'].get('password', 'admin123')
                }
        return {'username': 'admin', 'password': 'admin123'}

    def verify_admin(self, username, password):
        _admin_creds = self._load_admin()
        return username == _admin_creds['username'] and password == _admin_creds['password']