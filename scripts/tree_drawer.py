"""
显示文件夹结构
"""

from pathlib import Path

# 颜色定义
RESET = '\033[0m'
BOLD = '\033[1m'
BLUE = '\033[94m'  # 文件夹
GREEN = '\033[92m'  # Python文件
YELLOW = '\033[93m'  # 其他文件
CYAN = '\033[96m'  # CSS/JS文件
MAGENTA = '\033[95m'  # HTML文件
RED = '\033[91m'  # 错误信息

def get_file_color(file_path):
    if file_path.is_dir():
        return BLUE

    suffix = file_path.suffix.lower()
    if suffix in ['.py']:
        return GREEN
    elif suffix in ['.html', '.htm']:
        return MAGENTA
    elif suffix in ['.css', '.js']:
        return CYAN
    elif suffix in ['.json', '.yml', '.yaml', '.xml', '.md', '.txt']:
        return YELLOW
    else:
        return YELLOW

def should_exclude(path):
    exclude_patterns = ['.venv', '.idea', '__pycache__', '.git', '.vscode', '.vs', '.pytest_cache']
    path_str = str(path)

    for pattern in exclude_patterns:
        if pattern in path_str:
            return True

    # 排除常见的缓存和编译文件
    if path.suffix in ['.pyc', '.pyo', '.pyd', '.so']:
        return True

    return False

def find_project_root():
    current_path = Path('.').resolve()

    # 常见的项目根目录标记文件
    root_indicators = [
        '.git',
        'requirements.txt',
        'setup.py',
        'pyproject.toml',
        'Pipfile',
        'environment.yml',
        'app.py',
        'main.py',
        'manage.py',
        'README.md',
        'LICENSE'
    ]

    # 从当前目录向上查找
    while current_path != current_path.parent:  # 直到根目录
        for indicator in root_indicators:
            if (current_path / indicator).exists():
                return current_path
        current_path = current_path.parent

    # 如果没有找到标记文件，返回当前目录
    return Path('.').resolve()

def print_tree(directory, level=0, is_last=True, prefix=''):
    # 检查是否应该排除整个目录
    if should_exclude(directory):
        return

    # 构建当前层级的显示前缀
    if level == 0:
        connector = ''
    else:
        connector = '└── ' if is_last else '├── '

    # 打印当前目录/文件
    if level == 0:
        print(f"{BOLD}{BLUE}{directory.name}/{RESET}")
    else:
        color = BLUE if directory.is_dir() else get_file_color(directory)
        print(f"{prefix}{connector}{color}{directory.name}{RESET}")

    # 如果是文件，直接返回
    if not directory.is_dir():
        return

    # 获取目录内容并排序，文件夹在前，文件在后
    try:
        items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

        # 过滤排除的项目
        items = [item for item in items if not should_exclude(item)]

        # 递归处理子项
        for index, item in enumerate(items):
            is_last_item = (index == len(items) - 1)
            new_prefix = prefix + ('    ' if is_last else '│   ')

            print_tree(item, level + 1, is_last_item, new_prefix)

    except PermissionError:
        print(f"{prefix}    └── {RED}[权限被拒绝]{RESET}")
    except Exception as e:
        print(f"{prefix}    └── {RED}[错误: {str(e)}]{RESET}")

def main():
    # 自动检测项目根目录
    project_root = find_project_root()

    print(f"{BOLD}项目根目录: {BLUE}{project_root}{RESET}")
    print(f"{BOLD}项目目录树:{RESET}")
    print()

    # 打印目录树
    print_tree(project_root)

    print()
    print(f"{BOLD}颜色说明:{RESET}")
    print(f"{BLUE}蓝色{RESET}: 文件夹")
    print(f"{GREEN}绿色{RESET}: Python文件")
    print(f"{MAGENTA}洋红色{RESET}: HTML文件")
    print(f"{CYAN}青色{RESET}: CSS/JS文件")
    print(f"{YELLOW}黄色{RESET}: 其他文件")

if __name__ == '__main__':
    main()