import time
import json
import uuid
import random
import asyncio
import requests
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils.dialogue import Message
from core.utils.util import audio_to_data
from core.providers.tts.dto.dto import SentenceType
from core.utils.wakeup_word import WakeupWordsConfig
from core.handle.sendAudioHandle import sendAudioMessage, send_tts_message
from core.utils.util import remove_punctuation_and_length, opus_datas_to_wav_bytes
from core.providers.tools.device_mcp import MCPClient, send_mcp_initialize_message

TAG = __name__

WAKEUP_CONFIG = {
    "refresh_time": 10,
    "responses": [
        "我一直都在呢，您请说。",
        "在的呢，请随时吩咐我。",
        "来啦来啦，请告诉我吧。",
        "您请说，我正听着。",
        "请您讲话，我准备好了。",
        "请您说出指令吧。",
        "我认真听着呢，请讲。",
        "请问您需要什么帮助？",
        "我在这里，等候您的指令。",
    ],
}

# 创建全局的唤醒词配置管理器
wakeup_words_config = WakeupWordsConfig()

# 用于防止并发调用wakeupWordsResponse的锁
_wakeup_response_lock = asyncio.Lock()


async def handleHelloMessage(conn: "ConnectionHandler", msg_json):
    """处理hello消息"""
    audio_params = msg_json.get("audio_params")
    if audio_params:
        format = audio_params.get("format")
        conn.logger.bind(tag=TAG).debug(f"客户端音频格式: {format}")
        conn.audio_format = format
        conn.welcome_msg["audio_params"] = audio_params
    features = msg_json.get("features")
    if features:
        conn.logger.bind(tag=TAG).debug(f"客户端特性: {features}")
        conn.features = features
        if features.get("mcp"):
            conn.logger.bind(tag=TAG).debug("客户端支持MCP")
            conn.mcp_client = MCPClient()
            # 发送初始化
            asyncio.create_task(send_mcp_initialize_message(conn))

    await conn.websocket.send(json.dumps(conn.welcome_msg))
    
    # 设备连接后，异步获取待办列表并推送到设备端
    asyncio.create_task(fetch_and_push_todo_list_on_startup(conn))


async def fetch_and_push_todo_list_on_startup(conn: "ConnectionHandler"):
    """
    设备开机启动时获取待办列表并推送到设备端
    :param conn: 连接对象
    """
    try:
        # 等待配置初始化完成（最多等待5秒）
        wait_count = 0
        while wait_count < 50:  # 50 * 0.1s = 5s
            if hasattr(conn, 'config') and conn.config:
                break
            await asyncio.sleep(0.1)
            wait_count += 1
        
        if not hasattr(conn, 'config') or not conn.config:
            conn.logger.bind(tag=TAG).warning("配置未初始化，跳过待办列表获取")
            return
        
        # 获取manager-api的配置
        todo_config = conn.config.get("plugins", {}).get("create_todo", {})
        
        if not todo_config:
            conn.logger.bind(tag=TAG).debug("未配置待办功能，跳过")
            return
        
        manager_api_url = todo_config.get("manager_api_url", "http://localhost:8002")
        api_key = todo_config.get("api_key", "")
        
        # 构建查询URL
        query_url = f"{manager_api_url}/xiaozhi/todo/device/list"
        params = {"limit": 50}
        
        # 添加agentId和deviceId参数
        if hasattr(conn, 'agent_id') and conn.agent_id:
            params["agentId"] = conn.agent_id
        if hasattr(conn, 'device_id') and conn.device_id:
            params["deviceId"] = conn.device_id
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # 发送HTTP请求
        response = requests.get(query_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                todo_list = result.get("data", [])
                
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
                
                # 推送消息到设备端
                if hasattr(conn, 'websocket') and conn.websocket:
                    await conn.websocket.send(json.dumps(push_message, ensure_ascii=False))
                    conn.logger.bind(tag=TAG).info(f"开机时已推送{len(device_todos)}个待办到设备")
            else:
                conn.logger.bind(tag=TAG).warning(f"获取待办列表失败: {result.get('msg', '未知错误')}")
        else:
            conn.logger.bind(tag=TAG).error(f"获取待办列表HTTP错误: {response.status_code}")
    
    except requests.exceptions.Timeout:
        conn.logger.bind(tag=TAG).error("获取待办列表超时")
    except requests.exceptions.ConnectionError:
        conn.logger.bind(tag=TAG).error("无法连接到待办服务")
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"开机获取待办列表异常: {e}", exc_info=True)


async def checkWakeupWords(conn: "ConnectionHandler", text):
    enable_wakeup_words_response_cache = conn.config[
        "enable_wakeup_words_response_cache"
    ]

    # 等待tts初始化，最多等待3秒
    start_time = time.time()
    while time.time() - start_time < 3:
        if conn.tts:
            break
        await asyncio.sleep(0.1)
    else:
        return False

    if not enable_wakeup_words_response_cache:
        return False

    _, filtered_text = remove_punctuation_and_length(text)
    if filtered_text not in conn.config.get("wakeup_words"):
        return False

    conn.just_woken_up = True
    await send_tts_message(conn, "start")

    # 获取当前音色
    voice = getattr(conn.tts, "voice", "default")
    if not voice:
        voice = "default"

    # 获取唤醒词回复配置
    response = wakeup_words_config.get_wakeup_response(voice)
    if not response or not response.get("file_path"):
        response = {
            "voice": "default",
            "file_path": "config/assets/wakeup_words_short.wav",
            "time": 0,
            "text": "我在这里哦！",
        }

    # 获取音频数据
    opus_packets = await audio_to_data(response.get("file_path"), use_cache=False)
    # 播放唤醒词回复
    conn.client_abort = False

    # 将唤醒词回复视为新会话，生成新的 sentence_id，确保流控器重置
    conn.sentence_id = str(uuid.uuid4().hex)

    conn.logger.bind(tag=TAG).info(f"播放唤醒词回复: {response.get('text')}")
    await sendAudioMessage(conn, SentenceType.FIRST, opus_packets, response.get("text"))
    await sendAudioMessage(conn, SentenceType.LAST, [], None)

    # 补充对话
    conn.dialogue.put(Message(role="assistant", content=response.get("text")))

    # 检查是否需要更新唤醒词回复
    if time.time() - response.get("time", 0) > WAKEUP_CONFIG["refresh_time"]:
        if not _wakeup_response_lock.locked():
            asyncio.create_task(wakeupWordsResponse(conn))
    return True


async def wakeupWordsResponse(conn: "ConnectionHandler"):
    if not conn.tts:
        return

    try:
        # 尝试获取锁，如果获取不到就返回
        if not await _wakeup_response_lock.acquire():
            return

        # 从预定义回复列表中随机选择一个回复
        result = random.choice(WAKEUP_CONFIG["responses"])
        if not result or len(result) == 0:
            return

        # 生成TTS音频
        tts_result = await asyncio.to_thread(conn.tts.to_tts, result)
        if not tts_result:
            return

        # 获取当前音色
        voice = getattr(conn.tts, "voice", "default")

        # 使用链接的sample_rate
        wav_bytes = opus_datas_to_wav_bytes(tts_result, sample_rate=conn.sample_rate)
        file_path = wakeup_words_config.generate_file_path(voice)
        with open(file_path, "wb") as f:
            f.write(wav_bytes)
        # 更新配置
        wakeup_words_config.update_wakeup_response(voice, file_path, result)
    finally:
        # 确保在任何情况下都释放锁
        if _wakeup_response_lock.locked():
            _wakeup_response_lock.release()
