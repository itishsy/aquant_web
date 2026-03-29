"""项目配置"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 数据目录
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    # 日志目录
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    
    # 默认配置
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # 日志级别
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # 数据库URL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
    
    # API密钥
    API_KEY = os.getenv("API_KEY", "")