# ===================== 运势推送脚本（GitHub Actions 优化版）=====================
import requests
import schedule
import time
import logging
import os
from datetime import datetime

# --------------------- 日志配置 ---------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fortune_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --------------------- 读取密钥 ---------------------
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN')

if not DEEPSEEK_API_KEY:
    logging.error("❌ 未找到 DeepSeek API 密钥！")
    exit(1)
if not PUSHPLUS_TOKEN:
    logging.error("❌ 未找到 PushPlus Token！")
    exit(1)

# --------------------- 检测运行环境 ---------------------
IN_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'

# --------------------- 获取运势 ---------------------
def get_today_fortune():
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    request_data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "生成一段励志图文，要求：你就是毛泽东本人亲自对二三十岁的在低谷期和身处绝境的年青人加油打气，点燃他们心中的希望，可以包含毛泽东语录诗词选集内容等，也可加毛泽东亲身经历等故事，用亲切幽默的口吻轻松有趣，内容一定要做到给人希望启迪智慧的效果，每天内容必须不重复。"}],
        "temperature": 0.8,
        "max_tokens": 500
    }
    try:
        logging.info("📡 调用 DeepSeek API...")
        response = requests.post(url, json=request_data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        fortune_text = result['choices'][0]['message']['content'].strip()
        logging.info("✅ 运势生成成功")
        return fortune_text
    except Exception as e:
        logging.error(f"❌ 获取运势失败: {str(e)}")
        return None

# --------------------- 推送微信 ---------------------
def push_to_wechat(content):
    if not content:
        logging.warning("⚠️ 内容为空，跳过推送")
        return False
    url = "https://www.pushplus.plus/send"
    push_data = {
        "token": PUSHPLUS_TOKEN,
        "topic": "12211221",
        "title": f"毛爷爷碎碎念 🚀 {datetime.now().strftime('%Y-%m-%d')}",
        "content": content,
        "template": "txt"
    }
    try:
        logging.info("📤 推送至微信...")
        response = requests.post(url, data=push_data, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result.get('code') == 200:
            logging.info("✅ 推送成功！")
            return True
        else:
            logging.error(f"❌ PushPlus 错误: {result.get('msg')}")
            return False
    except Exception as e:
        logging.error(f"❌ 推送异常: {str(e)}")
        return False

# --------------------- 主任务 ---------------------
def main_task():
    logging.info("===== 开始执行运势任务 =====")
    fortune = get_today_fortune()
    if fortune:
        push_to_wechat(fortune)
    else:
        logging.error("❌ 未获取到运势")
    logging.info("===== 任务结束 =====\n")

# --------------------- 启动逻辑 ---------------------
if __name__ == "__main__":
    if IN_GITHUB_ACTIONS:
        # 在 GitHub Actions 中：立即执行一次并退出
        logging.info("🔄 检测到 GitHub Actions 环境，立即执行一次推送")
        main_task()
        logging.info("✅ 脚本执行完毕，退出")
    else:
        # 本地运行：设置定时任务（每天 22:12 北京时间 = 14:12 UTC）
        schedule.every().day.at("0:02").do(main_task)
        logging.info("🚀 本地定时模式已启动，将在每天 22:12 自动运行")
        logging.info("💡 按 Ctrl+C 停止")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("🛑 用户手动停止")
