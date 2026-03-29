import os
import sys

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入模型
from src.web.models import db, User

def reset_db():
    """重置数据库，清理用户表并初始化admin用户"""
    try:
        # 连接数据库
        db.connect()
        
        # 清理用户表
        User.delete().execute()
        print("用户表已清理")
        
        # 创建admin用户
        admin_user = User.create(username='admin', password='123456')
        print(f"管理员用户已创建: 用户名={admin_user.username}, 密码=123456")
        
    except Exception as e:
        print(f"数据库操作失败: {e}")
    finally:
        # 关闭数据库连接
        if not db.is_closed():
            db.close()

def init_db_with_admin():
    """初始化数据库表并创建admin用户"""
    try:
        # 连接数据库
        db.connect()
        
        # 创建用户表
        db.create_tables([User])
        print("用户表已创建或已存在")
        
        # 清理用户表
        User.delete().execute()
        print("用户表已清理")
        
        # 创建admin用户
        admin_user = User.create(username='admin', password='123456')
        print(f"管理员用户已创建: 用户名={admin_user.username}, 密码=123456")
        
    except Exception as e:
        print(f"数据库操作失败: {e}")
    finally:
        # 关闭数据库连接
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    init_db_with_admin()
