"""Flask app entry for aquant web."""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime

from flask import Blueprint, Flask, jsonify, redirect, render_template, request, send_from_directory
from flask_cors import CORS
from peewee import DoesNotExist

from src.db.auth import AuthService
from src.db.db_init import init_db
from src.db.models import (
    RevHot,
    RevPan,
    RevZtb,
    Signal,
    TradeDailyPlan,
    TradeDailyPlanItem,
    TradeMonthlySummary,
    TradeWeeklyReview,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "static")

app_bp = Blueprint("main", __name__, template_folder=TEMPLATE_DIR, static_folder=TEMPLATE_DIR)
server_shutdown_flag = False


def _now() -> datetime:
    return datetime.now()


def _safe_str(value) -> str:
    return "" if value is None else str(value)


def _date_or_default(date_text: str | None) -> str:
    if date_text:
        return date_text
    return datetime.now().strftime("%Y-%m-%d")


def serialize_signal(signal: Signal) -> dict:
    return {
        "id": signal.id,
        "code": signal.code,
        "name": signal.name,
        "freq": signal.freq,
        "dt": signal.dt,
        "price": float(signal.price) if signal.price else 0,
        "strategy": signal.strategy,
        "stage": signal.stage,
        "status": signal.status,
        "notify": signal.notify,
        "created": signal.created.strftime("%Y-%m-%d %H:%M:%S") if signal.created else "",
        "updated": signal.updated.strftime("%Y-%m-%d %H:%M:%S") if signal.updated else "",
    }


def serialize_trade_daily_item(item: TradeDailyPlanItem) -> dict:
    return {
        "id": item.id,
        "symbol": item.symbol,
        "name": item.name,
        "trade_type": item.plan_type,
        "logic": item.thesis,
        "sort_order": item.sort_order,
    }


def serialize_trade_daily(plan: TradeDailyPlan, include_items: bool = True) -> dict:
    data = {
        "id": plan.id,
        "trade_date": plan.trade_date,
        "position_pct": plan.position_pct,
        "cash_pct": plan.cash_pct,
        "holdings_summary": plan.holdings_summary,
        "market_view": plan.market_view,
        "operation_summary": plan.operation_summary,
        "tomorrow_plan": plan.tomorrow_plan,
        "risk_watch": plan.risk_watch,
        "created": plan.created.strftime("%Y-%m-%d %H:%M:%S") if plan.created else "",
        "updated": plan.updated.strftime("%Y-%m-%d %H:%M:%S") if plan.updated else "",
    }
    if include_items:
        items = (
            TradeDailyPlanItem.select()
            .where(TradeDailyPlanItem.plan == plan)
            .order_by(TradeDailyPlanItem.sort_order.asc(), TradeDailyPlanItem.id.asc())
        )
        action_list = [serialize_trade_daily_item(item) for item in items]
        # actions: new frontend field; items: backward-compatible alias
        data["actions"] = action_list
        data["items"] = action_list
    return data


def serialize_trade_weekly(review: TradeWeeklyReview) -> dict:
    return {
        "id": review.id,
        "week_key": review.week_key,
        "week_start": review.week_start,
        "week_end": review.week_end,
        "operation_review": review.operation_review,
        "trade_issues": review.trade_issues,
        "next_week_plan": review.next_week_plan,
        "improvements": review.improvements,
        "created": review.created.strftime("%Y-%m-%d %H:%M:%S") if review.created else "",
        "updated": review.updated.strftime("%Y-%m-%d %H:%M:%S") if review.updated else "",
    }


def serialize_trade_monthly(summary: TradeMonthlySummary) -> dict:
    return {
        "id": summary.id,
        "month_key": summary.month_key,
        "performance_review": summary.performance_review,
        "winning_patterns": summary.winning_patterns,
        "losing_patterns": summary.losing_patterns,
        "experience_summary": summary.experience_summary,
        "next_month_goal": summary.next_month_goal,
        "created": summary.created.strftime("%Y-%m-%d %H:%M:%S") if summary.created else "",
        "updated": summary.updated.strftime("%Y-%m-%d %H:%M:%S") if summary.updated else "",
    }


def serialize_market_review(review: RevPan) -> dict:
    return {
        "id": review.id,
        "date": review.date,
        "cjl": review.cjl,
        "zs": review.zs,
        "szl": review.szl,
        "zts": review.zts,
        "dts": review.dts,
        "fbl": review.fbl,
        "zgb": review.zgb,
        "review": review.review,
        "fund": review.fund,
        "subject": review.subject,
        "chance": review.chance,
        "tuyere": review.tuyere,
        "latent": review.latent,
        "topic": review.topic,
        "concept": review.concept,
        "notify": review.notify,
        "created": review.created.strftime("%Y-%m-%d %H:%M:%S") if review.created else "",
    }


def require_login_redirect():
    username = request.cookies.get("username")
    if not username:
        return redirect("/login")
    return None


@app_bp.route("/", methods=["GET"])
def home():
    username = request.cookies.get("username")
    return redirect("/index" if username else "/login")


@app_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or {}
    username = _safe_str(data.get("username")).strip()
    password = _safe_str(data.get("password")).strip()
    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

    result = AuthService.login(username, password)
    if result.get("success"):
        response = jsonify(result)
        response.set_cookie("username", result["user"]["username"], max_age=86400, path="/")
        return response, 200
    return jsonify(result), 401


@app_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = _safe_str(data.get("username")).strip()
    password = _safe_str(data.get("password")).strip()
    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
    result = AuthService.register(username, password)
    return jsonify(result), (200 if result.get("success") else 400)


@app_bp.route("/index", methods=["GET"])
def index():
    blocked = require_login_redirect()
    if blocked:
        return blocked
    return render_template("index.html")


@app_bp.route("/choice", methods=["GET"])
@app_bp.route("/signal", methods=["GET"])
def choice():
    blocked = require_login_redirect()
    if blocked:
        return blocked
    return render_template("choice.html")


@app_bp.route("/market", methods=["GET"])
def market():
    blocked = require_login_redirect()
    if blocked:
        return blocked
    return render_template("market.html")


@app_bp.route("/review", methods=["GET"])
@app_bp.route("/trade", methods=["GET"])
def review():
    blocked = require_login_redirect()
    if blocked:
        return blocked
    return render_template("review.html")


@app_bp.route("/setting", methods=["GET"])
def setting():
    blocked = require_login_redirect()
    if blocked:
        return blocked
    return render_template("setting.html")


@app_bp.route("/style.css", methods=["GET"])
def style_css():
    return send_from_directory(TEMPLATE_DIR, "style.css")


@app_bp.route("/api/signals", methods=["GET"])
def get_signals():
    try:
        signals = Signal.select().order_by(Signal.created.desc()).limit(60)
        return jsonify([serialize_signal(item) for item in signals])
    except Exception as exc:
        return jsonify([]), 200


@app_bp.route("/api/watchlist", methods=["GET"])
def get_watchlist():
    try:
        limit = request.args.get("limit", default=50, type=int)
        rows = (
            Signal.select()
            .where(Signal.status == 1)
            .order_by(Signal.updated.desc(), Signal.created.desc())
            .limit(max(1, min(limit, 100)))
        )
        return jsonify([serialize_signal(item) for item in rows])
    except Exception as exc:
        return jsonify([]), 200


@app_bp.route("/api/signals/<int:signal_id>/favorite", methods=["POST"])
def toggle_favorite(signal_id: int):
    try:
        signal = Signal.get_by_id(signal_id)
        signal.status = 0 if signal.status == 1 else 1
        signal.updated = _now()
        signal.save()
        return jsonify({"id": signal_id, "status": signal.status}), 200
    except DoesNotExist:
        return jsonify({"error": "signal not found"}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app_bp.route("/api/signals/<int:signal_id>/discard", methods=["POST"])
def discard_signal(signal_id: int):
    try:
        signal = Signal.get_by_id(signal_id)
        signal.status = 3
        signal.updated = _now()
        signal.save()
        return jsonify({"id": signal_id, "status": 3}), 200
    except DoesNotExist:
        return jsonify({"error": "signal not found"}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app_bp.route("/api/reviews/check/<string:date>", methods=["GET"])
def check_review(date: str):
    try:
        count = RevPan.select().where(RevPan.date == date).count()
        return jsonify({"result": count}), 200
    except Exception:
        return jsonify({"result": 0}), 200


@app_bp.route("/api/reviews/<int:review_id>/notify", methods=["POST"])
def mark_review_notified(review_id: int):
    try:
        review = RevPan.get_by_id(review_id)
        review.notify = 1
        review.save()
        return jsonify({"id": review_id, "notify": 1}), 200
    except DoesNotExist:
        return jsonify({"error": "review not found"}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app_bp.route("/api/reviews/<string:date>", methods=["GET"])
def get_review(date: str):
    try:
        review = RevPan.get_or_none(RevPan.date == date)
        return jsonify(serialize_market_review(review) if review else {}), 200
    except Exception as exc:
        return jsonify({}), 200


@app_bp.route("/api/hot_stocks/<string:date>", methods=["GET"])
def get_hot_stocks(date: str):
    try:
        rows = (
            RevHot.select()
            .where(RevHot.date == date)
            .order_by(RevHot.score.asc(), RevHot.id.asc())
            .limit(10)
        )
        payload = []
        for idx, row in enumerate(rows, start=1):
            payload.append(
                {
                    "id": idx,
                    "code": row.code,
                    "name": row.name,
                    "price": row.price,
                    "change": row.change,
                    "reason": row.reason,
                    "score": row.score,
                    "comment": row.comment,
                    "created": row.created.strftime("%Y-%m-%d %H:%M:%S") if row.created else "",
                }
            )
        return jsonify(payload), 200
    except Exception as exc:
        return jsonify([]), 200


@app_bp.route("/api/hot_plates/<string:date>", methods=["GET"])
def get_hot_plates(date: str):
    try:
        rows = (
            RevZtb.select()
            .where(RevZtb.date == date)
            .order_by(RevZtb.time.asc(), RevZtb.id.asc())
        )
        payload = []
        for row in rows:
            payload.append(
                {
                    "id": row.id,
                    "code": row.code,
                    "name": row.name,
                    "change": row.change,
                    "time": row.time,
                    "price": row.price,
                    "strong": row.strong,
                    "reason": row.reason,
                    "bk1": row.bk1,
                    "comment1": row.comment1,
                    "bk2": row.bk2,
                    "comment2": row.comment2,
                    "created": row.created.strftime("%Y-%m-%d %H:%M:%S") if row.created else "",
                }
            )
        return jsonify(payload), 200
    except Exception as exc:
        return jsonify([]), 200


def _list_review_daily():
    limit = request.args.get("limit", default=20, type=int)
    plans = (
        TradeDailyPlan.select()
        .order_by(TradeDailyPlan.trade_date.desc())
        .limit(max(1, min(limit, 60)))
    )
    return jsonify([serialize_trade_daily(item, include_items=False) for item in plans])


def _get_review_daily(trade_date: str):
    plan = TradeDailyPlan.get_or_none(TradeDailyPlan.trade_date == trade_date)
    return jsonify(serialize_trade_daily(plan) if plan else {})


def _save_review_daily():
    data = request.get_json(silent=True) or {}
    trade_date = _safe_str(data.get("trade_date")).strip()
    if not trade_date:
        return jsonify({"error": "trade_date is required"}), 400

    now = _now()
    plan = TradeDailyPlan.get_or_none(TradeDailyPlan.trade_date == trade_date)
    if plan:
        plan.position_pct = data.get("position_pct")
        plan.cash_pct = None
        plan.holdings_summary = None
        plan.market_view = None
        plan.operation_summary = data.get("operation_summary")
        plan.tomorrow_plan = data.get("tomorrow_plan")
        plan.risk_watch = data.get("risk_watch")
        plan.updated = now
        plan.save()
        TradeDailyPlanItem.delete().where(TradeDailyPlanItem.plan == plan).execute()
    else:
        plan = TradeDailyPlan.create(
            trade_date=trade_date,
            position_pct=data.get("position_pct"),
            cash_pct=None,
            holdings_summary=None,
            market_view=None,
            operation_summary=data.get("operation_summary"),
            tomorrow_plan=data.get("tomorrow_plan"),
            risk_watch=data.get("risk_watch"),
            created=now,
            updated=now,
        )

    actions = data.get("actions")
    if actions is None:
        actions = data.get("items") or []
    for index, item in enumerate(actions):
        if not any(
            [
                _safe_str(item.get("symbol")).strip(),
                _safe_str(item.get("name")).strip(),
                _safe_str(item.get("logic")).strip(),
                _safe_str(item.get("trade_type")).strip(),
            ]
        ):
            continue
        TradeDailyPlanItem.create(
            plan=plan,
            symbol=item.get("symbol"),
            name=item.get("name"),
            direction=None,
            plan_type=item.get("trade_type"),
            trigger_price=None,
            stop_price=None,
            target_price=None,
            planned_position_pct=None,
            thesis=item.get("logic"),
            sort_order=item.get("sort_order", index),
            created=now,
        )

    plan = TradeDailyPlan.get_by_id(plan.id)
    return jsonify(serialize_trade_daily(plan)), 200


def _list_review_weekly():
    limit = request.args.get("limit", default=12, type=int)
    reviews = (
        TradeWeeklyReview.select()
        .order_by(TradeWeeklyReview.week_start.desc())
        .limit(max(1, min(limit, 52)))
    )
    return jsonify([serialize_trade_weekly(item) for item in reviews])


def _get_review_weekly(week_key: str):
    review = TradeWeeklyReview.get_or_none(TradeWeeklyReview.week_key == week_key)
    return jsonify(serialize_trade_weekly(review) if review else {})


def _save_review_weekly():
    data = request.get_json(silent=True) or {}
    week_key = _safe_str(data.get("week_key")).strip()
    week_start = _safe_str(data.get("week_start")).strip()
    week_end = _safe_str(data.get("week_end")).strip()
    if not week_key or not week_start or not week_end:
        return jsonify({"error": "week_key, week_start and week_end are required"}), 400

    now = _now()
    review = TradeWeeklyReview.get_or_none(TradeWeeklyReview.week_key == week_key)
    payload = {
        "week_start": week_start,
        "week_end": week_end,
        "operation_review": data.get("operation_review"),
        "trade_issues": data.get("trade_issues"),
        "next_week_plan": data.get("next_week_plan"),
        "improvements": data.get("improvements"),
        "updated": now,
    }
    if review:
        for key, value in payload.items():
            setattr(review, key, value)
        review.save()
    else:
        review = TradeWeeklyReview.create(week_key=week_key, created=now, **payload)
    return jsonify(serialize_trade_weekly(review)), 200


def _list_review_monthly():
    limit = request.args.get("limit", default=12, type=int)
    rows = (
        TradeMonthlySummary.select()
        .order_by(TradeMonthlySummary.month_key.desc())
        .limit(max(1, min(limit, 24)))
    )
    return jsonify([serialize_trade_monthly(item) for item in rows])


def _get_review_monthly(month_key: str):
    summary = TradeMonthlySummary.get_or_none(TradeMonthlySummary.month_key == month_key)
    return jsonify(serialize_trade_monthly(summary) if summary else {})


def _save_review_monthly():
    data = request.get_json(silent=True) or {}
    month_key = _safe_str(data.get("month_key")).strip()
    if not month_key:
        return jsonify({"error": "month_key is required"}), 400

    now = _now()
    summary = TradeMonthlySummary.get_or_none(TradeMonthlySummary.month_key == month_key)
    payload = {
        "performance_review": data.get("performance_review"),
        "winning_patterns": data.get("winning_patterns"),
        "losing_patterns": data.get("losing_patterns"),
        "experience_summary": data.get("experience_summary"),
        "next_month_goal": data.get("next_month_goal"),
        "updated": now,
    }
    if summary:
        for key, value in payload.items():
            setattr(summary, key, value)
        summary.save()
    else:
        summary = TradeMonthlySummary.create(month_key=month_key, created=now, **payload)
    return jsonify(serialize_trade_monthly(summary)), 200


@app_bp.route("/api/review/daily", methods=["GET", "POST"])
@app_bp.route("/api/trade/daily", methods=["GET", "POST"])
def review_daily():
    if request.method == "GET":
        return _list_review_daily()
    return _save_review_daily()


@app_bp.route("/api/review/daily/<string:trade_date>", methods=["GET"])
@app_bp.route("/api/trade/daily/<string:trade_date>", methods=["GET"])
def review_daily_item(trade_date: str):
    return _get_review_daily(trade_date)


@app_bp.route("/api/review/weekly", methods=["GET", "POST"])
@app_bp.route("/api/trade/weekly", methods=["GET", "POST"])
def review_weekly():
    if request.method == "GET":
        return _list_review_weekly()
    return _save_review_weekly()


@app_bp.route("/api/review/weekly/<string:week_key>", methods=["GET"])
@app_bp.route("/api/trade/weekly/<string:week_key>", methods=["GET"])
def review_weekly_item(week_key: str):
    return _get_review_weekly(week_key)


@app_bp.route("/api/review/monthly", methods=["GET", "POST"])
@app_bp.route("/api/trade/monthly", methods=["GET", "POST"])
def review_monthly():
    if request.method == "GET":
        return _list_review_monthly()
    return _save_review_monthly()


@app_bp.route("/api/review/monthly/<string:month_key>", methods=["GET"])
@app_bp.route("/api/trade/monthly/<string:month_key>", methods=["GET"])
def review_monthly_item(month_key: str):
    return _get_review_monthly(month_key)


@app_bp.route("/@vite/client", methods=["GET"])
def vite_client():
    return "", 204


def run_with_shutdown_support(app: Flask, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    global server_shutdown_flag
    server_shutdown_flag = False

    from werkzeug.serving import make_server

    server = make_server(host, port, app, threaded=True)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    while not server_shutdown_flag:
        time.sleep(1)

    server.shutdown()
    server_thread.join()
    return "Server has been shut down"


def create_app() -> Flask:
    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=TEMPLATE_DIR)
    CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})

    with app.app_context():
        try:
            init_db()
        except Exception as exc:
            app.logger.exception("Database initialization failed: %s", exc)

    @app.route("/shutdown", methods=["GET"])
    def shutdown():
        global server_shutdown_flag
        server_shutdown_flag = True
        return "Server shutting down..."

    app.register_blueprint(app_bp)
    return app


def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, debug: bool = False):
    app = create_app()
    return run_with_shutdown_support(app, host=host, port=port)


if __name__ == "__main__":
    main()
