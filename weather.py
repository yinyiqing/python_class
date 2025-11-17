import gzip
import io
import json
import urllib.request
import urllib.parse
import urllib.error

API_KEY = "your_api_key"
API_HOST = "your_api_host"

def get_city_location(city_name):
    geo_api_url = f"https://{API_HOST}/geo/v2/city/lookup"

    params = {
        'location': city_name,
        'key': API_KEY,
        'number': 1
    }
    url = f"{geo_api_url}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url)
        req.add_header('X-QW-Api-Key', API_KEY)
        req.add_header('Accept-Encoding', 'gzip')

        with urllib.request.urlopen(req) as response:
            data = response.read()
            # 解压Gzip
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as gzip_file:
                decompressed_data = gzip_file.read().decode('utf-8')

            geo_data = json.loads(decompressed_data)

            if geo_data.get('code') == '200':
                location_id = geo_data['location'][0]['id']
                city_name_found = geo_data['location'][0]['name']
                print(f"找到城市: {city_name_found}, Location ID: {location_id}")
                return location_id
            else:
                print(f"城市查询失败: {geo_data.get('message', '未知错误')}")
                return None

    except urllib.error.HTTPError as e:
        print(f"HTTP错误 {e.code}: {e.reason}")
        print("请检查: 1. API_HOST是否正确 2. API Key是否有效")
        return None
    except Exception as e:
        print(f"在查询城市ID时发生错误: {e}")
        return None

def get_weather_forecast(location_id, forecast_days=3):
    """
    根据Location ID获取天气预报 - 处理gzip压缩响应
    """
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
    weather_api_url = f"https://{API_HOST}/v7/weather/{api_path}"

    params = {
        'location': location_id,
        'key': API_KEY,
        'lang': 'zh',
        'unit': 'm'
    }
    url = f"{weather_api_url}?{urllib.parse.urlencode(params)}"

    try:
        # 创建请求对象，并添加认证头和接受gzip编码
        req = urllib.request.Request(url)
        req.add_header('X-QW-Api-Key', API_KEY)
        req.add_header('Accept-Encoding', 'gzip')  # 声明接受gzip压缩

        with urllib.request.urlopen(req) as response:
            data = response.read()
            # 解压Gzip
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as gzip_file:
                decompressed_data = gzip_file.read().decode('utf-8')

            weather_data = json.loads(decompressed_data)

            if weather_data.get('code') == '200':
                return weather_data
            else:
                print(f"天气查询失败: {weather_data.get('message', '未知错误')}")
                return None

    except Exception as e:
        print(f"在获取天气数据时发生错误: {e}")
        return None

def get_weather_data(city_name, forecast_days=3):
    """
    根据城市名称获取天气数据

    Args:
        city_name (str): 城市名称
        forecast_days (int): 预报天数，支持 3、7、10、15 天

    Returns:
        dict: 天气数据包，如果获取失败则返回 None
    """
    print(f"正在查询 {city_name} 的天气信息...")

    # 获取城市Location ID
    location_id = get_city_location(city_name)

    if not location_id:
        print("无法获取城市Location ID")
        return None

    # 获取天气预报
    weather_data = get_weather_forecast(location_id, forecast_days)

    if weather_data:
        return weather_data
    else:
        print("无法获取天气信息")
        return None

# 调试信息
def display_weather_info(weather_data):
    if not weather_data:
        return

    print(f"\n=== 天气预报 ===")
    print(f"数据更新时间: {weather_data.get('updateTime', '未知')}")

    if 'now' in weather_data:
        # 实时天气
        now = weather_data['now']
        print(f"\n【实时天气】")
        print(f"天气状况: {now.get('text', '未知')}")
        print(f"当前温度: {now.get('temp', '未知')}°C")
        print(f"体感温度: {now.get('feelsLike', '未知')}°C")
        print(f"湿度: {now.get('humidity', '未知')}%")
        print(f"风向: {now.get('windDir', '未知')}")
        print(f"风力: {now.get('windScale', '未知')}级")

    if 'daily' in weather_data:
        # 预报天气
        print(f"\n【未来预报】")
        for i, day in enumerate(weather_data['daily'][:3]):  # 显示前3天
            print(f"第{i + 1}天: {day.get('fxDate', '未知')}")
            print(f"  白天: {day.get('textDay', '未知')} | 夜间: {day.get('textNight', '未知')}")
            print(f"  温度: {day.get('tempMin', '未知')}°C ~ {day.get('tempMax', '未知')}°C")

if __name__ == "__main__":
    city_name = "北京"
    weather_data = get_weather_data(city_name, 3)

    display_weather_info(weather_data)