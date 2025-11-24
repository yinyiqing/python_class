import configparser
import gzip
import io
import json
import os
import urllib.request
import urllib.parse
import urllib.error

class Weather:
    def __init__(self, config_file: str = "config/weather_api.cfg"):
        self.config_file = config_file
        self.api_host, self.api_key = self._read_weather_config(config_file)

    def _read_weather_config(self, config_file: str) -> tuple:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')

        api_section = config['weather_api']
        api_host = api_section['api_host']
        api_key = api_section['api_key']

        return api_host, api_key

    def _make_api_request(self, url: str) -> dict | None:
        try:
            req = urllib.request.Request(url)
            req.add_header('X-QW-Api-Key', self.api_key)
            req.add_header('Accept-Encoding', 'gzip')

            with urllib.request.urlopen(req) as response:
                data = response.read()
                # 解压Gzip
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as gzip_file:
                    decompressed_data = gzip_file.read().decode('utf-8')

                return json.loads(decompressed_data)

        except Exception as e:
            print(f"API请求失败: {e}")
            return None

    def _get_city_location(self, city_name: str) -> str | None:
        geo_api_url = f"https://{self.api_host}/geo/v2/city/lookup"

        params = {
            'location': city_name,
            'key': self.api_key,
            'number': 1
        }
        url = f"{geo_api_url}?{urllib.parse.urlencode(params)}"

        geo_data = self._make_api_request(url)

        if geo_data and geo_data.get('code') == '200':
            location_id = geo_data['location'][0]['id']
            city_name_found = geo_data['location'][0]['name']
            print(f"找到城市: {city_name_found}, Location ID: {location_id}")
            return location_id
        else:
            print(f"城市查询失败: {geo_data.get('message', '未知错误') if geo_data else '请求失败'}")
            return None

    def _get_weather_forecast(self, location_id: str, forecast_days: int = 3) -> dict | None:
        day_to_api = {
            3: '3d',
            7: '7d',
            10: '10d',
            15: '15d'
        }

        if forecast_days not in day_to_api:
            print(f"不支持的预报天数: {forecast_days}")
            return None

        api_path = day_to_api[forecast_days]
        weather_api_url = f"https://{self.api_host}/v7/weather/{api_path}"

        params = {
            'location': location_id,
            'key': self.api_key,
            'lang': 'zh',
            'unit': 'm'
        }
        url = f"{weather_api_url}?{urllib.parse.urlencode(params)}"

        weather_data = self._make_api_request(url)

        if weather_data and weather_data.get('code') == '200':
            return weather_data
        else:
            print(f"天气查询失败: {weather_data.get('message', '未知错误') if weather_data else '请求失败'}")
            return None

    def get_weather_data(self, city_name: str, forecast_days: int = 3) -> dict | None:
        """
        根据城市名称获取天气数据

        Args:
            city_name: 城市名称
            forecast_days: 预报天数，支持 3、7、10、15 天

        Returns:
            dict: 天气数据包，如果获取失败则返回 None
        """
        print(f"正在查询 {city_name} 的天气信息...")

        # 获取城市 Location ID
        location_id = self._get_city_location(city_name)

        if not location_id:
            print("无法获取城市Location ID")
            return None

        # 获取天气预报
        weather_data = self._get_weather_forecast(location_id, forecast_days)

        if weather_data:
            return weather_data
        else:
            print("无法获取天气信息")
            return None

    def display_weather_info(self, weather_data: dict) -> None:
        """
        显示天气信息（用于调试）

        Args:
            weather_data: 天气数据字典
        """
        if not weather_data:
            return

        print(f"\n=== 天气预报 ===")
        print(f"数据更新时间: {weather_data.get('updateTime', '未知')}")

        if 'now' in weather_data:
            now = weather_data['now']
            print(f"\n【实时天气】")
            print(f"天气状况: {now.get('text', '未知')}")
            print(f"当前温度: {now.get('temp', '未知')}°C")
            print(f"体感温度: {now.get('feelsLike', '未知')}°C")
            print(f"湿度: {now.get('humidity', '未知')}%")
            print(f"风向: {now.get('windDir', '未知')}")
            print(f"风力: {now.get('windScale', '未知')}级")

        if 'daily' in weather_data:
            print(f"\n【未来预报】")
            for i, day in enumerate(weather_data['daily'][:3]):
                print(f"第{i + 1}天: {day.get('fxDate', '未知')}")
                print(f"  白天: {day.get('textDay', '未知')} | 夜间: {day.get('textNight', '未知')}")
                print(f"  温度: {day.get('tempMin', '未知')}°C ~ {day.get('tempMax', '未知')}°C")

    def get_weather_config(self) -> dict:
        """
        获取当前天气API配置

        Returns:
            dict: 包含api_host和api_key的配置字典
        """
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')

            if 'weather_api' not in config:
                return {}

            return {
                'api_host': config['weather_api'].get('api_host', ''),
                'api_key': config['weather_api'].get('api_key', '')
            }

        except Exception as e:
            print(f"读取天气配置失败: {e}")
            return {}

    def update_weather_config(self, api_host: str, api_key: str) -> bool:
        """
        更新天气API配置

        Args:
            api_host: API主机名，必须以 .re.qweatherapi.com 结尾
            api_key: API密钥

        Returns:
            bool: 配置更新成功返回 True，失败返回 False
        """
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')

            if 'weather_api' not in config:
                config['weather_api'] = {}

            config['weather_api']['api_host'] = api_host
            config['weather_api']['api_key'] = api_key

            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                config.write(configfile)

            # 更新当前实例的配置
            self.api_host = api_host
            self.api_key = api_key

            return True
        except Exception as e:
            print(f"更新天气配置失败: {e}")
            return False

if __name__ == "__main__":
    # 创建天气查询实例
    weather = Weather()

    # 获取天气数据
    city_name = "北京"
    weather_data = weather.get_weather_data(city_name, 3)

    # 显示天气信息
    if weather_data:
        weather.display_weather_info(weather_data)
    else:
        print("天气查询失败")