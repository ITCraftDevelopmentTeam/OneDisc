import os
import toml


def _pyproject_candidates() -> list[str]:
    """
    返回 pyproject.toml 的候选路径

    源码运行时：优先使用当前文件所在目录（仓库根目录）
    Nuitka 打包运行时：pyproject.toml 作为数据文件被解压到可执行文件/临时目录中，
    此时 __file__ 指向解压目录，因此优先使用 __file__ 所在目录
    """
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyproject.toml"),
        "pyproject.toml",
    ]
    return candidates


def get_version_from_pyproject() -> str:
    # 依次尝试所有候选路径，读取 pyproject.toml 文件
    for path in _pyproject_candidates():
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = toml.load(file)

            # 提取版本号
            version = data.get("project", {}).get("version", None)

            if version:
                return version
        except Exception:
            continue
    return "Failed to read version number."


try:
    VERSION = get_version_from_pyproject()
except Exception:
    VERSION = "FAILED TO GET"
SUB_VER = 0
