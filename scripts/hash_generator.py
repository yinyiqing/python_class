"""
计算关键文件哈希值
每次更改关键文件后都应重新运行此脚本，否则程序无法通过文件完整性验证
"""

from datetime import datetime
import hashlib
import json
import os

FILES = [
    "app.py",

    "modules/auth.py",
    # "modules/config.py",
    "modules/database.py",
    "modules/departments.py",
    "modules/employee.py",
    "modules/weather.py",

    "static/css/login.css",
    "static/css/style.css",
    "static/css/theme.css",
    "static/js/common.js",
    "static/js/employees.js",
    "static/js/login.js",

    "templates/analytics.html",
    "templates/base.html",
    "templates/customers.html",
    "templates/dashboard.html",
    "templates/employees.html",
    "templates/login.html",
    "templates/orders.html",
    "templates/rooms.html",
    "templates/security.html",
    "templates/theme.html",
    "templates/weather.html"
]

def calculate_file_hash(filepath):
    full_path = os.path.join("..", filepath)
    with open(full_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def generate_hashes():
    hashes = {}
    for filepath in FILES:
        try:
            hashes[filepath] = calculate_file_hash(filepath)
            print(f"{filepath}")
        except Exception as e:
            print(f"{filepath} - {e}")

    return hashes

def save_hashes_json(hashes):
    json_content = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "file_count": len(hashes)
        },
        "file_hashes": hashes
    }

    with open("../config/hashes.json", "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    hashes = generate_hashes()
    save_hashes_json(hashes)