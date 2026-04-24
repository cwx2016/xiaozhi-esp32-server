import requests
from datetime import datetime, timedelta
import re
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
                "status": todo.get("status", 0),
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


CREATE_TODO_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "create_todo",
        "description": (
            "创建待办事项提醒。当用户表达需要记住某事、提醒做某事、安排任务时使用。"
            "例如：'明天10点提醒我买蔬菜'、'帮我记住下午开会'、'后天要去医院'等。"
            "可以解析时间信息（明天、后天、下周一、10点、下午3点等）和重复类型（每天、每周、每月）。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "待办事项的标题或主要内容，例如：买蔬菜、开会、健身。从用户话语中提取核心任务。",
                },
                "content": {
                    "type": "string",
                    "description": "待办的详细说明或备注，可选。如果用户没有提供额外信息，可以为空字符串。",
                },
                "due_date": {
                    "type": "string",
                    "description": "截止时间，格式为YYYY-MM-DD HH:mm:ss。如果用户提到时间（如明天10点），需要解析并填入；如果没有提到时间，可以不传或传null。",
                },
                "priority": {
                    "type": "string",
                    "description": "优先级：high(高/紧急/重要)、medium(中/普通)、low(低)。默认为medium。如果用户说'紧急'、'重要'则设为high。",
                    "enum": ["high", "medium", "low"],
                },
                "repeat_type": {
                    "type": "string",
                    "description": "重复类型：none(不重复/一次性)、daily(每天/每日)、weekly(每周)、monthly(每月)。如果用户说'每天'、'每周'等，设置对应值；否则为none。",
                    "enum": ["none", "daily", "weekly", "monthly"],
                },
            },
            "required": ["title"],
        },
    },
}


def parse_relative_time(time_str: str) -> str:
    """
    解析相对时间字符串，转换为绝对时间
    支持：明天、后天、下周一、下周、10点、下午3点、晚上8点半等
    """
    if not time_str or not time_str.strip():
        return None
    
    now = datetime.now()
    time_str = time_str.strip()
    
    # 解析日期部分
    target_date = now.date()
    
    # 处理“明天”
    if "明天" in time_str or "明日" in time_str:
        target_date = now.date() + timedelta(days=1)
    # 处理“后天”
    elif "后天" in time_str:
        target_date = now.date() + timedelta(days=2)
    # 处理“下周一”到“下周日”
    elif re.search(r'下[周一二三四五六日]', time_str):
        weekday_map = {
            '一': 0, '二': 1, '三': 2, '四': 3, 
            '五': 4, '六': 5, '日': 6, '天': 6
        }
        match = re.search(r'下周([一二三四五六日天])', time_str)
        if match:
            target_weekday = weekday_map[match.group(1)]
            days_ahead = target_weekday - now.weekday()
            if days_ahead <= 0:  # 目标日期在本周，则跳到下周
                days_ahead += 7
            days_ahead += 7  # 再加一周
            target_date = now.date() + timedelta(days=days_ahead)
    # 处理“下周”
    elif "下周" in time_str:
        days_ahead = 7 - now.weekday() + 7
        target_date = now.date() + timedelta(days=days_ahead)
    
    # 解析时间部分
    target_hour = 9  # 默认早上9点
    target_minute = 0
    
    # 匹配具体时间，如"10点"、"10点30分"、"10点半"
    time_match = re.search(r'(\d{1,2})点(\d{1,2})?[分半]?', time_str)
    if time_match:
        target_hour = int(time_match.group(1))
        if time_match.group(2):
            minute_str = time_match.group(2)
            if '半' in minute_str or minute_str == '30':
                target_minute = 30
            else:
                target_minute = int(minute_str)
    
    # 处理时间段修饰词
    if '上午' in time_str or '早上' in time_str:
        if not time_match:  # 如果没有具体时间，默认9点
            target_hour = 9
    elif '中午' in time_str:
        if not time_match:
            target_hour = 12
    elif '下午' in time_str:
        if time_match and target_hour < 12:
            target_hour += 12
        elif not time_match:
            target_hour = 14
    elif '晚上' in time_str or '傍晚' in time_str:
        if time_match and target_hour < 12:
            target_hour += 12
        elif not time_match:
            target_hour = 19
    elif '凌晨' in time_str:
        if time_match and target_hour >= 12:
            target_hour -= 12
        elif not time_match:
            target_hour = 0
    
    # 组合成完整的时间字符串
    try:
        target_datetime = datetime(
            target_date.year, target_date.month, target_date.day,
            target_hour, target_minute, 0
        )
        return target_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.bind(tag=TAG).error(f"时间解析失败: {e}")
        return None


@register_function("create_todo", CREATE_TODO_FUNCTION_DESC, ToolType.SYSTEM_CTL)
def create_todo(
    conn: "ConnectionHandler",
    title: str,
    content: str = "",
    due_date: str = None,
    priority: str = "medium",
    repeat_type: str = "none"
):
    """
    创建待办事项
    :param conn: 连接对象
    :param title: 待办标题
    :param content: 待办内容
    :param due_date: 截止时间
    :param priority: 优先级
    :param repeat_type: 重复类型
    :return: ActionResponse
    """
    try:
        # 获取manager-api的配置
        plugins_config = conn.config.get("plugins", {})
        todo_config = plugins_config.get("create_todo", {})
        
        # 调试日志：输出完整的配置信息
        logger.bind(tag=TAG).info(f"plugins配置: {list(plugins_config.keys())}")
        logger.bind(tag=TAG).info(f"create_todo配置: {todo_config}")
        
        manager_api_url = todo_config.get("manager_api_url", "http://localhost:8002")
        api_key = todo_config.get("api_key", "")
        
        # 强制修正错误的端口配置（兜底逻辑）
        # 支持的错误端口列表：8080, 8082 等常见错误
        incorrect_ports = [":8080", ":8082", ":8088", ":9090"]
        for incorrect_port in incorrect_ports:
            if incorrect_port in manager_api_url:
                correct_url = manager_api_url.replace(incorrect_port, ":8002")
                logger.bind(tag=TAG).warning(f"检测到错误的端口{incorrect_port}，自动修正为8002")
                logger.bind(tag=TAG).warning(f"原URL: {manager_api_url}")
                logger.bind(tag=TAG).warning(f"修正后: {correct_url}")
                manager_api_url = correct_url
                break
        
        logger.bind(tag=TAG).info(f"最终使用的manager_api_url: {manager_api_url}")
        
        if not manager_api_url or "你" in manager_api_url:
            return ActionResponse(
                Action.REQLLM,
                "待办功能未正确配置，请联系管理员配置manager-api地址",
                None
            )
        
        # 构建请求URL - TodoController的路径是 /xiaozhi/todo/voice/create
        # 注意：manager-api的context-path是/xiaozhi
        url = f"{manager_api_url}/xiaozhi/todo/voice/create"
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 构建请求体
        payload = {
            "title": title,
            "content": content or "",
            "agentId": getattr(conn, 'agent_id', ''),
            "deviceId": getattr(conn, 'device_id', '')
        }
        
        # 如果有截止时间，添加到payload
        if due_date:
            payload["dueDate"] = due_date
        
        # 如果有优先级且不是默认的low，添加到payload
        if priority and priority != "low":
            payload["priority"] = priority
        
        # 如果有重复类型且不是默认的none，添加到payload
        if repeat_type and repeat_type != "none":
            payload["repeatType"] = repeat_type
        
        logger.bind(tag=TAG).info(f"调用待办创建接口: {url}, 参数: {payload}")
        
        # 发送请求
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                todo_id = result.get("data")
                
                # 获取更新后的待办列表
                todo_list = get_todo_list_after_action(conn, manager_api_url, api_key)
                
                # 推送待办列表到设备端显示
                if todo_list:
                    push_todo_list_to_device(conn, todo_list)
                
                # 构建简洁的回复文本（不包含格式化列表，避免TTS拆分）
                success_msg = f"已为您创建待办事项：{title}"
                if due_date:
                    # 提取日期和时间部分，简化显示
                    try:
                        dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                        success_msg += f"，{dt.strftime('%m月%d日%H点%M分')}"
                    except:
                        success_msg += f"，{due_date[:16]}"
                
                # 添加待办数量提示
                if todo_list:
                    remaining = len(todo_list)
                    success_msg += f"。当前还有{remaining}个待办事项"
                
                # 使用 RESPONSE action 直接返回，不让 LLM 重新生成回复
                return ActionResponse(Action.RESPONSE, None, success_msg)
            else:
                error_msg = result.get("msg", "创建待办失败")
                logger.bind(tag=TAG).error(f"待办创建失败: {error_msg}")
                return ActionResponse(Action.REQLLM, f"抱歉，创建待办失败：{error_msg}", None)
        else:
            logger.bind(tag=TAG).error(f"待办创建接口返回错误: {response.status_code}, {response.text}")
            return ActionResponse(Action.REQLLM, "抱歉，创建待办时遇到网络错误，请稍后重试", None)
    
    except requests.exceptions.Timeout:
        logger.bind(tag=TAG).error("待办创建接口超时")
        return ActionResponse(Action.REQLLM, "抱歉，创建待办超时，请检查网络连接", None)
    except requests.exceptions.ConnectionError:
        logger.bind(tag=TAG).error("无法连接到待办服务")
        return ActionResponse(Action.REQLLM, "抱歉，无法连接到待办服务，请检查配置", None)
    except Exception as e:
        logger.bind(tag=TAG).error(f"创建待办异常: {e}", exc_info=True)
        return ActionResponse(Action.REQLLM, f"抱歉，创建待办时出现错误：{str(e)}", None)
