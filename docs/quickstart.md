# 快速开始

## 开始之前

在开始之前，请前往 [下载](download.md) 页面下载对应系统版本及架构的 OneDisc

> 如果「下载」页内提供的是一个压缩包，请在下载完成后将它解压到一个您找得到的目录

如果您需要使用 OneBot V11 中的合并转发功能，请安装 [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)

## 初次运行

> 在 MacOS 或 Linux 中，执行前需要赋予 OneDisc 执行权限
> ```bash
> chmod +x ./onedisc
> ```
> 请将 `./onedisc` 替换为对应的 OneDisc 文件，下同

初次运行（或检测不到 `config.json`）时，OneDisc 会引导您创建一个新的配置文件

```bash
$ ./onedisc
没有可用的配置文件，正在进入配置文件创建向导 ...
机器人令牌：*************
代理服务器（如无需请留空）：http://127.0.0.1:7890
已在 /path/to/your/onedisc/config.json 创建配置
```

### 如何创建 机器人令牌（Bot Token）

机器人令牌将用于 OneDisc 登陆您的机器人的账号

1. 登陆 [Discord Developer Portal](https://discord.com/developers/applications)
2. 点击 `New Application`，填写 Bot 名称，勾选协议并点击 `Create`
3. 在新建的应用程序中，点击 `Bot`，打开 `MESSAGE CONTENT INTENT`、`SERVER MEMBERS INTENT` 开关
4. 点击 `TOKEN` -> `Reset Token`，将新的令牌填入 OneDisc

### 配置文件

在信息填写完成后，OneDisc 将在当前工作目录创建新的配置文件（`config.json`）

```json
{
    "account_token": "--YOUR TOKEN HERE--",
    "system": {
        "proxy": "http://127.0.0.1:7890",
        "logger": {
            "level": 20
        }
    },
    "servers": []
}
```

> 对于配置项的详细信息，请查看 [配置](config.md)

## 启动 OneDisc

在配置完成后，再次启动 OneDisc

出现类似输出代表 OneDisc 已成功启动

```bash
[1919-08-10 11:45:14][__main__ / INFO]: 成功登陆到 OneDisc#9527
```


