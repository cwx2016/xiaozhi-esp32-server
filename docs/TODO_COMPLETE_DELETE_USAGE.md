# 完成待办和删除待办功能使用说明

## 📋 功能概述

新增了兩個待办事项管理工具：
- **complete_todo**: 标记待办事项为已完成
- **delete_todo**: 删除待办事项（逻辑删除）

## 🛠️ 部署步骤

### 1. 执行数据库迁移脚本

按顺序执行以下 SQL 文件：

```bash
# 1. 添加插件配置到 ai_model_provider 表
mysql -u root -p your_database < main/manager-api/src/main/resources/db/changelog/202604180100.sql

# 2. 为所有智能体关联新插件
mysql -u root -p your_database < main/manager-api/src/main/resources/db/changelog/202604180110.sql
```

或者在 MySQL 客户端中直接执行这两个文件的内容。

### 2. 重启后端服务

```bash
cd main/manager-api
mvn spring-boot:run
# 或者使用你的启动方式
```

### 3. 更新配置文件

`config.yaml` 已经更新，包含了新的插件配置：

```yaml
Intent:
  function_call:
    functions:
      - create_todo
      - get_todo_list
      - complete_todo    # 新增
      - delete_todo      # 新增
```

### 4. 重启 xiaozhi-server

```bash
cd main/xiaozhi-server
python app.py
```

## 💬 使用示例

### 完成待办

**用户可以说：**
- "我已经吃早饭了"
- "完成买菜任务"
- "记周报做完了"
- "把开会的待办标记为完成"

**系统行为：**
1. LLM 识别用户意图，调用 `complete_todo` 工具
2. 如果提供了标题，系统会模糊匹配待办列表找到对应的 ID
3. 调用后端接口 `/xiaozhi/todo/{id}/complete` 标记为完成
4. 返回成功消息："好的，'买菜'这个待办已经完成了！真棒！👍"

### 删除待办

**用户可以说：**
- "删除买菜的待办"
- "取消记周报的任务"
- "把吃饭的提醒删掉"
- "我不需要那个开会的提醒了"

**系统行为：**
1. LLM 识别用户意图，调用 `delete_todo` 工具
2. 如果提供了标题，系统会模糊匹配待办列表找到对应的 ID
3. 调用后端接口 `/xiaozhi/todo/{id}` (DELETE) 进行逻辑删除
4. 返回成功消息："好的，'买菜'这个待办已经删除了！🗑️"

## 🔧 技术实现

### 插件文件

- `plugins_func/functions/complete_todo.py` - 完成待办工具
- `plugins_func/functions/delete_todo.py` - 删除待办工具

### 后端接口

- `PUT /xiaozhi/todo/{id}/complete` - 标记为已完成
- `DELETE /xiaozhi/todo/{id}` - 删除待办（逻辑删除）

### 数据库迁移

- `202604180100.sql` - 添加插件配置
- `202604180110.sql` - 关联智能体

### 默认插件配置

新建智能体时会自动关联以下插件：
- SYSTEM_PLUGIN_MUSIC
- SYSTEM_PLUGIN_WEATHER
- SYSTEM_PLUGIN_NEWS_NEWSNOW
- SYSTEM_PLUGIN_CREATE_TODO
- SYSTEM_PLUGIN_GET_TODO_LIST
- **SYSTEM_PLUGIN_COMPLETE_TODO** (新增)
- **SYSTEM_PLUGIN_DELETE_TODO** (新增)

## ⚠️ 注意事项

1. **删除操作不可恢复**：虽然使用的是逻辑删除（status=-1），但用户界面上不会再显示该待办
2. **模糊匹配**：如果只提供标题，系统会使用模糊匹配查找待办，可能匹配到多个结果时会选择第一个匹配的
3. **权限控制**：由于是内部调用，使用了 `@PermitAll` 注解允许匿名访问
4. **错误处理**：所有接口都有完善的异常处理和日志记录

## 🐛 故障排查

### 工具未显示在可用工具列表中

1. 检查数据库是否有插件配置：
   ```sql
   SELECT * FROM ai_model_provider 
   WHERE provider_code IN ('complete_todo', 'delete_todo');
   ```

2. 检查智能体是否关联了插件：
   ```sql
   SELECT a.agent_name, amp.provider_code
   FROM ai_agent a
   JOIN ai_agent_plugin_mapping apm ON a.id = apm.agent_id
   JOIN ai_model_provider amp ON apm.plugin_id = amp.id
   WHERE amp.provider_code IN ('complete_todo', 'delete_todo');
   ```

3. 查看启动日志：
   ```
   [DEBUG] 最终需要加载的函数: [...'complete_todo', 'delete_todo'...]
   ```

### 调用失败

1. 检查 manager-api 是否正常运行
2. 检查 config.yaml 中的 `manager_api_url` 配置是否正确
3. 查看 xiaozhi-server 日志中的错误信息

## 📊 测试建议

1. **创建测试待办**：
   - "明天上午10点开会"
   - "每天下午5点记周报"

2. **查询待办列表**：
   - "显示待办"

3. **完成待办**：
   - "我已经开完会了"
   - "完成记周报的任务"

4. **删除待办**：
   - "删除开会的待办"
   - "我不需要记周报的提醒了"

5. **验证状态**：
   - 再次查询待办列表，确认状态已更新
