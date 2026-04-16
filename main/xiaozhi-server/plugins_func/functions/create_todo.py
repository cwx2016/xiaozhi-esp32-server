import requests
from datetime import datetime
import re
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

CREATE_TODO_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "create_todo",
        "description": (
            "创建待办事项，用于记录用户需要完成的任务或提醒。"
            "当用户说'提醒我...'、'帮我记住...'、'明天要...'等表达时调用此函数。"
            "可以智能解析时间信息（如：明天、后天、下周一、10点、下午3点等）和重复类型（每天、每周、每月）。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "待办事项的标题，简洁明了地描述任务内容，例如：买蔬菜、开会、健身等",
                },
                "content": {
                    "type": "string",
                    "description": "待办事项的详细内容或备注信息，可选参数",
                },
                "due_date": {
                    "type": "string",
                    "description": "截止时间，格式为YYYY-MM-DD HH:mm:ss，如果用户没有指定具体时间，可以根据相对时间推算，可选参数",
                },
                "priority": {
                    "type": "string",
                    "description": "优先级：high(高)、medium(中)、low(低)，默认为medium",
                    "enum": ["high", "medium", "low"],
                },
                "repeat_type": {
                    "type": "string",
                    "description": "重复类型：none(不重复)、daily(每天)、weekly(每周)、monthly(每月)，默认为none",
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
    
    # 处理"明天"
    if "明天" in time_str or "明日" in time_str:
        from datetime import timedelta
        target_date = now.date() + timedelta(days=1)
    # 处理"后天"
    elif "后天" in time_str:
        from datetime import timedelta
        target_date = now.date() + timedelta(days=2)
    # 处理"下周一"到"下周日"
    elif re.search(r'下[周一二三四五六日]', time_str):
        from datetime import timedelta
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
    # 处理"下周"
    elif "下周" in time_str:
        from datetime import timedelta
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
        todo_config = conn.config.get("plugins", {}).get("create_todo", {})
        manager_api_url = todo_config.get("manager_api_url", "http://localhost:8080")
        api_key = todo_config.get("api_key", "")
        
        if not manager_api_url or "你" in manager_api_url:
            return ActionResponse(
                Action.REQLLM,
                "待办功能未正确配置，请联系管理员配置manager-api地址",
                None
            )
        
        # 构建请求URL - TodoController的路径是 /todo/voice/create
        url = f"{manager_api_url}/todo/voice/create"
        
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
        
        # 如果有优先级，添加到payload
        if priority and priority != "medium":
            payload["priority"] = priority
        
        # 如果有重复类型，添加到payload
        if repeat_type and repeat_type != "none":
            payload["repeatType"] = repeat_type
        
        logger.bind(tag=TAG).info(f"调用待办创建接口: {url}, 参数: {payload}")
        
        # 发送请求
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                todo_id = result.get("data")
                success_msg = f"已为您创建待办事项：{title}"
                if due_date:
                    success_msg += f"，截止时间：{due_date}"
                logger.bind(tag=TAG).info(f"待办创建成功，ID: {todo_id}")
                return ActionResponse(Action.REQLLM, success_msg, None)
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
