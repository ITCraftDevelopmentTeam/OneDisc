import toml


def get_version_from_pyproject() -> str:
    # 读取 pyproject.toml 文件
    with open('pyproject.toml', 'r') as file:
        data = toml.load(file)

    # 提取版本号
    version = data.get('project', {}).get('version', None)

    if version:
        return version
    else:
        return "Failed to read version number."


VERSION = get_version_from_pyproject()
SUB_VER = 0
