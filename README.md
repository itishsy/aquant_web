# Aquant Web

短线交易辅助 Web 项目，使用 Flask + Peewee + MySQL，默认监听 `http://localhost:8080`。

## 当前结构

```text
aquant_web/
|- main.py                # 根目录统一启动入口
|- requirements.txt       # 运行依赖
|- pyproject.toml         # 项目元数据
|- setup.py               # setuptools 兼容配置
|- src/
|  |- config.py           # 环境变量与基础配置
|  `- web/
|     |- app.py           # Flask 应用、路由、API
|     |- auth.py          # 登录注册逻辑
|     |- db_init.py       # 数据表初始化
|     |- models.py        # Peewee 模型
|     |- reset_db.py      # 数据库重置工具
|     |- *.html           # 页面模板
|     `- style.css        # 全局样式
`- logs/
   |- app.log
   |- web_stdout.log
   `- web_stderr.log
```

## 启动方式

```powershell
.\.venv\Scripts\python.exe main.py
```

启动后访问 [http://localhost:8080](http://localhost:8080)。

## 环境变量

项目从根目录 `.env` 读取数据库配置，常用项如下：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=admin_db
```

## 主要页面

- `/login` 登录页
- `/index` 首页
- `/signal` 信号页
- `/review` 每日复盘
- `/trade` 交易计划、周复盘、月总结
- `/setting` 设置页

## 数据初始化

首次运行时会自动建表；如需手动初始化，可执行：

```powershell
.\.venv\Scripts\python.exe src\web\db_init.py
```

## 说明

项目已经整理为以 `src/web` 为核心的单体 Web 应用，根目录 `main.py` 是建议的统一入口。
