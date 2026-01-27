#!/usr/bin/env python3
"""
监控任务执行状态并显示结果
"""
import sys
import time
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def format_duration(seconds):
    """格式化时长"""
    if seconds is None:
        return "N/A"
    try:
        sec = float(seconds)
        if sec < 60:
            return f"{sec:.2f}秒"
        elif sec < 3600:
            return f"{sec/60:.2f}分钟"
        else:
            return f"{sec/3600:.2f}小时"
    except:
        return str(seconds)

def monitor_task(execution_id: int, max_wait_minutes: int = 30):
    """监控任务执行状态"""
    print("=" * 60)
    print(f"监控任务执行状态 - Execution ID: {execution_id}")
    print("=" * 60)
    print()
    
    start_time = time.time()
    check_count = 0
    
    while True:
        try:
            response = requests.get(f"{BASE_URL}/tasks/executions/{execution_id}", timeout=5)
            if response.status_code != 200:
                print(f"❌ 获取任务状态失败: HTTP {response.status_code}")
                break
            
            data = response.json()
            status = data.get("status")
            check_count += 1
            
            # 显示当前状态
            elapsed = time.time() - start_time
            print(f"[检查 #{check_count}] {datetime.now().strftime('%H:%M:%S')} - 已运行: {format_duration(elapsed)}")
            print(f"  状态: {status}")
            print(f"  任务名称: {data.get('task_name')}")
            print(f"  目标日期: {data.get('target_date')}")
            
            if data.get("start_time"):
                start_time_str = data.get("start_time")
                print(f"  开始时间: {start_time_str}")
            
            if data.get("duration"):
                print(f"  执行时长: {format_duration(data.get('duration'))}")
            
            if data.get("result"):
                result = data.get("result")
                print(f"  执行结果:")
                print(f"    {json.dumps(result, ensure_ascii=False, indent=4)}")
            
            if data.get("error_message"):
                print(f"  错误信息: {data.get('error_message')}")
            
            print()
            
            # 如果任务完成，显示最终结果
            if status in ["success", "failed"]:
                print("=" * 60)
                print("任务执行完成")
                print("=" * 60)
                
                if status == "success":
                    print("✅ 任务执行成功")
                else:
                    print("❌ 任务执行失败")
                
                if data.get("result"):
                    result = data.get("result")
                    print(f"\n详细结果:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                
                if data.get("error_message"):
                    print(f"\n错误信息: {data.get('error_message')}")
                
                break
            
            # 检查超时
            if elapsed > max_wait_minutes * 60:
                print(f"\n⚠️  等待超时（{max_wait_minutes}分钟）")
                break
            
            # 等待5秒后再次检查
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n用户中断监控")
            break
        except Exception as e:
            print(f"❌ 监控出错: {str(e)}")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python monitor_task.py <execution_id> [max_wait_minutes]")
        sys.exit(1)
    
    execution_id = int(sys.argv[1])
    max_wait = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    monitor_task(execution_id, max_wait)
