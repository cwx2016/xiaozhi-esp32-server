import requests
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

GET_TODO_LIST_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_todo_list",
        "description": (
            "查询用户的待办事项列表。当用户想查看自己有哪些任务、待办、提醒时使用。"
            "例如：'查看待办'、'我有什么任务'、'显示待办事项'、'还有哪些事没做'等。"
            "返回未完成的待办列表，并推送到设备屏幕显示。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "返回的待办数量，默认为10条。如果用户说'显示前5个待办'，则设为5。可选参数，不传则使用默认值10。",
                    "default": 10,
                },
            },
            "required": [],
        },
    },
}


@register_function("get_todo_list", GET_TODO_LIST_FUNCTION_DESC, ToolType.SYSTEM_CTL)
def get_todo_list(conn: "ConnectionHandler", limit: int = 10):
    """
    查询待办事项列表并推送到设备显示
    :param conn: 连接对象
    :param limit: 返回数量限制
    :return: ActionResponse
    """
    try:
        # 获取manager-api的配置
        todo_config = conn.config.get("plugins", {}).get("create_todo", {})
        
        # 调试日志
        logger.bind(tag=TAG).info(f"get_todo_list - create_todo配置: {todo_config}")
        
        manager_api_url = todo_config.get("manager_api_url", "http://localhost:8002")
        api_key = todo_config.get("api_key", "")
        
        # 强制修正错误的端口配置（兜底逻辑）
        # 支持的错误端口列表：8080, 8082 等常见错误
        incorrect_ports = [":8080", ":8082", ":8088", ":9090"]
        for incorrect_port in incorrect_ports:
            if incorrect_port in manager_api_url:
                correct_url = manager_api_url.replace(incorrect_port, ":8002")
                logger.bind(tag=TAG).warning(f"get_todo_list - 检测到错误的端口{incorrect_port}，自动修正为8002")
                logger.bind(tag=TAG).warning(f"原URL: {manager_api_url}")
                logger.bind(tag=TAG).warning(f"修正后: {correct_url}")
                manager_api_url = correct_url
                break
        
        logger.bind(tag=TAG).info(f"get_todo_list - 最终使用的manager_api_url: {manager_api_url}")
        
        if not manager_api_url or "你" in manager_api_url:
            return ActionResponse(
                Action.REQLLM,
                "待办功能未正确配置，请联系管理员配置manager-api地址",
                None
            )
        
        # 构建请求URL - TodoController的路径是 /xiaozhi/todo/device/list
        # 注意：manager-api的context-path是/xiaozhi
        url = f"{manager_api_url}/xiaozhi/todo/device/list"
        
        # 构建请求参数
        params = {
            "limit": min(max(limit, 1), 50),  # 限制在1-50之间
        }
        
        # 添加 agentId 和 deviceId（如果可用）
        if hasattr(conn, 'agent_id') and conn.agent_id:
            params["agentId"] = conn.agent_id
        if hasattr(conn, 'device_id') and conn.device_id:
            params["deviceId"] = conn.device_id
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        logger.bind(tag=TAG).info(f"调用待办查询接口: {url}, 参数: {params}")
        
        # 发送请求
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                todo_list = result.get("data", [])
                
                if not todo_list:
                    return ActionResponse(
                        Action.REQLLM,
                        "您目前没有待办事项",
                        None
                    )
                
                # 构建待办列表文本
                todo_text = f"您有{len(todo_list)}个待办事项：\n\n"
                for i, todo in enumerate(todo_list, 1):
                    title = todo.get("title", "")
                    content = todo.get("content", "")
                    due_date = todo.get("dueDate", "")
                    due_time = todo.get("dueTime", "")
                    priority = todo.get("priority", 0)
                    repeat_type = todo.get("repeatType", "none")
                    
                    # 优先级标识（使用中文）
                    priority_text = ""
                    if priority == 2:
                        priority_text = "【紧急】"
                    elif priority == 1:
                        priority_text = "【重要】"
                    
                    # 时间信息
                    time_info = ""
                    if due_date:
                        if due_time:
                            time_info = f"{due_date} {due_time}"
                        else:
                            time_info = due_date
                    else:
                        if due_time:
                            time_info = due_time
                        else:
                            time_info = "未设置时间"
                    
                    # 重复类型标识
                    repeat_text = ""
                    if repeat_type == "daily":
                        repeat_text = " (每天)"
                    elif repeat_type == "weekly":
                        repeat_text = " (每周)"
                    elif repeat_type == "monthly":
                        repeat_text = " (每月)"
                    elif repeat_type == "yearly":
                        repeat_text = " (每年)"
                    
                    # 组合显示：优先级 + 标题 + 内容 + 时间 + 重复类型
                    display_content = f"{i}. {priority_text}{title}"
                    if content:
                        display_content += f" - {content}"
                    display_content += f"\n   时间：{time_info}{repeat_text}\n\n"
                    
                    todo_text += display_content
                
                # 通过WebSocket推送待办数据到设备
                device_todos = []
                for todo in todo_list:
                    device_todo = {
                        "id": todo.get("id"),
                        "title": todo.get("title", ""),
                        "content": todo.get("content", ""),
                        "dueDate": todo.get("dueDate", ""),
                        "dueTime": todo.get("dueTime", ""),
                        "priority": todo.get("priority", 0),
                        "repeatType": todo.get("repeatType", "none"),
                    }
                    device_todos.append(device_todo)
                
                # 推送消息到设备
                push_message = {
                    "type": "todo",
                    "action": "list",
                    "count": len(device_todos),
                    "todos": device_todos,
                    "session_id": getattr(conn, 'session_id', '')
                }
                
                import json
                import asyncio
                
                # 异步推送消息
                async def push_to_device():
                    try:
                        if hasattr(conn, 'websocket') and conn.websocket:
                            await conn.websocket.send(json.dumps(push_message, ensure_ascii=False))
                            logger.bind(tag=TAG).info(f"已推送{len(device_todos)}个待办到设备")
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"推送待办到设备失败: {e}")
                
                # 在事件循环中执行
                if hasattr(conn, 'loop') and conn.loop:
                    asyncio.run_coroutine_threadsafe(push_to_device(), conn.loop)
                
                logger.bind(tag=TAG).info(f"待办查询成功，共{len(todo_list)}条")
                return ActionResponse(Action.REQLLM, todo_text, None)
            else:
                error_msg = result.get("msg", "查询待办失败")
                logger.bind(tag=TAG).error(f"待办查询失败: {error_msg}")
                return ActionResponse(Action.REQLLM, f"抱歉，查询待办失败：{error_msg}", None)
        else:
            logger.bind(tag=TAG).error(f"待办查询接口返回错误: {response.status_code}, {response.text}")
            return ActionResponse(Action.REQLLM, "抱歉，查询待办时遇到网络错误，请稍后重试", None)
    
    except requests.exceptions.Timeout:
        logger.bind(tag=TAG).error("待办查询接口超时")
        return ActionResponse(Action.REQLLM, "抱歉，查询待办超时，请检查网络连接", None)
    except requests.exceptions.ConnectionError:
        logger.bind(tag=TAG).error("无法连接到待办服务")
        return ActionResponse(Action.REQLLM, "抱歉，无法连接到待办服务，请检查配置", None)
    except Exception as e:
        logger.bind(tag=TAG).error(f"查询待办异常: {e}", exc_info=True)
        return ActionResponse(Action.REQLLM, f"抱歉，查询待办时出现错误：{str(e)}", None)
