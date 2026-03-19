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
        "messages": [{"role": "user", "content": "请你以毛泽东本人的身份、口吻与视角，写一篇纯文字励志小文章，无配图，适配图文文案风格，专门给二三十岁正处在低谷、陷入绝境的年轻人鼓劲打气、点燃希望、启迪智慧。
硬性要求
语气：亲切、幽默、轻松接地气，像长辈拉家常，不生硬、不教条
内容：必须自然融入毛泽东经典诗词、语录，结合毛泽东青年求学、革命低谷的亲身经历
效果：让人重燃信心、看清方向、获得力量
格式：纯文字短文，篇幅适中，适合阅读传播
唯一性：每次生成必须全新内容，轮换不同诗词、不同经历、不同切入点，绝不重复。"}],
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
        "title": f"毛爷爷的碎碎念 🚀 {datetime.now().strftime('%Y-%m-%d')}",
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
