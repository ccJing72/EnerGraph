"""初始化大模型"""
from langchain_openai import ChatOpenAI
import os
import yaml
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    """初始化任意模型"""
    with open("config/agent_config.yaml") as f:
        config = yaml.safe_load(f)

    return ChatOpenAI(
        model=config["model"]["name"],
        temperature=config["model"]["temperature"],
        max_tokens=config["model"]["max_tokens"],
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE"),
    )