# Hotel Management System

一个基于 Flask 和 SQLite 的酒店管理系统课程项目。项目提供登录认证、员工与部门管理、客户管理、客房管理、订单管理、经营统计、天气查询和基础完整性校验等功能，适合作为 Python Web 后端、Jinja2 页面渲染和 SQLite 数据库操作的综合练习。

## 功能概览

- 管理员登录与密码修改
- 员工账号登录、部门权限控制
- 部门与员工信息的增删改查
- 客户信息管理与搜索
- 客房信息管理、房态维护
- 订单创建、查询、筛选、付款和导出
- 营业数据统计与图表数据接口
- 和风天气 API 配置与天气查询
- 关键文件完整性校验

## 技术栈

- Python 3
- Flask
- Jinja2
- SQLite
- HTML / CSS / JavaScript

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yinyiqing/python_class.git
cd python_class
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动项目

```bash
python app.py
```

浏览器打开：

```text
http://127.0.0.1:5000
```

首次启动时，程序会自动创建本地配置文件和 `hotel.db` 数据库。

## 默认管理员账号

```text
用户名：admin
密码：admin123
```

登录后可以在系统中修改管理员密码。生产或公开演示前，请务必修改默认密码。

## 配置说明

项目运行时会自动生成以下配置文件：

```text
config/admin.cfg
config/permission.cfg
config/weather_api.cfg
```

这些文件包含管理员账号、部门权限和天气 API 配置，默认不会提交到 Git。天气功能需要在页面或配置文件中填写和风天气 API Host 与 Key。

## 目录结构

```text
.
├── app.py                  # Flask 应用入口与路由
├── fix_db.py               # 数据库修复辅助脚本
├── modules/                # 业务逻辑模块
│   ├── analytics.py        # 统计分析
│   ├── auth.py             # 登录认证与权限
│   ├── config.py           # 配置文件初始化
│   ├── customers.py        # 客户管理
│   ├── database.py         # SQLite 数据库封装
│   ├── departments.py      # 部门管理
│   ├── employee.py         # 员工管理
│   ├── orders.py           # 订单管理
│   ├── rooms.py            # 客房管理
│   ├── security.py         # 文件完整性校验
│   └── weather.py          # 天气查询
├── templates/              # Jinja2 页面模板
├── static/                 # CSS 和 JavaScript 静态资源
├── scripts/                # 数据生成与辅助脚本
├── config/                 # 运行时配置目录
└── requirements.txt        # Python 依赖
```

## 数据库

默认数据库文件为：

```text
hotel.db
```

主要数据表包括：

- `departments`
- `employees`
- `customers`
- `rooms`
- `orders`

数据库会在项目启动时自动初始化。`hotel.db` 属于本地运行数据，默认不提交到 Git。

## 推荐仓库名

当前仓库名 `python_class` 更像课程练习集合，不太能体现项目内容。更贴合的仓库名可以考虑：

- `hotel-management-system`
- `flask-hotel-management`
- `hotel-admin-system`
- `python-hotel-management`

如果希望名字简洁、专业，推荐使用 `flask-hotel-management`。

在 GitHub 修改仓库名：

1. 进入仓库页面
2. 点击 `Settings`
3. 在 `Repository name` 中改为新名称
4. 点击 `Rename`

本地远端地址也需要同步更新：

```bash
git remote set-url origin https://github.com/yinyiqing/flask-hotel-management.git
```

## 注意事项

- 当前项目适合课程作业、学习和本地演示，不建议直接作为生产系统使用。
