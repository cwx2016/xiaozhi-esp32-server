import requests
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

DELETE_TODO_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "delete_todo",
        "description": (
            "删除待办事项。当用户想取消某个任务或删除不需要的待办时使用。"
            "例如：'删除买菜的待办'、'取消记周报的任务'、'把吃饭的提醒删掉'等。"
            "需要提供待办的ID或标题来识别要删除的待办。"
            "注意：删除操作不可恢复，请谨慎使用。"
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
                    "description": "待办事项的标题或关键词。用于模糊匹配要删除的待办。如果提供了todo_id，此参数可选。",
                },
            },
            "required": [],
        },
    },
}


@register_function("delete_todo", DELETE_TODO_FUNCTION_DESC, ToolType.SYSTEM_CTL)
def delete_todo(conn: "ConnectionHandler", todo_id: str = None, title: str = None):
    """
    删除待办事项（逻辑删除）
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
        
        logger.bind(tag=TAG).info(f"delete_todo - 收到请求: todo_id={todo_id}, title={title}")
        
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
            return ActionResponse(Action.REQLLM, "请提供待办ID或标题，例如：'删除买菜的待办'", None)
        
        # 二次确认：询问用户是否确定删除
        # 这里直接执行删除，LLM会在回复中提醒用户
        
        # 调用删除接口
        delete_url = f"{manager_api_url}/xiaozhi/todo/{todo_id}"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.delete(delete_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                logger.bind(tag=TAG).info(f"待办 {todo_id} 已删除")
                
                # 构建回复文本
                reply_text = "好的，已将待办删除！🗑️"
                if title:
                    reply_text = f"好的，'{title}'这个待办已经删除了！🗑️"
                
                return ActionResponse(Action.REQLLM, reply_text, None)
            else:
                error_msg = result.get("msg", "删除失败")
                logger.bind(tag=TAG).error(f"删除待办失败: {error_msg}")
                return ActionResponse(Action.REQLLM, f"抱歉，删除失败：{error_msg}", None)
        else:
            logger.bind(tag=TAG).error(f"删除待办接口返回错误: {response.status_code}, {response.text}")
            return ActionResponse(Action.REQLLM, "抱歉，删除时遇到网络错误，请稍后重试", None)
    
    except requests.exceptions.Timeout:
        logger.bind(tag=TAG).error("删除待办接口超时")
        return ActionResponse(Action.REQLLM, "抱歉，操作超时，请检查网络连接", None)
    except requests.exceptions.ConnectionError:
        logger.bind(tag=TAG).error("无法连接到待办服务")
        return ActionResponse(Action.REQLLM, "抱歉，无法连接到待办服务，请检查配置", None)
    except Exception as e:
        logger.bind(tag=TAG).error(f"删除待办异常: {e}", exc_info=True)
        return ActionResponse(Action.REQLLM, f"抱歉，操作时出现错误：{str(e)}", None)
