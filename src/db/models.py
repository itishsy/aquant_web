"""用户模型"""
import hashlib
import os
import sys

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from dotenv import load_dotenv

# 显式加载项目根目录 .env，确保数据库配置从 .env 读取
load_dotenv(os.path.join(project_root, '.env'))

from peewee import (
    Model,
    CharField,
    MySQLDatabase,
    AutoField,
    DecimalField,
    IntegerField,
    DateTimeField,
    TextField,
    ForeignKeyField,
    fn,
)
# 数据库连接配置
db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'root'),
    'database': os.getenv('MYSQL_DATABASE', 'test'),
    'connect_timeout': int(os.getenv('MYSQL_CONNECT_TIMEOUT', 5)),
}

# 创建数据库实例
db = MySQLDatabase(
    db_config['database'],
    host=db_config['host'],
    port=db_config['port'],
    user=db_config['user'],
    password=db_config['password'],
    connect_timeout=db_config['connect_timeout'],
)

class Signal(Model):
    id = AutoField()
    code = CharField()  # 票据
    name = CharField()  # 名称
    freq = CharField()  # 级别
    dt = CharField()  # 信号时间
    price = DecimalField()  # 价格
    strategy = CharField()  # 策略
    stage = CharField()  # 阶段
    status = IntegerField()  # 状态： 0 新建 1 自选 2 交易 3 弃用
    notify = IntegerField(null=True)  # 通知 0 待通知， 1 已通知
    created = DateTimeField()
    updated = DateTimeField(null=True)
    
    class Meta:
        database = db
        table_name = 'signal'


class User(Model):
    username = CharField(max_length=50, unique=True)
    password = CharField(max_length=64)
    
    class Meta:
        database = db
        table_name = 'user'
    
    def _hash_password(self, password):
        """对密码进行哈希处理"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """验证密码"""
        return self.password == self._hash_password(password)
    
    @classmethod
    def authenticate(cls, username, password):
        """用户认证"""
        try:
            user = cls.get(cls.username == username)
            if user.check_password(password):
                return user
            return None
        except Exception as e:
            return None
    
    @classmethod
    def get_by_username(cls, username):
        """根据用户名获取用户，不验证密码"""
        try:
            return cls.get(cls.username == username)
        except Exception as e:
            return None
    
    def save(self, *args, **kwargs):
        """保存用户时对密码进行哈希处理"""
        self.password = self._hash_password(self.password)
        return super(User, self).save(*args, **kwargs)


class Review(Model):
    id = AutoField()
    date = CharField()  # 日期
    cjl = CharField()   # 成交量
    zs = CharField()  # 指数
    szs = CharField()  # 上涨数
    
    zt = CharField()  # 涨停数
    zt1 = CharField()  # 一板数
    zt2 = CharField()  # 二板数
    zt3 = CharField()  # 三板数
    zth = CharField()  # 高板数
    ztd = CharField()  # 最高板
    ztm = CharField()  # 连板数
    
    fund = CharField()      # 资金动向
    subject = CharField()   # 今日机会
    chance = CharField()   # 長線机会
    tuyere = CharField()     # 风口
    latent = CharField()    # 潜伏
    
    topic = CharField()  # 同花顺热门话题
    concept = CharField()     # 同花顺热门题材板块
    
    notify = IntegerField(null=True)  # 通知 0 待通知， 1 已通知
    created = DateTimeField()
    
    class Meta:
        database = db
        table_name = 'review'


class RevPan(Model):
    id = AutoField()
    date = CharField()
    cjl = CharField()
    zs = CharField()
    szl = CharField()
    zts = CharField()
    dts = CharField(null=True)
    fbl = CharField(null=True)
    zgb = CharField(null=True)
    review = CharField(null=True)
    concept = CharField(null=True)
    chance = CharField(max_length=1000, null=True)
    tuyere = CharField(max_length=1000, null=True)
    topic = CharField(max_length=1000, null=True)
    subject = CharField(max_length=1000, null=True)
    fund = CharField(max_length=1000, null=True)
    latent = CharField(max_length=1000, null=True)
    notify = IntegerField(default=0)
    created = DateTimeField()

    class Meta:
        database = db
        table_name = 'rev_pan'


class RevHot(Model):
    id = AutoField()
    date = CharField()
    code = CharField()
    name = CharField()
    price = CharField()
    change = CharField()
    reason = CharField()
    score = IntegerField(default=0)
    rank1 = IntegerField(default=0)
    rank2 = IntegerField(default=0)
    rank3 = IntegerField(default=0)
    comment = CharField()
    created = DateTimeField()

    class Meta:
        database = db
        table_name = 'rev_hot'


class RevZtb(Model):
    id = AutoField()
    date = CharField()
    code = CharField()
    name = CharField()
    change = CharField(null=True)
    time = CharField(null=True)
    price = CharField(null=True)
    strong = CharField(null=True)
    reason = CharField(max_length=255, null=True)
    bk1 = CharField(max_length=255, null=True)
    comment1 = CharField(max_length=255, null=True)
    bk2 = CharField(max_length=255, null=True)
    comment2 = CharField(max_length=255, null=True)
    created = DateTimeField()

    class Meta:
        database = db
        table_name = 'rev_ztb'


class TradeDailyPlan(Model):
    id = AutoField()
    trade_date = CharField(unique=True)
    position_pct = CharField(null=True)
    cash_pct = CharField(null=True)
    holdings_summary = TextField(null=True)
    market_view = TextField(null=True)
    operation_summary = TextField(null=True)
    tomorrow_plan = TextField(null=True)
    risk_watch = TextField(null=True)
    created = DateTimeField()
    updated = DateTimeField(null=True)

    class Meta:
        database = db
        table_name = 'trade_daily_plan'


class TradeDailyPlanItem(Model):
    id = AutoField()
    plan = ForeignKeyField(TradeDailyPlan, backref='items', on_delete='CASCADE')
    symbol = CharField(null=True)
    name = CharField(null=True)
    direction = CharField(null=True)
    plan_type = CharField(null=True)
    trigger_price = CharField(null=True)
    stop_price = CharField(null=True)
    target_price = CharField(null=True)
    planned_position_pct = CharField(null=True)
    thesis = TextField(null=True)
    sort_order = IntegerField(default=0)
    created = DateTimeField()

    class Meta:
        database = db
        table_name = 'trade_daily_plan_item'


class TradeWeeklyReview(Model):
    id = AutoField()
    week_key = CharField(unique=True)
    week_start = CharField()
    week_end = CharField()
    operation_review = TextField(null=True)
    trade_issues = TextField(null=True)
    next_week_plan = TextField(null=True)
    improvements = TextField(null=True)
    created = DateTimeField()
    updated = DateTimeField(null=True)

    class Meta:
        database = db
        table_name = 'trade_weekly_review'


class TradeMonthlySummary(Model):
    id = AutoField()
    month_key = CharField(unique=True)
    performance_review = TextField(null=True)
    winning_patterns = TextField(null=True)
    losing_patterns = TextField(null=True)
    experience_summary = TextField(null=True)
    next_month_goal = TextField(null=True)
    created = DateTimeField()
    updated = DateTimeField(null=True)

    class Meta:
        database = db
        table_name = 'trade_monthly_summary'


class Hot(Model):
    id = AutoField()
    date = CharField()  # 日期
    code = CharField()  # 票据
    name = CharField()  # 名称
    rank = IntegerField()  # 排名&連板屬
    bk = CharField()   # 板塊
    plate = CharField()   # 題材
    ztt = CharField()   # 涨停时间
    comment = CharField()   # 备注
    comment2 = CharField()   # 备注
    comment3 = CharField()   # 备注
    source = CharField()  # 来源(top、zt)
    created = DateTimeField()
    
    class Meta:
        database = db
        table_name = 'hot'

    @staticmethod
    def top_stocks(date, limit=10):
        """获取tgb、cls、ths综合排名前10的热门股票
        逻辑：按tgb、cls、ths的排名相加后，再重新排名取前10
        """
        # 获取各来源的热门股票
        tgb_stocks = {stock.code: stock.rank for stock in Hot.select().where(Hot.date == date, Hot.source == 'tgb')}
        cls_stocks = {stock.code: stock.rank for stock in Hot.select().where(Hot.date == date, Hot.source == 'cls')}
        ths_stocks = {stock.code: stock.rank for stock in Hot.select().where(Hot.date == date, Hot.source == 'ths')}

        # 获取所有唯一的股票代码
        all_codes = set(tgb_stocks.keys()) | set(cls_stocks.keys()) | set(ths_stocks.keys())

        # 计算每只股票的综合排名（各来源排名之和）
        stock_scores = {}
        for code in all_codes:
            # 如果某来源没有该股票，则使用一个较大的值（如100）作为默认排名
            tgb_rank = tgb_stocks.get(code, 100)
            cls_rank = cls_stocks.get(code, 100)
            ths_rank = ths_stocks.get(code, 100)
            total_rank = tgb_rank + cls_rank + ths_rank
            stock_scores[code] = total_rank

        # 按综合排名排序，取前limit名
        sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1])[:limit]
        top_codes = [code for code, _ in sorted_stocks]

        # 获取这些股票的详细信息
        top_stocks = Hot.select().where(Hot.date == date, Hot.code.in_(tuple(top_codes))).distinct()

        # 创建一个字典，用于按代码快速查找股票信息
        stock_dict = {stock.code: stock for stock in top_stocks}

        # 按综合排名顺序返回结果
        result = []
        for code in top_codes:
            if code in stock_dict:
                result.append(stock_dict[code])

        return result

    @staticmethod
    def top_bks(date):
        """查询的热门bk"""
        bks = Hot.select(Hot.bk, fn.Count(Hot.bk).alias('count')).where(Hot.date == date, Hot.source == 'zt').group_by(Hot.bk)
        # 转换为列表
        bks_list = [{'bk': bk.bk, 'count': bk.count} for bk in bks]
        # 按数量排序
        bks_list = sorted(bks_list, key=lambda x: x['count'], reverse=True)
        return bks_list

# 确保所有模型表都被创建
def create_tables():
    with db:
        db.create_tables([
            Signal,
            User,
            Review,
            Hot,
            RevPan,
            RevHot,
            RevZtb,
            TradeDailyPlan,
            TradeDailyPlanItem,
            TradeWeeklyReview,
            TradeMonthlySummary,
        ])

# 在应用启动时创建表
