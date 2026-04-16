# 待办事项功能使用说明

## 功能概述

通过语音指令创建待办事项，例如："明天10点提醒我买蔬菜"，大模型会自动解析时间、任务内容，并调用待办创建接口。

## 实现架构

```
用户语音 → ASR识别 → LLM意图识别 → Function Call → create_todo工具 → manager-api → 数据库
```

## 已完成的实现

### 1. xiaozhi-server 端

#### 1.1 工具函数
- **文件**: `plugins_func/functions/create_todo.py`
- **功能**:
  - 智能时间解析（支持：明天、后天、下周一、10点、下午3点等）
  - 重复类型识别（每天、每周、每月）
  - 调用 manager-api 的待办创建接口
  - 错误处理和日志记录

#### 1.2 配置文件
- **文件**: `config.yaml`
- **配置项**:
```yaml
plugins:
  create_todo:
    # manager-api的地址
    manager_api_url: "http://localhost:8080"
    # API密钥（如果需要认证）
    api_key: ""

Intent:
  function_call:
    functions:
      - create_todo  # 注册待办工具
```

### 2. manager-api 端

#### 2.1 Controller
- **文件**: `TodoController.java`
- **接口**: `POST /todo/voice/create`
- **请求体**:
```json
{
  "title": "买蔬菜",
  "content": "明天上午去菜市场",
  "agentId": "xxx",
  "deviceId": "xxx"
}
```

## 使用示例

### 语音指令示例

1. **简单待办**
   - 用户说："提醒我买蔬菜"
   - 解析结果：title="买蔬菜", due_date=null

2. **带时间的待办**
   - 用户说："明天10点提醒我开会"
   - 解析结果：title="开会", due_date="2024-01-16 10:00:00"

3. **带详细内容的待办**
   - 用户说："后天下午3点提醒我去医院看医生，记得带上医保卡"
   - 解析结果：
     - title="去医院看医生"
     - content="记得带上医保卡"
     - due_date="2024-01-17 15:00:00"

4. **重复待办**
   - 用户说："每天早上8点提醒我晨跑"
   - 解析结果：
     - title="晨跑"
     - repeat_type="daily"
     - due_date="2024-01-16 08:00:00"

### 时间解析规则

| 用户表达 | 解析结果 |
|---------|---------|
| 明天 | 当前日期 + 1天 |
| 后天 | 当前日期 + 2天 |
| 下周一 | 下周的星期一 |
| 10点 | 当天或指定日期的10:00 |
| 下午3点 | 当天或指定日期的15:00 |
| 晚上8点半 | 当天或指定日期的20:30 |

默认时间规则：
- 未指定具体时间时，默认为早上9点
- 上午/早上：默认9点
- 中午：默认12点
- 下午：默认14点
- 晚上/傍晚：默认19点
- 凌晨：默认0点

## 配置步骤

### 1. 启动 manager-api

确保 manager-api 服务已启动，默认端口为 8080。

### 2. 配置 xiaozhi-server

编辑 `config.yaml` 文件：

```yaml
plugins:
  create_todo:
    # 修改为你的 manager-api 地址
    manager_api_url: "http://your-manager-api-host:8080"
    # 如果 manager-api 需要认证，填写 API key
    api_key: ""

# 在 Intent 中启用 create_todo
Intent:
  function_call:
    functions:
      - create_todo
```

### 3. 重启 xiaozhi-server

```bash
cd main/xiaozhi-server
python app.py
```

### 4. 测试功能

1. 连接 ESP32 设备或使用测试页面
2. 说出语音指令，例如："明天10点提醒我买蔬菜"
3. 查看日志确认待办是否创建成功

## 日志示例

```
[INFO] 调用待办创建接口: http://localhost:8080/todo/voice/create, 参数: {'title': '买蔬菜', 'content': '', 'dueDate': '2024-01-16 10:00:00'}
[INFO] 待办创建成功，ID: 1234567890
[INFO] 已为您创建待办事项：买蔬菜，截止时间：2024-01-16 10:00:00
```

## 故障排查

### 1. 待办创建失败

**问题**: 返回 "待办功能未正确配置"

**解决**:
- 检查 `config.yaml` 中的 `manager_api_url` 是否正确
- 确保 manager-api 服务正在运行
- 检查网络连接

### 2. 时间解析不准确

**问题**: 时间解析不符合预期

**解决**:
- 尽量使用明确的时间表达，如"明天上午10点"
- 避免模糊表达，如"过一会儿"

### 3. 认证失败

**问题**: 返回 401 未授权

**解决**:
- 如果 manager-api 需要认证，在配置中添加 `api_key`
- 检查 Token 是否有效

## 扩展功能

### 添加更多时间表达

编辑 `create_todo.py` 中的 `parse_relative_time` 函数，添加新的时间解析规则。

### 支持更多重复类型

目前支持：none, daily, weekly, monthly

可以扩展支持：
- yearly（每年）
- custom（自定义，如每3天）

### 集成日历服务

可以将待办同步到 Google Calendar、Outlook 等日历服务。

## 技术细节

### 工具注册机制

```python
@register_function("create_todo", CREATE_TODO_FUNCTION_DESC, ToolType.SYSTEM_CTL)
def create_todo(conn, title, content, due_date, priority, repeat_type):
    # 工具实现
    pass
```

### Function Call 流程

1. LLM 分析用户意图
2. 决定调用 `create_todo` 工具
3. 提取参数（title, due_date 等）
4. 调用工具函数
5. 工具返回结果给 LLM
6. LLM 生成最终回复

### 安全性

- 所有请求都经过用户认证
- 待办事项与用户ID绑定
- 支持跨设备同步（通过 agentId 和 deviceId）

## 注意事项

1. **时区问题**: 确保服务器时区设置正确
2. **并发控制**: 大量用户同时创建待办时注意数据库性能
3. **数据清理**: 定期清理已完成的待办事项
4. **隐私保护**: 待办内容可能包含敏感信息，注意数据加密

## 相关文件

- `main/xiaozhi-server/plugins_func/functions/create_todo.py` - 工具函数实现
- `main/xiaozhi-server/config.yaml` - 配置文件
- `main/manager-api/src/main/java/xiaozhi/modules/todo/controller/TodoController.java` - API接口
- `main/manager-api/src/main/java/xiaozhi/modules/todo/service/TodoService.java` - 业务逻辑

## 更新日志

### 2024-01-15
- ✅ 初始版本发布
- ✅ 支持基本待办创建
- ✅ 支持智能时间解析
- ✅ 支持重复类型设置
