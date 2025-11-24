import configparser
import os

class Config:
    def __init__(self):
        self.config_dir = "config"
        self.admin_config_file = os.path.join(self.config_dir, "admin.cfg")
        self.weather_config_file = os.path.join(self.config_dir, "weather_api.cfg")
        self._check_configs()

    def _check_configs(self):
        # 检查并创建配置目录
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)

        # 检查并创建配置文件
        if not os.path.exists(self.admin_config_file):
            self._create_admin_config()
        if not os.path.exists(self.weather_config_file):
            self._create_weather_config()

    def _create_admin_config(self):
        config = configparser.ConfigParser()
        config['admin'] = {
            'username': '183大帅哥',
            'password': '183dashuaige'
        }

        try:
            with open(self.admin_config_file, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            print(f"创建管理员配置文件: {self.admin_config_file}")
        except Exception as e:
            print(f"创建管理员配置文件失败: {e}")

    def _create_weather_config(self):
        config = configparser.ConfigParser()
        config['weather_api'] = {
            'api_host': 'your-api-host.re.qweatherapi.com',
            'api_key': 'your-api-key'
        }

        try:
            with open(self.weather_config_file, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            print(f"创建天气API配置文件: {self.weather_config_file}")
        except Exception as e:
            print(f"创建天气API配置文件失败: {e}")