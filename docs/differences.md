# 标准偏差细节

> 本页面是 OneDisc 实现与 OneBot V12 标准的偏差细节，与 OneBot V11 的偏差请查看 [本页面][2]

## 支持受限的内容

### 动作

| 动作名        | 终结点                   | 原因                         |
|---------------|--------------------------|------------------------------|
| 获取好友列表  | `get_friend_list`        | Discord Bot 没有好友功能，请求此动作将返回空列表 |

### 事件

| 事件                             | 说明                                   |
|----------------------------------|----------------------------------------|
| `notice.friend_increase`         | Discord Bot 没有好友功能               |
| `notice.friend_decrease`         | Discord Bot 没有好友功能               |
| `notice.channel_member_increase` | `discord.py` 未提供相关接口            |
| `notice.channel_member_decrease` | `discord.py` 未提供相关接口            |

#### 与标准有差异的事件

| 事件                               | 说明                                                                                                    |
|------------------------------------|---------------------------------------------------------------------------------------------------------|
| `notice.group_member_increase`     | 平台限制，无法判断加入成员是被邀请还是主动加入，`sub_type` 将依 [配置项][1] 填入空字符串或 `"join"`     |
| `notice.group_member_decrease`     | 平台限制，无法判断成员是主动离开还是被踢出，`sub_type` 将依 [配置项][1] 填入空字符串或 `"leave"`        |
| `notice.guild_member_increase`     | 同 `notice.group_member_increase`                                                                       |
| `notice.guild_member_decrease`     | 同 `notice.group_member_decrease`                                                                       |
| `notice.channel_create`            | 平台限制，无法获取操作者 ID，将填入`"-1"`                                                               |
| `notice.channel_delete`            | 平台限制，无法获取操作者 ID，将填入`"-1"`                                                               |
| `notice.channel_message_delete`    | 平台限制，无法判断消息为主动撤回还是被管理员撤回，`sub_type` 将依 [配置项][1] 填入空字符串或 `"recall"` |
| `notice.group_message_delete`      | 同 `notice.channel_message_delete`                                                                      |
| `notice.private_message_delete`    | 同 `notice.channel_message_delete`                                                                      |

### 消息段

| 消息段             | 说明                                               |
|--------------------|----------------------------------------------------|
| `voice` 语音       | `discord.py` 未提供相关接口，将以 `audio` 形式发送 |


## 拓展内容

> `message` 类型为 OneBot V12 消息段，其余数据类型参考 Python3 数据类型

### 拓展动作

#### `edit_message` 编辑消息

| 参数         | 类型    | 必须 | 说明                |
|--------------|---------|------|---------------------|
| `message_id` | str     | 是   | 要编辑的消息 ID     |
| `content`    | message | 是   | 消息内容            |

本动作无响应数据

### 拓展消息段

#### `discord.emoji` 自定义表情

| 字段名      | 数据类型    | 说明                      |
|-------------|-------------|---------------------------|
| `name`      | str         | 自定义表情名称            |
| `id`        | int         | 表情 ID                   |

#### `discord.channel` 频道

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `channel_id` | str         | 频道 ID                   |

#### `discord.role` 提及权限组

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `id`         | str         | 权限组 ID                 |

#### `discord.timestamp` 时间

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `time`       | int         | Unix 时间戳               |
| `style`      | str         | 时间格式，[参见][3]       |

#### `discord.navigation` Navigation

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `type`       | str         | ~~我不知道这是什么~~      |


#### `discord.markdown` MarkDown

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `data`       | str         | MarkDown 内容，支持使用 `base64:// + b64编码` |


[1]: config.md#%E5%9C%A8%E4%BA%8B%E4%BB%B6%E4%B8%AD%E4%BD%BF%E7%94%A8%E7%A9%BA%E5%AD%97%E7%AC%A6%E4%B8%B2%E4%BB%A3%E6%9B%BF%E4%B8%8D%E6%94%AF%E6%8C%81%E7%9A%84%E5%AD%90%E7%B1%BB%E5%9E%8B-use-empty-for-unsupported-subtype
[2]: diff-v11.md
[3]: https://discord.com/developers/docs/reference#message-formatting-timestamp-styles

