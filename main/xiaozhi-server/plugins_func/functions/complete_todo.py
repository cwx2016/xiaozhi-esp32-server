import requests
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


def get_todo_list_after_action(conn: "ConnectionHandler", manager_api_url: str, api_key: str = "", limit: int = 10) -> list:
    """
    获取待办列表的辅助函数
    :param conn: 连接对象
    :param manager_api_url: API地址
    :param api_key: API密钥
    :param limit: 返回数量限制
    :return: 待办列表
    """
    try:
        query_url = f"{manager_api_url}/xiaozhi/todo/device/list"
        params = {"limit": limit}
        
        # 添加agentId和deviceId参数
        if hasattr(conn, 'agent_id') and conn.agent_id:
            params["agentId"] = conn.agent_id
        if hasattr(conn, 'device_id') and conn.device_id:
            params["deviceId"] = conn.device_id
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.get(query_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                return result.get("data", [])
        return []
    except Exception as e:
        logger.bind(tag=TAG).error(f"获取待办列表失败: {e}")
        return []


def push_todo_list_to_device(conn: "ConnectionHandler", todo_list: list):
    """
    推送待办列表到设备端显示
    :param conn: 连接对象
    :param todo_list: 待办列表数据
    """
    try:
        # 转换为设备端格式
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
        
        # 构建推送消息
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
    except Exception as e:
        logger.bind(tag=TAG).error(f"推送待办列表异常: {e}")


COMPLETE_TODO_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "complete_todo",
        "description": (
            "标记待办事项为已完成。当用户完成某个任务后，使用此功能将其标记为完成状态。"
            "例如：'我已经吃早饭了'、'完成买菜任务'、'记周报做完了'等。"
            "需要提供待办的ID或标题来识别要完成的待办。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "todo_id": {
                    "type": "string",
                    "description": "待办事项的ID。如果知道具体ID则传入，否则可以传入标题让系统自动匹配。",
                },
                "title": {
                    "type": "string",
                    "description": "待办事项的标题或关键词。用于模糊匹配要完成的待办。如果提供了todo_id，此参数可选。",
                },
            },
            "required": [],
        },
    },
}


@register_function("complete_todo", COMPLETE_TODO_FUNCTION_DESC, ToolType.SYSTEM_CTL)
def complete_todo(conn: "ConnectionHandler", todo_id: str = None, title: str = None):
    """
    标记待办事项为已完成
    :param conn: 连接对象
    :param todo_id: 待办ID（可选）
    :param title: 待办标题（可选，用于模糊匹配）
    :return: ActionResponse
    """
    try:
        # 获取manager-api的配置
        todo_config = conn.config.get("plugins", {}).get("create_todo", {})
        
        manager_api_url = todo_config.get("manager_api_url", "http://localhost:8002")
        api_key = todo_config.get("api_key", "")
        
        logger.bind(tag=TAG).info(f"complete_todo - 收到请求: todo_id={todo_id}, title={title}")
        
        # 如果只提供了标题，需要先查询待办列表找到对应的ID
        if not todo_id and title:
            logger.bind(tag=TAG).info(f"根据标题 '{title}' 查找待办ID")
            
            # 调用查询接口获取待办列表
            query_url = f"{manager_api_url}/xiaozhi/todo/device/list"
            params = {
                "limit": 50,  # 获取更多以便匹配
            }
            
            # 如果有agentId和deviceId，添加到查询参数
            if hasattr(conn, 'agent_id') and conn.agent_id:
                params["agentId"] = conn.agent_id
            if hasattr(conn, 'device_id') and conn.device_id:
                params["deviceId"] = conn.device_id
            
            response = requests.get(query_url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    todo_list = result.get("data", [])
                    
                    # 模糊匹配标题
                    matched_todo = None
                    for todo in todo_list:
                        todo_title = todo.get("title", "")
                        if title.lower() in todo_title.lower() or todo_title.lower() in title.lower():
                            matched_todo = todo
                            break
                    
                    if matched_todo:
                        todo_id = matched_todo.get("id")
                        logger.bind(tag=TAG).info(f"找到匹配的待办: ID={todo_id}, 标题={matched_todo.get('title')}")
                    else:
                        return ActionResponse(Action.REQLLM, f"抱歉，没有找到标题包含'{title}'的待办事项", None)
                else:
                    return ActionResponse(Action.REQLLM, f"查询待办失败：{result.get('msg', '未知错误')}", None)
            else:
                return ActionResponse(Action.REQLLM, "查询待办时遇到网络错误，请稍后重试", None)
        
        # 检查是否获得了todo_id
        if not todo_id:
            return ActionResponse(Action.REQLLM, "请提供待办ID或标题，例如：'完成买菜的待办'", None)
        
        # 调用完成接口（使用设备端专用接口）
        complete_url = f"{manager_api_url}/xiaozhi/todo/device/{todo_id}/complete"
        
        # 添加查询参数
        params = {}
        if hasattr(conn, 'agent_id') and conn.agent_id:
            params["agentId"] = conn.agent_id
        if hasattr(conn, 'device_id') and conn.device_id:
            params["deviceId"] = conn.device_id
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.put(complete_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                logger.bind(tag=TAG).info(f"待办 {todo_id} 已标记为完成")
                
                # 获取更新后的待办列表
                todo_list = get_todo_list_after_action(conn, manager_api_url, api_key)
                
                # 推送待办列表到设备端显示（即使是空列表也要推送，让设备端刷新界面）
                push_todo_list_to_device(conn, todo_list)
                
                # 构建简洁的回复文本（不包含格式化列表，避免TTS拆分）
                reply_text = "好的，已将待办标记为完成"
                if title:
                    reply_text = f"好的，'{title}'已经完成了"
                
                # 添加待办数量提示
                if todo_list:
                    remaining = len(todo_list)
                    reply_text += f"。当前还有{remaining}个待办事项"
                else:
                    reply_text += "。所有待办都已完成，真棒"
                
                # 使用 RESPONSE action 直接返回，不让 LLM 重新生成回复
                return ActionResponse(Action.RESPONSE, None, reply_text)
            else:
                error_msg = result.get("msg", "标记完成失败")
                logger.bind(tag=TAG).error(f"标记完成失败: {error_msg}")
                return ActionResponse(Action.REQLLM, f"抱歉，标记完成失败：{error_msg}", None)
        else:
            logger.bind(tag=TAG).error(f"完成待办接口返回错误: {response.status_code}, {response.text}")
            return ActionResponse(Action.REQLLM, "抱歉，标记完成时遇到网络错误，请稍后重试", None)
    
    except requests.exceptions.Timeout:
        logger.bind(tag=TAG).error("完成待办接口超时")
        return ActionResponse(Action.REQLLM, "抱歉，操作超时，请检查网络连接", None)
    except requests.exceptions.ConnectionError:
        logger.bind(tag=TAG).error("无法连接到待办服务")
        return ActionResponse(Action.REQLLM, "抱歉，无法连接到待办服务，请检查配置", None)
    except Exception as e:
        logger.bind(tag=TAG).error(f"完成待办异常: {e}", exc_info=True)
        return ActionResponse(Action.REQLLM, f"抱歉，操作时出现错误：{str(e)}", None)
