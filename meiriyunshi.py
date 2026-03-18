# 导入所需库：requests用于调用API，schedule用于定时任务，logging用于日志，os读取环境变量
import requests
import schedule
import time
import logging
import os
from datetime import datetime

# ===================== 1. 日志配置（出错时能看到详细信息） =====================
# 日志会同时输出到控制台和文件（fortune_log.txt），方便排查问题
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式：时间-级别-内容
    handlers=[
        logging.FileHandler('fortune_log.txt', encoding='utf-8'),  # 日志文件（自动生成）
        logging.StreamHandler()  # 控制台输出
    ]
)

# ===================== 2. 读取API密钥（安全起见，不硬编码） =====================
# 从系统环境变量读取密钥，避免直接写在代码里泄露
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN')

# 检查密钥是否配置成功
if not DEEPSEEK_API_KEY:
    logging.error("❌ 未找到DeepSeek API密钥！请先设置环境变量")
    exit(1)  # 密钥缺失则退出脚本
if not PUSHPLUS_TOKEN:
    logging.error("❌ 未找到PushPlus Token！请先设置环境变量")
    exit(1)

# ===================== 3. 调用DeepSeek API生成运势 =====================
def get_today_fortune():
    """调用DeepSeek API生成今日运势文本"""
    # DeepSeek官方API地址（通用对话接口）
    url = "https://api.deepseek.com/v1/chat/completions"
    # 请求头（必须包含授权信息和内容类型）
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    # API请求参数（按DeepSeek要求的格式）
    request_data = {
        "model": "deepseek-chat",  # DeepSeek通用对话模型
        "messages": [{"role": "user", "content": "生成一段今日运势，按照老黄历上的禁忌，还包括整体运势、幸运颜色、幸运数字，星座生肖等，语气轻松有趣，末尾加一句毛主席励志语录诗词等"}],
        "temperature": 0.8,  # 控制生成文本的随机性（0-1，越高越有趣）
        "max_tokens": 500  # 最大生成字符数（足够容纳运势内容）
    }

    try:
        logging.info("📡 开始调用DeepSeek API生成运势...")
        # 发送POST请求调用API
        response = requests.post(url, json=request_data, headers=headers, timeout=30)
        response.raise_for_status()  # 如果HTTP请求出错（如401/500），直接抛出异常
        
        # 解析API返回的结果
        result = response.json()
        fortune_text = result['choices'][0]['message']['content'].strip()
        logging.info("✅ 成功获取今日运势")
        return fortune_text  # 返回生成的运势文本

    # 捕获API调用相关的错误（如网络问题、密钥错误）
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ 调用DeepSeek API失败: {str(e)}")
        # 打印详细的错误响应（如果有）
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"API返回详情: {e.response.text}")
        return None
    # 捕获结果解析错误（如API返回格式异常）
    except KeyError as e:
        logging.error(f"❌ 解析运势结果失败，缺少字段: {str(e)}")
        return None
    # 捕获其他未知错误
    except Exception as e:
        logging.error(f"❌ 获取运势时发生未知错误: {str(e)}")
        return None

# ===================== 4. 推送运势到微信（PushPlus） =====================
def push_to_wechat(content):
    """通过PushPlus API将运势推送到微信"""
    if not content:  # 如果运势文本为空，直接返回
        logging.warning("⚠️ 运势内容为空，跳过推送")
        return False

    # PushPlus API地址
    url = "https://www.pushplus.plus/send"
    # 推送参数（token是你的密钥，content是推送内容）
    push_data = {
        "token": PUSHPLUS_TOKEN,
        "title": f"今日运势 🚀 {datetime.now().strftime('%Y-%m-%d')}",  # 推送标题（带日期）
        "content": content,
        "template": "txt"  # 推送格式（纯文本）
    }

    try:
        logging.info("📤 开始推送运势到微信...")
        # 发送POST请求推送
        response = requests.post(url, data=push_data, timeout=30)
        response.raise_for_status()
        
        # 解析推送结果
        result = response.json()
        if result.get('code') == 200:
            logging.info("✅ 成功推送运势到微信！")
            return True
        else:
            logging.error(f"❌ PushPlus推送失败: {result.get('msg', '未知错误')}")
            return False

    # 捕获推送相关错误
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ 调用PushPlus API失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"PushPlus返回详情: {e.response.text}")
        return False
    except Exception as e:
        logging.error(f"❌ 推送微信时发生未知错误: {str(e)}")
        return False

# ===================== 5. 主任务（获取运势+推送） =====================
def main_task():
    """每日8点执行的核心任务"""
    logging.info("===== 开始执行今日运势任务 =====")
    # 第一步：获取运势
    fortune_text = get_today_fortune()
    # 第二步：推送微信
    if fortune_text:
        push_to_wechat(fortune_text)
    else:
        logging.error("❌ 未能获取到运势，推送失败")
    logging.info("===== 今日运势任务执行结束 =====\n")

# ===================== 6. 定时任务+脚本主循环 =====================
if __name__ == "__main__":
    # 设置定时任务：每天上午8点执行main_task函数
    schedule.every().day.at("14:39").do(main_task)
    logging.info("🚀 运势推送脚本已启动！将在每天8:00自动运行")
    logging.info("💡 按 Ctrl+C 可手动停止脚本")

    # 保持脚本一直运行（每分钟检查一次是否到执行时间）
    try:
        while True:
            schedule.run_pending()  # 检查并执行待触发的定时任务
            time.sleep(60)  # 每分钟检查一次，减少电脑资源占用
    except KeyboardInterrupt:
        logging.info("🛑 用户手动停止脚本，程序退出")
    except Exception as e:
        logging.error(f"💥 脚本运行出错: {str(e)}")
