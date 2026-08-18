"""pytest 公共配置：保证 import utils 链的依赖环境可用"""
import json
import os
import shutil

import pytest

# 模块级执行（收集阶段即生效）：import utils 链需要 config.json，
# CI/干净环境不存在时创建 dummy，本地已有则不动
if not os.path.exists("config.json"):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "account_token": "dummy_token",
                "system": {"proxy": None, "logger": {"level": 20}},
                "servers": [],
            },
            f,
        )


@pytest.fixture(autouse=True)
def cleanup_cache_dir():
    """清理测试 import 副作用创建的 .cache 目录"""
    yield
    shutil.rmtree(".cache", ignore_errors=True)
