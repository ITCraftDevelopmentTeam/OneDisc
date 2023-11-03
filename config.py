import os.path
import sys
import json


def set_config(conf: dict) -> None:
    global config
    config = conf

def read_local_config() -> dict:
    """
    读取本地配置文件

    Returns:
        dict: OneDisc 配置
    """
    # config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
    if config.get("flatten_system"):
        config["system"] = config.copy()
    return config


def get_config() -> dict:
    """
    读取配置文件。当配置文件不存在时，将进入创建向导

    Returns:
        dict: 配置文件
    """
    try:
        return read_local_config()
    except FileNotFoundError:
        print("没有可用的配置文件，正在进入配置文件创建向导 ...")
        create_wizard()
        sys.exit()
    except json.JSONDecodeError as e:
        print(f"读取配置文件失败：JSON 结构不完整（{e}）")
        sys.exit(1)


def create_wizard() -> None:
    """
    配置文件创建向导
    """
    config = BASE_CONFIG.copy()
    if not (account_token := input("机器人令牌：")):
        create_empty_config()
        print(f"已在 {os.path.abspath('config.json')} 创建空配置")
        return
    config["account_token"] = account_token
    if proxy := input("代理服务器（如无需请留空）："):
        config["system"]["proxy"] = proxy
    # TODO 初始化连接方式
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    print(f"已在 {os.path.abspath('config.json')} 创建配置")

BASE_CONFIG = {
    "account_token": "your token here",
    "system": {
        "proxy": None,
        "logger": {
            "level": 20
        }
    },
    "servers": []
}


def create_empty_config() -> None:
    """
    创建一个空配置
    """
    json.dump(BASE_CONFIG, open("config.json", "w", encoding="utf-8"), indent=4)

config = get_config()
