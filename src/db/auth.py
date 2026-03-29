"""认证服务"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.models import User

class AuthService:
    @staticmethod
    def login(username, password):
        """用户登录"""
        user = User.authenticate(username, password)
        if user:
            return {"success": True, "message": "登录成功", "user": {"username": user.username}}
        else:
            return {"success": False, "message": "用户名或密码错误"}
    
    @staticmethod
    def register(username, password):
        """用户注册"""
        # 检查用户是否已存在
        existing_user = User.get_by_username(username)
        if existing_user:
            return {"success": False, "message": "用户已存在"}
        
        # 创建新用户
        try:
            user = User.create(username=username, password=password)
            return {"success": True, "message": "注册成功", "user": {"username": user.username}}
        except Exception as e:
            return {"success": False, "message": f"注册失败: {str(e)}"}
