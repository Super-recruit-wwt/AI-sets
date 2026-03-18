import sys
import io
import json
import time
import os
import re
from openai import OpenAI

# 修复Windows控制台中文乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

client = OpenAI(
    api_key="sk-sp-503ab119dfe74700a26d48bd726d041e",
    base_url="https://coding.dashscope.aliyuncs.com/v1",
)

def get_session_json_path(script_dir: str) -> str:
    """
    生成会话JSON文件路径，格式：data/YYYYMMDD-编号.json

    Args:
        script_dir: 脚本所在目录的绝对路径

    Returns:
        完整的JSON文件路径，如：/path/to/data/20260318-3.json
    """
    # 1. 获取当前日期 YYYYMMDD
    current_date = time.strftime("%Y%m%d")

    # 2. 构建 data 目录路径
    data_dir = os.path.join(script_dir, "data")

    # 3. 确保 data 目录存在
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 4. 扫描当天已有的JSON文件，找到最大编号
    max_number = 0
    pattern = re.compile(r"^(\d{8})-(\d+)\.json$")

    try:
        for file_name in os.listdir(data_dir):
            match = pattern.match(file_name)
            if match:
                file_date = match.group(1)
                file_number = int(match.group(2))

                # 只统计当天的JSON文件
                if file_date == current_date:
                    max_number = max(max_number, file_number)
    except Exception as e:
        print(f"扫描文件时出错: {e}")

    # 5. 新编号 = 最大编号 + 1
    new_number = max_number + 1

    # 6. 创建新文件名
    new_file_name = f"{current_date}-{new_number}.json"
    new_file_path = os.path.join(data_dir, new_file_name)

    return new_file_path

class ChatRoom:
    """管理对话历史并负责JSON读写"""
    def __init__(self, filename="chat_history.json"):
        self.filename = filename
        self.history = []
        
        # 如果你想每次运行追加历史，可以解除下面的注释：
        # if os.path.exists(self.filename):
        #     with open(self.filename, 'r', encoding='utf-8') as f:
        #         self.history = json.load(f)

    def add_message(self, speaker: str, text: str):
        """添加一条新消息并立即保存到JSON"""
        msg = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "speaker": speaker,
            "text": text
        }
        self.history.append(msg)
        self.save_to_json()
        print(f"\n[{speaker}]: {text}")

    def save_to_json(self):
        """将对话历史持久化为JSON格式"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)

    def get_transcript(self) -> str:
        """生成供AI阅读的纯文本剧本"""
        return "\n".join([f"{m['speaker']}: {m['text']}" for m in self.history])

class Agent:
    """定义AI代理及其行为"""
    # "依次输入：AI名称；性格和背景；使用的模型（默认为qwen3.5-plus）；"
    def __init__(self, name: str, persona: str, model: str = "qwen3.5-plus"):
        self.name = name
        self.persona = persona
        self.model = model

    def generate_reply(self, chat_room: ChatRoom) -> str:
        """读取当前的房间对话历史，并生成回复"""
        transcript = chat_room.get_transcript()
        
        # 构建System Prompt，明确AI的人设和任务
        system_prompt = (
            f"你是 {self.name}。你的性格和背景是：{self.persona}。\n"
            "请根据提供的对话历史，给出你的回应。直接说出你的回答，不要加上你的名字前缀，也不要重复别人的话。"
        )

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"【当前对话历史】\n{transcript}\n\n现在轮到你发言了："}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"(API调用失败: {e})"

def main():
    # 使用绝对路径，确保JSON文件保存在脚本所在目录下的data文件夹
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = get_session_json_path(script_dir)
    room = ChatRoom(json_path)

    # 显示JSON文件保存位置
    print(f"📄 JSON文件: {json_path}\n")
    
    # 1. 定义两个立场不同的AI
    agent_a = Agent("AI科学家", "一位极度理性、注重数据和逻辑的计算机科学家，认为一切都可以用算法解释。","glm-5")
    agent_b = Agent("人文哲学家", "一位感性、关注伦理、道德和人类情感的哲学家，对纯粹的技术主义持怀疑态度。","kimi-k2.5")
    agent_c = Agent("金融学家", "一位理性的金融学家，擅长沉着冷静分析问题。","MiniMax-M2.5")
    agent_d = Agent("奥运冠军", "一位充满活力的体育运动员，对生活充满激情。","qwen3-max-2026-01-23")
    
    agents = [agent_a, agent_b,agent_c,agent_d]
    
    # 2. 设定初始讨论话题
    topic = "人类是否应该将所有决策权（包括司法和医疗）交给超级人工智能？"
    room.add_message("System", f"讨论开始，今日议题：{topic}")
    
    turn = 0
    print("==================================================")
    print("多主体AI聊天室已启动。")
    print("操作说明：")
    print("- 按【Enter】键：让下一个AI继续发言。")
    print("- 输入AI名称（如：AI科学家）并按Enter：让指定AI发言。")
    print("- 输入其他文字并按Enter：以人类身份插入对话。")
    print("- 输入【exit】：结束程序。")
    print(f"\n下一个发言的AI: {agents[turn % len(agents)].name}")
    print("==================================================")

    # 3. 循环对话机制
    while True:
        # 询问人类是否需要干预
        user_input = input("\n[按Enter继续 / 输入AI名称 / 插话 / 'exit'退出] > ").strip()

        # 处理用户输入
        if user_input.lower() == 'exit':
            print("聊天结束，已保存JSON文件。")
            break
        elif user_input == "":
            # 按Enter，让下一个AI发言
            current_agent = agents[turn % len(agents)]
        elif user_input in [agent.name for agent in agents]:
            # 输入了AI名称，找到对应的AI
            current_agent = next(agent for agent in agents if agent.name == user_input)
        else:
            # 输入了其他内容，作为人类插话
            room.add_message("人类(Admin)", user_input)
            # 继续让当前轮次的AI发言
            current_agent = agents[turn % len(agents)]

        # 让AI生成回复并加入房间
        reply = current_agent.generate_reply(room)
        room.add_message(current_agent.name, reply)

        # 更新轮次（只有按Enter或插话后才增加，指定AI发言不改变轮次）
        if user_input == "" or user_input not in [agent.name for agent in agents]:
            turn += 1

        # 提示下一个发言的AI
        next_agent = agents[turn % len(agents)]
        print(f"\n[提示] 下一个发言的AI: {next_agent.name}")

if __name__ == "__main__":
    main()
