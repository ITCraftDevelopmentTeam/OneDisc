# 配置

在首次启动过后，OneDisc 会自动创建一个新的配置文件（`config.json`）

```json
{
    "account_token": "your token here",
    "system": {
        "proxy": "http://127.0.0.1:7890",
        "logger": {
            "level": 20
        }
    },
    "servers": []
}

```

## 机器人令牌（`account_token`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 字符串     | 是   | 无         |

机器人令牌，用于 OneDisc 登陆 Bot 的账号

参见：[如何创建 机器人令牌（Bot Token）](quickstart.md#如何创建-机器人令牌-bot-token)

## 系统设置（`system`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 对象       | 是   | 无         |

OneDisc 高级设置（无特殊需要不建议更改）

### 连接 Discord 时使用的代理（`proxy`）

| 类型        | 必须 | 默认值     |
|:-----------:|:----:|:----------:|
| 字符串 / 空 | 是   | 无         |

### 在群管理员变动事件中使用服务器ID（`guild_id_for_group_admin`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 布尔       | 否   | `false`    |

启用后，将在群组管理员变动事件（`notice.group_admin`）中使用群组 ID 填入 `group_id` 字段，且群组管理员变动时只会触发一次事件

禁用后，群组管理员变动时将在每个频道触发一次 `notice.group_admin` 事件

### 仅在文字频道触发群管理员变动事件（`group_admin_text_channel`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 布尔       | 否   | `false`    |

启用后，在群组管理员变动时，将不在非文字频道触发 `notice.group_admin` 事件

仅在 `guild_id_for_group_admin` 为 `false` 时有效

### 是否启用群管理员变动事件（`enable_group_admin`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 布尔       | 否   | `true`     |

### 日志记录工具配置（`logger`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 对象       | 否   | `{"level": 20}` |

配置日志记录工具时的参数，可参考 [Python3 文档](https://docs.python.org/zh-cn/3/library/logging.html?highlight=logging%20basicconfig#logging.basicConfig)

### 合并转发图片类型（`node_image_type`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 字符串     | 否   | `jpg`      |

将合并转发消息渲染为图片缓存并发送时使用的图片类型


### 数据库地址（`database`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 字符串      | 否   | `sqlite+aiosqlite:///:memory:` |

OneDisc 缓存消息使用的数据库地址

参考 [Engine Configuration — SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls)

不支持自动创建数据库

> 目前可执行版只支持 SQLite3，源码版使用其他数据库需要手动安装依赖

### 使用静态表情（`use_static_face`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 布尔       | 否   | `false`                |

如启用，将在发送 `CQ:face` 时使用 QQ 表情包静态图

### 忽略不需要的实参（`ignore_unneeded_args`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 布尔       | 否   | `true`                 |

是否忽略动作请求中不需要的参数

如为 `false`，将在处理请求中发现不被动作需要的参数时返回 `10004 - Unsupported Param`

### 转义 `text` 段中的 MarkDown（`escape_markdown`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:--------------------:|
| 布尔       | 否   | `false`               |


### 默认最大成员数（`default_max_member_count`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 数字       | 否   | `-1`                   |

`get_group_info` (OneBot V11) 及有关接口 `max_member_count` 字段内容

### 位置消息段默认描述（`location_default_content`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 字符串     | 否   | `机器人向你发送了一个位置` |

### 合并转发换行符替换内容（`node_linebreak_replacement`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 字符串     | 否   | `<br>`                 |

解析合并转发消息节点时用于替换换行符（`\n`）内容

### wkhtmltopdf 路径（`wkhtmltopdf`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 字符串/空  | 否   | `null`                 |

wkhtmltopdf 可执行程序路径

### 是否可以发送语音（`can_send_record`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 布尔       | 否   | `false`                |

`can_send_record` (OneBot V11) 接口中 `yes` 字段内容

### 反向 WebSocket 最大消息大小（`max_message_size`）

| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 数字       | 否   | `1048576`               |

OneBot V11 和 OneBot V12 的反向 WebSocket 连接中最大消息大小，单位为字节，默认 1MB（即 `2^20`）

如果在使用过程中出现以下错误请考虑增大这一配置项的数值: 

```python
websockets.exceptions.ConnectionClosedError: sent 1009 (message too big); no close frame received
```

### 跳过参数类型检查（`skip_params_type_checking`）


| 类型       | 必须 | 默认值                 |
|:----------:|:----:|:----------------------:|
| 布尔       | 否   | `false`                |

### 心跳元事件设置（`heartbeat`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 对象       | 否   | `{"enable": true, 'interval': 5000}` |

OneBot V12 心跳元事件设置

#### 心跳事件开关（`enable`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 布尔       | 否   | `true`     |

是否启用心跳元事件

#### 心跳事件触发间隔（`interval`）


| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 数字       | 否   | `5000`     |

心跳元事件触发间隔（单位：毫秒）

### 下载重试次数（`download_max_retry_count`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 数字       | 否   | `0`        |

`upload_file` 及相关动作下载出错时的重试次数

### 隔离动作（`action_isolation`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 布尔       | 否   | `false`     |

启用后将禁止跨协议访问动作

### 是否忽略自身事件（`ignore_self_events`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 布尔       | 否   | `true`     |

如果此项为`true`，将忽略由 Bot 自身触发的事件

### 允许罢工（`allow_strike`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 布尔       | 否   | `false`    |

如果此项为`true`，将在请求每次执行动作时有`10%`的概率返回`36000`（I Am Tired）错误

### 在事件中使用空字符串代替不支持的子类型（`use_empty_for_unsupported_subtype`）

| 类型      | 必须 | 默认值           |
|:---------:|:----:|:----------------:|
| 布尔      | 否   | `true`           |

在事件上报中将不支持的子类型替换为空字符串（`""`）

如在`channel_message_delete`事件中，由于`discord.py`限制，无法判断消息为主动删除还是被管理员删除，当`use_empty_for_unsupported_subtype`为`false`时，这个事件的`sub_type`将被填入`recall`（发送者主动删除）；当`use_empty_for_unsupported_subtype`为`true`时，这个事件的`sub_type`将被填入空字符串


### 默认私聊消息子类型（`default_message_sub_type`）

| 类型      | 必须 | 默认值           |
|:---------:|:----:|:----------------:|
| 字符串    | 否   | `friend`          |

OneBot V11 中，私聊消息事件（`message.private`）的 `sub_type` 字段内容

### 缓存优先（`cache_first`）

| 类型      | 必须 | 默认值           |
|:---------:|:----:|:----------------:|
| 布尔      | 否   | `false`          |

此项为 `true` 时，当同一文件同时存在于缓存 URL 索引和本地储存库（`.cache/files`）时，优先保留缓存（删除本地储存文件）

此项为 `false` 时，将删除缓存库的索引


### 在启动时检查更新（`check_update`）

| 类型      | 必须 | 默认值           |
|:---------:|:----:|:----------------:|
| 布尔      | 否   | `true`          |

### 在全局范围同步命令（`sync_globally`）

| 类型      | 必须 | 默认值           |
|:---------:|:----:|:----------------:|
| 布尔      | 否   | `false`          |

这可能需要一些时间（大约为一个小时）

### 指令响应超时时的提示（`command_timeout_message`）

| 类型      | 必须 | 默认值               |
|:---------:|:----:|:--------------------:|
| 字符串    | 否   | `timeout` |

### 指令前缀（`prefix`）

| 类型      | 必须 | 默认值               |
|:---------:|:----:|:--------------------:|
| 字符串    | 否   | `/` |

在收到指令调用请求后添加的指令前缀

### 同步指令的频道（`sync_guilds`）

| 类型      | 必须 | 默认值           |
|:---------:|:----:|:----------------:|
| 数组      | 否   | `[]`          |

### 是否忽略不支持的消息段（`ignore_unsupported_segment`）

| 类型      | 必须 | 默认值           |
|:---------:|:----:|:----------------:|
| 布尔      | 否   | `false`          |

如为`false`，将在发送消息并解析到不支持的消息段时返回 `10005` 错误

### 启动完成日志提示内容（`started_text`）

| 类型      | 必须 | 默认值               |
|:---------:|:----:|:--------------------:|
| 字符串    | 否   | `OneDisc 已成功启动` |

OneDisc 完成启动后打印的日志的内容

### 是否启用两级群组事件（`enable_channel_event`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 布尔       | 否   | `false`    |

如果此项为 `true`，将以 `message.channel` 事件推送消息

如为 `false` 将以 `message.group` 事件推送消息

## 连接方式（`servers`）

| 类型       | 必须 | 默认值     |
|:----------:|:----:|:----------:|
| 数组       | 是   | 无         |

设置 OneDisc 的连接方式，可以创建多个连接方式

### OneBot V12

<details>
<summary>HTTP</summary>

```json
{
    "type": "http",
    "host": "0.0.0.0",
    "port": 8080,
    "protocol_version": 12,
    "access_token": null,
    "event_enabled": false,
    "event_buffer_size": 0
}
```

| 项目                | 类型      | 必须 | 默认值    | 备注                 |
|---------------------|-----------|------|-----------|----------------------|
| `type`              | 字符串    | 是   | 无        | 连接的类型，为`http` |
| `protocol_version`  | 数字      | 否   | `12`      | 协议版本，为 `12`    |
| `host`              | 字符串    | 否   | `0.0.0.0` | HTTP 服务器 IP       |
| `port`              | 数字      | 否   | `8080`    | HTTP 服务器端口      |
| `access_token`      | 字符串/空 | 是   | `null`    | 访问令牌             |
| `event_enabled`     | 布尔      | 否   | `false`   | 是否启用 `get_latest_events` 元动作 |
| `event_buffer_size` | 数字      | 否   | `0`       | 事件缓冲区大小       |
</details>

<details>
<summary>HTTP WebHook</summary>

```json
{
    "type": "http-webhook",
    "url": null,
    "protocol_version": 12,
    "access_token": null,
    "timeout": 0
}
```

| 项目               | 类型         | 必须 | 默认值     | 说明                       |
|--------------------|--------------|------|------------|----------------------------|
| `type`             | 字符串       | 是   | 无         | 连接类型，为`http-webhook` |
| `protocol_version` | 数字         | 否   | `12`      | 协议版本，为 `12`    |
| `url`              | 字符串       | 是   | 无         | 上报地址                   |
| `access_token`     | 字符串/空    | 否   | `null`     | 访问令牌                   |
| `timeout`          | 数字         | 否   | `0`        | 超时时间（单位毫秒，为`0`不启用） |

</details>

<details>
<summary>WebSocket</summary>

```json
{
    "type": "ws",
    "protocol_version": 12,
    "host": "0.0.0.0",
    "port": 5700,
    "access_token": null
}
```

| 项目               | 类型           | 必须 | 默认值             | 说明                        |
|--------------------|----------------|------|--------------------|-----------------------------|
| `type`             | 字符串         | 是   | 无                 | 连接类型，为`ws`            |
| `protocol_version` | 数字           | 否   | `12`               | 协议版本，为 `12`           |
| `port`             | 数字           | 否   | `5700`             | WebSocket 服务器端口        |
| `host`             | 字符串         | 否   | `0.0.0.0`          | WebSocket 服务器 IP         |
| `access_token`     | 字符串/空      | 否   | `null`             | 访问令牌                    |


</details>

<details>
<summary>反向 WebSocket</summary>

```json
{
    "type": "ws-reverse",
    "url": "",
    "protocol_version": 12,
    "access_token": null,
    "reconnect_interval": 5000
}
```

| 项目                 | 类型      | 必须 | 默认值     | 说明                       |
|----------------------|-----------|------|------------|----------------------------|
| `type`               | 字符串    | 是   | 无         | 连接类型，为`ws-reverse`   |
| `protocol_version`   | 数字      | 否   | `12`       | 协议版本，为 `12`          |
| `url`                | 字符串    | 是   | 无         | WebSocket 客户端连接地址   |
| `access_token`       | 字符串/空 | 否   | `null`     | 访问令牌                   |
| `reconnect_interval` | 数字      | 否   | `5000`     | 重连间隔（单位毫秒）       |



</details>


### OneBot V11

::: tip

在所有采用 OneBot V11 标准的连接中，请确保指定 `"protocol_version": 11`（默认值为 `12` ）。

若不正确设定，将会收到「无效的连接类型或协议版本」的提示。

:::

<details>
<summary>HTTP</summary>

```json
{
    "type": "http",
    "protocol_version": 11,
    "host": "0.0.0.0",
    "port": 5700,
    "access_token": null
}
```

| 项目               | 类型         | 必须 | 默认值     | 说明                       |
|--------------------|--------------|------|------------|----------------------------|
| `type`             | 字符串       | 是   | 无         | 连接类型，为 `http`        |
| `protocol_version` | 数字         | 是   | `12`       | 协议版本，为 `11`          |
| `host`             | 字符串       | 否   | `0.0.0.0`  | HTTP 服务器 IP             |
| `port`             | 数字         | 否   | `5700`     | HTTP 服务器端口            |
| `access_token`     | 字符串/空    | 否   | `null`     | 访问令牌                   |


</details>

<details>
<summary>HTTP Post</summary>

```json
{
    "type": "http-post",
    "protocol_version": 11,
    "url": "",
    "timeout": 0,
    "secret": null
}
```

| 项目               | 类型         | 必须 | 默认值     | 说明                       |
|--------------------|--------------|------|------------|----------------------------|
| `type`             | 字符串       | 是   | 无         | 连接类型，为 `http`        |
| `protocol_version` | 数字         | 是   | `12`       | 协议版本，为 `11`          |
| `url`              | 字符串       | 是   | 无         | HTTP 连接地址              |
| `secret`           | 字符串/空    | 否   | `null`     | 请求密钥                   |


</details>



<details>
<summary>WebSocket</summary>

```json
{
    "type": "ws",
    "protocol_version": 11,
    "host": "0.0.0.0",
    "port": 6700,
    "access_token": null
}
```

| 项目               | 类型           | 必须 | 默认值             | 说明                        |
|--------------------|----------------|------|--------------------|-----------------------------|
| `type`             | 字符串         | 是   | 无                 | 连接类型，为`ws`            |
| `protocol_version` | 数字           | 否   | `12`               | 协议版本，为 `11`           |
| `port`             | 数字           | 否   | `6700`             | WebSocket 服务器端口        |
| `host`             | 字符串         | 否   | `0.0.0.0`          | WebSocket 服务器 IP         |
| `access_token`     | 字符串/空      | 否   | `null`             | 访问令牌                    |


</details>


<details>
<summary>反向 WebSocket</summary>

```json
{
    "type": "ws-reverse",
    "protocol_version": 11,
    "url": "",
    "api_url": "",
    "event_url": "",
    "reconnect_interval": 3000,
    "use_universal_client": false,
    "access_token": null
}
```

| 项目               | 类型           | 必须 | 默认值             | 说明                        |
|--------------------|----------------|------|--------------------|-----------------------------|
| `type`             | 字符串         | 是   | 无                 | 连接类型，为`ws-reverse`    |
| `protocol_version` | 数字           | 否   | `12`               | 协议版本，为 `11`           |
| `url`              | 字符串         | 否   | 无                 | WebSocket 服务器地址        |
| `api_url`          | 字符串         | 否   | 无                 | WebSocket API 服务器地址，为空时填入 `url` 字段的配置 |
| `event_url`        | 字符串         | 否   | 无                 | WebSocket Event 服务器地址，为空时填入 `url` 字段的配置 |
| `use_universal_client` | 布尔       | 否   | `false`            | 是否启用 WebSocket Universal 客户端 |
| `access_token`     | 字符串/空      | 否   | `null`             | 访问令牌                    |


</details>


