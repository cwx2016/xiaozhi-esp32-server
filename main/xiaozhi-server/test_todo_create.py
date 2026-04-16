"""
待办创建工具测试脚本
用于测试时间解析和接口调用功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugins_func.functions.create_todo import parse_relative_time
from datetime import datetime


def test_time_parsing():
    """测试时间解析功能"""
    print("=" * 60)
    print("时间解析功能测试")
    print("=" * 60)
    
    test_cases = [
        # (输入, 期望输出模式)
        ("明天", "明天的日期"),
        ("后天", "后天的日期"),
        ("明天10点", "明天10:00"),
        ("下午3点", "当天15:00"),
        ("晚上8点半", "当天20:30"),
        ("下周一", "下周一的日期"),
        ("下周", "下周一的日期"),
        ("早上9点", "当天09:00"),
        ("中午12点", "当天12:00"),
    ]
    
    now = datetime.now()
    print(f"\n当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for input_str, expected in test_cases:
        result = parse_relative_time(input_str)
        status = "✅" if result else "❌"
        print(f"{status} 输入: {input_str:15} => 输出: {result:25} (期望: {expected})")
    
    print("\n" + "=" * 60)


def test_api_call():
    """测试API调用（需要配置正确的manager-api地址）"""
    print("\n" + "=" * 60)
    print("API调用测试")
    print("=" * 60)
    
    # 这里可以添加实际的API调用测试
    # 需要模拟 conn 对象
    
    print("\n提示: 要测试完整的API调用，请:")
    print("1. 确保 manager-api 服务正在运行")
    print("2. 配置正确的 manager_api_url")
    print("3. 通过小智设备进行语音测试")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n" + "🚀 待办创建工具测试\n")
    
    # 测试时间解析
    test_time_parsing()
    
    # 测试API调用
    test_api_call()
    
    print("\n✨ 测试完成!\n")
