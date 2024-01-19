# 斜线命令

自 `0.2.2.2` 后，OneDisc 开始支持使用 Discord 原生的斜线命令

## 指令列表

所有的指令保存在 OneDisc 工作目录下的 `commands.json` 文件（需要您手动创建）， OneDisc 在启动时会读取它并在 Discord 上注册相应命令

这是一个例子：

```json
[
    {
        "name": "cave",
        "guild": 1006772208460365845,
        "description": "回声洞"
    },
    {
        "name": "help",
        "guild": 1006772208460365845,
        "description": "获取指令帮助"
    }
]

```

`commands.json` 是一个数组，每一项的内容是一个对象，包含注册指令时的参数，常用的参数如下：

- `name`: 指令名称
- `description`: 指令简介

事实上，除了 `name` 的参数都是可选的

> 更多参数详见 [此处](https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=commandtree#discord.app_commands.CommandTree.command)

## 开启全局同步


1. 删除指令指令列表的 `guild`、`guilds` 参数（将指令设为全局指令）
2. 将 `system.sync_globally` 配置设为 `true`
3. 重新启动 OneDisc

请注意，Discord 在全局范围同步指令非常缓慢（大约需要一个小时）






