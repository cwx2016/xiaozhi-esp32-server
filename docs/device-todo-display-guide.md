# 设备端待办显示集成指南

## 概述

本文档说明如何在 ESP32 设备上接收并显示从服务器推送的待办事项列表。

## WebSocket 消息格式

当用户通过语音查询待办时，服务器会推送以下格式的 JSON 消息到设备：

```json
{
  "type": "todo",
  "action": "list",
  "count": 3,
  "todos": [
    {
      "id": "1234567890",
      "title": "买蔬菜",
      "content": "记得带上环保袋",
      "dueDate": "2024-01-16",
      "dueTime": "10:00",
      "priority": 1,
      "repeatType": "none"
    },
    {
      "id": "1234567891",
      "title": "开会",
      "content": "准备项目汇报材料",
      "dueDate": "2024-01-16",
      "dueTime": "14:00",
      "priority": 2,
      "repeatType": "none"
    }
  ],
  "session_id": "abc123"
}
```

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型，固定为 "todo" |
| action | string | 操作类型，"list" 表示待办列表 |
| count | integer | 待办数量 |
| todos | array | 待办数组 |
| todos[].id | string | 待办ID |
| todos[].title | string | 待办标题 |
| todos[].content | string | 待办内容/备注 |
| todos[].dueDate | string | 截止日期 (YYYY-MM-DD) |
| todos[].dueTime | string | 截止时间 (HH:MM) |
| todos[].priority | integer | 优先级 (0=普通, 1=重要, 2=紧急) |
| todos[].repeatType | string | 重复类型 (none/daily/weekly/monthly) |
| session_id | string | 会话ID |

## ESP32 代码示例

### 1. 消息处理

```cpp
#include <ArduinoJson.h>
#include <WiFi.h>
#include <WebSocketsClient.h>

// WebSocket 客户端
WebSocketsClient webSocket;

// 待办数据结构
struct TodoItem {
  String id;
  String title;
  String content;
  String dueDate;
  String dueTime;
  int priority;
  String repeatType;
};

// 待办列表
std::vector<TodoItem> todoList;

// WebSocket 事件回调
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_TEXT: {
      // 解析 JSON 消息
      StaticJsonDocument<4096> doc;
      DeserializationError error = deserializeJson(doc, payload, length);
      
      if (error) {
        Serial.println("JSON 解析失败");
        return;
      }
      
      // 检查消息类型
      const char* msgType = doc["type"];
      if (strcmp(msgType, "todo") == 0) {
        handleTodoMessage(doc);
      }
      break;
    }
  }
}

// 处理待办消息
void handleTodoMessage(JsonDocument& doc) {
  const char* action = doc["action"];
  
  if (strcmp(action, "list") == 0) {
    // 清空旧列表
    todoList.clear();
    
    // 解析待办列表
    JsonArray todos = doc["todos"];
    for (JsonObject todo : todos) {
      TodoItem item;
      item.id = todo["id"].as<String>();
      item.title = todo["title"].as<String>();
      item.content = todo["content"].as<String>();
      item.dueDate = todo["dueDate"].as<String>();
      item.dueTime = todo["dueTime"].as<String>();
      item.priority = todo["priority"].as<int>();
      item.repeatType = todo["repeatType"].as<String>();
      
      todoList.push_back(item);
    }
    
    int count = doc["count"];
    Serial.printf("收到 %d 个待办事项\n", count);
    
    // 显示待办列表
    displayTodoList();
  }
}
```

### 2. 屏幕显示

```cpp
#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();

// 显示待办列表
void displayTodoList() {
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  
  // 标题
  tft.setCursor(10, 10);
  tft.printf("待办事项 (%d)", todoList.size());
  
  // 绘制分隔线
  tft.drawLine(10, 40, 310, 40, TFT_BLUE);
  
  // 显示每个待办
  int yPos = 50;
  for (int i = 0; i < todoList.size() && i < 5; i++) {
    TodoItem& todo = todoList[i];
    
    // 优先级颜色
    uint16_t priorityColor;
    switch(todo.priority) {
      case 2: priorityColor = TFT_RED; break;    // 紧急
      case 1: priorityColor = TFT_YELLOW; break; // 重要
      default: priorityColor = TFT_WHITE; break;  // 普通
    }
    
    // 显示序号和标题
    tft.setTextColor(priorityColor);
    tft.setCursor(10, yPos);
    tft.printf("%d. %s", i + 1, todo.title.c_str());
    
    // 显示时间
    if (!todo.dueDate.isEmpty()) {
      tft.setTextColor(TFT_GREEN);
      tft.setCursor(10, yPos + 20);
      tft.printf("   %s %s", todo.dueDate.c_str(), todo.dueTime.c_str());
    }
    
    yPos += 50;
    
    // 如果超出屏幕，停止显示
    if (yPos > 200) {
      tft.setTextColor(TFT_GRAY);
      tft.setCursor(10, yPos);
      tft.print("...更多待办请语音查看");
      break;
    }
  }
}
```

### 3. 触摸交互（可选）

```cpp
// 触摸完成待办
void handleTouch(uint16_t x, uint16_t y) {
  // 计算点击的是哪个待办
  int index = (y - 50) / 50;
  
  if (index >= 0 && index < todoList.size()) {
    // 标记为已完成
    markTodoAsComplete(todoList[index].id);
  }
}

// 调用服务器接口标记完成
void markTodoAsComplete(String todoId) {
  // 发送 HTTP 请求或 WebSocket 消息
  // POST /todo/{id}/complete
}
```

## UI 设计建议

### 布局方案

```
┌─────────────────────────────┐
│  待办事项 (3)                │
├─────────────────────────────┤
│  1. 🔴 买蔬菜               │
│     2024-01-16 10:00        │
│                             │
│  2. 🟡 开会                 │
│     2024-01-16 14:00        │
│                             │
│  3. ⚪ 健身                 │
│     2024-01-17 08:00        │
└─────────────────────────────┘
```

### 颜色方案

- **紧急** (priority=2): 红色 (#FF0000)
- **重要** (priority=1): 黄色 (#FFFF00)
- **普通** (priority=0): 白色 (#FFFFFF)
- **时间**: 绿色 (#00FF00)
- **背景**: 黑色 (#000000)

### 交互建议

1. **滑动浏览**: 支持上下滑动查看更多待办
2. **点击完成**: 点击待办项标记为已完成
3. **长按删除**: 长按待办项弹出删除确认
4. **语音操作**: 支持语音"完成第一个待办"等指令

## 完整示例代码

参考 `examples/todo_display_example.ino` 文件获取完整的 Arduino 示例代码。

## 测试步骤

1. **启动服务**
   ```bash
   # 启动 manager-api
   cd main/manager-api
   mvn spring-boot:run
   
   # 启动 xiaozhi-server
   cd main/xiaozhi-server
   python app.py
   ```

2. **创建待办**
   - 对小智说："明天10点提醒我买蔬菜"
   - 对小智说："后天下午3点提醒我开会"

3. **查询待办**
   - 对小智说："查看我的待办"
   - 对小智说："我有什么任务"

4. **验证显示**
   - 检查 ESP32 屏幕是否正确显示待办列表
   - 验证优先级颜色是否正确
   - 验证时间信息是否准确

## 常见问题

### Q1: 收不到待办消息？

**A**: 检查以下几点：
1. WebSocket 连接是否正常
2. 消息解析是否正确（添加调试日志）
3. 服务器配置是否正确

### Q2: 待办列表为空？

**A**: 
1. 确认数据库中已有未完成的待办
2. 检查 userId、agentId、deviceId 是否匹配
3. 查看服务器日志确认查询结果

### Q3: 显示乱码？

**A**:
1. 确保 JSON 使用 UTF-8 编码
2. 检查屏幕库是否支持中文
3. 加载合适的中文字体

## 性能优化

1. **限制数量**: 默认只返回10条，避免数据过多
2. **分页加载**: 大量待办时分页显示
3. **缓存机制**: 本地缓存待办数据，减少网络请求
4. **增量更新**: 只传输变化的待办项

## 扩展功能

### 1. 待办提醒

```cpp
// 定时检查即将到期的待办
void checkDueTodos() {
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  
  for (TodoItem& todo : todoList) {
    // 解析待办时间
    // 如果即将到期（如30分钟内），发出提醒
  }
}
```

### 2. 语音播报

```cpp
// TTS 播报待办
void speakTodos() {
  String text = "您有" + String(todoList.size()) + "个待办事项。";
  
  for (int i = 0; i < todoList.size(); i++) {
    text += "第" + String(i+1) + "个，" + todoList[i].title;
  }
  
  // 调用 TTS 接口播报
}
```

### 3. 同步状态

```cpp
// 定期同步待办状态
void syncTodoStatus() {
  // 从服务器拉取最新待办列表
  // 更新本地显示
}
```

## 相关文档

- [待办功能实现总结](../../docs/TODO_IMPLEMENTATION_SUMMARY.md)
- [待办集成指南](../../docs/todo-integration.md)
- [WebSocket 通信协议](../websocket-protocol.md)

## 技术支持

如有问题，请查阅项目文档或提交 Issue。
