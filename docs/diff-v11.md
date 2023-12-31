# 标准差异细节 (OneBot V11)

> 本页面是 OneDisc 与 OneBot V11 标准差异的详细说明，与 OneBot V12 的偏差请查看 [本页面][1]

[1]: differences.md

## 支持受限的内容

### 事件

> OneDisc 暂不支持事件快速操作

| 事件名称               | 说明             |
|------------------------|------------------|
| `notice.group_upload`  | |
| `notice.friend_add`    | Discord Bot 没有好友功能 |
| `notice.notify`        | Discord 不支持相关功能 |
| `request.friend`       | Discord Bot 没有好友功能 |
| `request.group`        | Discord 不支持相关功能 |

> 「说明」为空表示「暂未实现」，将在后续版本完成  

#### `message.private`

| 字段名     | 说明                                          |
|------------|-----------------------------------------------|
| `font`     | Discord 不支持相关功能，将填入 `-1`           |
| `sender`   | 平台限制，只能获取 `user_id`、`nickname` 字段 |

#### `message.group`


| 字段名     | 说明                                          |
|------------|-----------------------------------------------|
| `font`     | Discord 不支持相关功能，将填入 `-1`           |
| `sender`   | 平台限制，只能获取 `user_id`、`nickname`、`card`、`role` 字段 |

### API

| 接口名称         | 终结点                    | 说明                     |
|------------------|---------------------------|--------------------------|
| 获取合并转发消息 | `get_forward_msg`         | Discord 不支持相关功能   |
| 发送好友赞       | `send_like`               | Discord 不支持相关功能   |
| 群组匿名用户禁言 | `set_group_anonymous_ban` | Discord 不支持相关功能   |
| 群组全员禁言     | `set_group_whole_ban`     | Discord 不支持相关功能   |
| 群组匿名         | `set_group_anonymous`     | Discord 不支持相关功能   |
| 设置群组专属头衔 | `set_group_special_title` | Discord 不支持相关功能   |
| 处理加好友请求   | `set_friend_add_request`  | Discord Bot 没有好友功能 |
| 处理加群请求     | `set_group_add_request`   | Discord 不支持相关功能   |
| 获取好友列表     | `get_friend_list`         | Discord Bot 没有好友功能 |
| 获取群荣誉信息   | `get_group_honor_info`    | Discord 不支持相关功能   |
| 获取 Cookies     | `get_cookies`             | ~~这是什么.jpg~~         |
| 获取 CSRF Token  | `get_csrf_token`          | ~~这是什么.jpg~~         |
| 获取 QQ 接口凭证 | `get_credentials`         | ~~这是什么.jpg~~         |
| 获取语音         | `get_record`              | ~~这玩意不写CQ码上了吗~~ |
| 获取图片         | `get_image`               | ~~这玩意不写CQ码上了吗~~ |
| 获取群成员信息   | `get_group_member_info`   | 平台限制，只能获取 `user_id`、`nickname`、`card`、`sex`、`join_time`、`role` 字段 |

> 「说明」为空的接口表示「暂未实现」将在后续版本完成


### 消息段类型

| 消息段名称     | 消息段类型  | 说明                   |
|----------------|-------------|------------------------|
| 猜拳魔法表情   | `rps`       | Discord 不支持相关功能 |
| 掷骰子魔法表情 | `dice`      | Discord 不支持相关功能 |
| 窗口抖动       | `shake`     | Discord 不支持相关功能 |
| 戳一戳         | `poke`      | Discord 不支持相关功能 |
| 匿名发消息     | `anonymous` | Discord 不支持相关功能 |
| 推荐好友/群    | `contact`   |                        |
| 音乐自定义分享 | `music`     |                        |
| 合并转发       | `forward`   | Discord 不支持有关功能 |
| XML 消息       | `xml`       | Discord 不支持有关功能 |
| JSON 消息      | `json`      | Discord 不支持有关功能 |

> 「说明」为空表示「暂未实现」，将在后续版本完成  

## 拓展内容

### 拓展接口

#### `edit_message` 编辑消息

| 参数         | 类型           | 必须 | 说明                |
|--------------|----------------|------|---------------------|
| `message_id` | int            | 是   | 要编辑的消息 ID     |
| `content`    | message \| str | 是   | 消息内容            |

本动作无相应数据

### 拓展消息段

#### `emoji` 自定义表情

| 字段名      | 数据类型    | 说明                      |
|-------------|-------------|---------------------------|
| `name`      | str         | 自定义表情名称            |
| `id`        | int         | 表情 ID                   |

#### `channel` 频道

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `channel_id` | int         | 频道 ID                   |


#### `role` 提及权限组

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `id`         | int         | 权限组 ID                 |

#### `timestamp` 时间

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `time`       | int         | Unix 时间戳               |
| `style`      | str         | 时间格式，[参见][3]       |

#### `navigation` Navigation

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `type`       | str         | ~~我不知道这是什么~~      |


#### `markdown` MarkDown

| 字段名       | 数据类型    | 说明                      |
|--------------|-------------|---------------------------|
| `data`       | str         | MarkDown 内容，支持使用 `base64:// + b64编码` |