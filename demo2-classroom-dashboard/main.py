"""
main.py  -  趣配音 班级作业看板 FastAPI 后端

启动:
    uvicorn main:app --host 0.0.0.0 --port 8000

REST endpoints:
    GET  /                                       -> 看板 HTML
    GET  /api/kpi                                -> 顶部 4 个 KPI
    GET  /api/classes                            -> 班级下拉数据
    GET  /api/completion_rate?class_id=&start=&end=
                                                 -> 各班完成率柱状图
    GET  /api/avg_score_trend?class_id=&days=7   -> 均分趋势折线
    GET  /api/pending_students?class_id=&limit=10
                                                 -> 待补做名单 Top N
    GET  /api/popular_materials?limit=5          -> 最受欢迎素材饼图
    GET  /api/parent_checkin?class_id=&days=7    -> [扩展点] 家长打卡参与度

业务字段说明：
  - 完成率  = (completed + graded) / 全部 submissions
  - 均分    = AVG(score) over status='graded'
  - 活跃班级 = 近 7 天内至少 1 条 submitted_at 的班级数
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "data" / "classroom.db"
STATIC_DIR = BASE / "static"

app = FastAPI(
    title="趣配音 班级作业看板",
    description="K12 英语配音学习平台 - 班级作业看板 API",
    version="1.0.0",
)

# ------------------ 工具 ------------------

def get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"数据库未生成，请先执行: python3 seed.py  (期望路径 {DB_PATH})",
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_date(s: Optional[str], default: datetime) -> datetime:
    """容错解析 'YYYY-MM-DD' / ISO。"""
    if not s:
        return default
    try:
        if len(s) == 10:
            return datetime.strptime(s, "%Y-%m-%d")
        return datetime.fromisoformat(s)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"非法日期格式: {s}")


def week_window() -> tuple[str, str]:
    """本周 (近 7 天) ISO 时间窗。"""
    end = datetime.now()
    start = end - timedelta(days=7)
    return start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")


# ------------------ 看板首页 ------------------

@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html_file = STATIC_DIR / "index.html"
    if not html_file.exists():
        return HTMLResponse("<h1>index.html 缺失</h1>", status_code=500)
    return HTMLResponse(html_file.read_text(encoding="utf-8"))


# 兼容直接访问 /static/*
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ------------------ KPI ------------------

@app.get("/api/kpi")
def api_kpi() -> dict[str, Any]:
    """顶部 4 个 KPI: 总学生数 / 本周完成率 / 平均分 / 活跃班级数"""
    conn = get_conn()
    cur = conn.cursor()

    total_students = cur.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    start, end = week_window()
    # 本周内布置的作业的完成率
    row = cur.execute(
        """
        SELECT
          SUM(CASE WHEN s.status IN ('completed','graded') THEN 1 ELSE 0 END) AS done,
          COUNT(*) AS total
        FROM submissions s
        JOIN assignments a ON a.id = s.assignment_id
        WHERE a.assigned_at >= ? AND a.assigned_at <= ?
        """,
        (start, end),
    ).fetchone()
    done = row["done"] or 0
    total = row["total"] or 0
    completion_rate = round(done * 100.0 / total, 1) if total else 0.0

    avg_row = cur.execute(
        "SELECT AVG(score) AS avg_score FROM submissions WHERE status='graded'"
    ).fetchone()
    avg_score = round(avg_row["avg_score"], 1) if avg_row["avg_score"] is not None else 0.0

    active_classes_row = cur.execute(
        """
        SELECT COUNT(DISTINCT st.class_id) AS active
        FROM submissions s
        JOIN students st ON st.id = s.student_id
        WHERE s.submitted_at >= ?
        """,
        (start,),
    ).fetchone()
    active_classes = active_classes_row["active"] or 0

    conn.close()
    return {
        "total_students": total_students,
        "week_completion_rate": completion_rate,   # 百分比 (0-100)
        "avg_score": avg_score,
        "active_classes": active_classes,
        "window": {"start": start, "end": end},
    }


# ------------------ 班级列表 ------------------

@app.get("/api/classes")
def api_classes() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, grade FROM classes ORDER BY grade, name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ------------------ 各班完成率柱状图 ------------------

@app.get("/api/completion_rate")
def api_completion_rate(
    class_id: Optional[int] = Query(None, description="可选: 仅高亮该班，仍返回全部 10 个班"),
    start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
) -> dict[str, Any]:
    now = datetime.now()
    start_dt = parse_date(start, now - timedelta(days=7))
    end_dt = parse_date(end, now)

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT
          c.id        AS class_id,
          c.name      AS class_name,
          SUM(CASE WHEN s.status IN ('completed','graded') THEN 1 ELSE 0 END) AS done,
          COUNT(s.id) AS total
        FROM classes c
        LEFT JOIN students  st ON st.class_id = c.id
        LEFT JOIN submissions s
               ON s.student_id = st.id
              AND s.assignment_id IN (
                    SELECT id FROM assignments
                    WHERE assigned_at BETWEEN ? AND ?
                  )
        GROUP BY c.id, c.name
        ORDER BY c.grade, c.name
        """,
        (start_dt.isoformat(timespec="seconds"), end_dt.isoformat(timespec="seconds")),
    ).fetchall()
    conn.close()

    items = []
    for r in rows:
        done = r["done"] or 0
        total = r["total"] or 0
        rate = round(done * 100.0 / total, 1) if total else 0.0
        items.append({
            "class_id": r["class_id"],
            "class_name": r["class_name"],
            "done": done,
            "total": total,
            "rate": rate,
            "highlighted": (class_id is not None and r["class_id"] == class_id),
        })
    return {
        "items": items,
        "start": start_dt.strftime("%Y-%m-%d"),
        "end": end_dt.strftime("%Y-%m-%d"),
    }


# ------------------ 均分趋势 ------------------

@app.get("/api/avg_score_trend")
def api_avg_score_trend(
    class_id: Optional[int] = Query(None, description="可选: 限定班级"),
    days: int = Query(7, ge=1, le=60, description="最近 N 天"),
) -> dict[str, Any]:
    end_dt = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    start_dt = (end_dt - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0)

    # 生成日期序列
    series_days = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
                   for i in range(days)]

    conn = get_conn()
    sql = """
        SELECT substr(s.submitted_at, 1, 10) AS day,
               AVG(s.score)                  AS avg_score,
               COUNT(s.id)                   AS n
        FROM submissions s
        JOIN students st ON st.id = s.student_id
        WHERE s.status = 'graded'
          AND s.submitted_at IS NOT NULL
          AND s.submitted_at BETWEEN ? AND ?
    """
    params: list[Any] = [start_dt.isoformat(timespec="seconds"),
                         end_dt.isoformat(timespec="seconds")]
    if class_id is not None:
        sql += " AND st.class_id = ? "
        params.append(class_id)
    sql += " GROUP BY day ORDER BY day "

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    by_day = {r["day"]: (r["avg_score"], r["n"]) for r in rows}
    series = []
    for d in series_days:
        avg_score, n = by_day.get(d, (None, 0))
        series.append({
            "date": d,
            "avg_score": round(avg_score, 1) if avg_score is not None else None,
            "count": n,
        })
    return {"class_id": class_id, "days": days, "series": series}


# ------------------ 待补做名单 ------------------

@app.get("/api/pending_students")
def api_pending_students(
    class_id: Optional[int] = Query(None, description="可选: 限定班级"),
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """
    返回当前 status='pending' 数最多的学生列表（待补做榜）。
    只统计 due_at 已过 或 未来 3 天内的作业。
    """
    now = datetime.now()
    soon = now + timedelta(days=3)

    conn = get_conn()
    sql = """
        SELECT
          st.id        AS student_id,
          st.name      AS student_name,
          c.name       AS class_name,
          COUNT(s.id)  AS pending_count
        FROM students st
        JOIN classes c    ON c.id = st.class_id
        JOIN submissions s ON s.student_id = st.id
        JOIN assignments a ON a.id = s.assignment_id
        WHERE s.status = 'pending'
          AND a.due_at <= ?
    """
    params: list[Any] = [soon.isoformat(timespec="seconds")]
    if class_id is not None:
        sql += " AND st.class_id = ? "
        params.append(class_id)
    sql += """
        GROUP BY st.id, st.name, c.name
        ORDER BY pending_count DESC, st.name ASC
        LIMIT ?
    """
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return {
        "as_of": now.isoformat(timespec="seconds"),
        "items": [dict(r) for r in rows],
    }


# ------------------ 最受欢迎素材饼图 ------------------

@app.get("/api/popular_materials")
def api_popular_materials(
    limit: int = Query(5, ge=1, le=10),
) -> dict[str, Any]:
    """按 submissions 总条数（即被布置 × 学生数）统计素材使用量。"""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT
          m.id           AS material_id,
          m.title        AS title,
          COUNT(s.id)    AS submission_count,
          SUM(CASE WHEN s.status IN ('completed','graded') THEN 1 ELSE 0 END) AS done_count
        FROM materials m
        JOIN assignments a ON a.material_id = m.id
        JOIN submissions s ON s.assignment_id = a.id
        GROUP BY m.id, m.title
        ORDER BY submission_count DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}


# ------------------ [扩展点] 家长打卡参与度 ------------------
# 现场演示时 Copilot 改前端调用即可立刻有图。
# Prompt 示例见 README "现场加家长打卡指标"

@app.get("/api/parent_checkin")
def api_parent_checkin(
    class_id: Optional[int] = Query(None, description="可选: 限定班级"),
    days: int = Query(7, ge=1, le=60),
) -> dict[str, Any]:
    """
    家长打卡参与度:
      - bound_rate: 该班学生中绑定家长比例
      - checkin_rate: 近 N 天 submissions 中 parent_checkin=1 的比例
    """
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days)

    conn = get_conn()

    # 绑定率
    st_sql = "SELECT COUNT(*) AS total, SUM(parent_bound) AS bound FROM students"
    st_params: list[Any] = []
    if class_id is not None:
        st_sql += " WHERE class_id = ?"
        st_params.append(class_id)
    st_row = conn.execute(st_sql, st_params).fetchone()
    total_st = st_row["total"] or 0
    bound_st = st_row["bound"] or 0
    bound_rate = round(bound_st * 100.0 / total_st, 1) if total_st else 0.0

    # 打卡率
    sub_sql = """
        SELECT
          COUNT(*) AS total,
          SUM(s.parent_checkin) AS checkins
        FROM submissions s
        JOIN students st ON st.id = s.student_id
        WHERE s.submitted_at IS NOT NULL
          AND s.submitted_at BETWEEN ? AND ?
    """
    sub_params: list[Any] = [start_dt.isoformat(timespec="seconds"),
                              end_dt.isoformat(timespec="seconds")]
    if class_id is not None:
        sub_sql += " AND st.class_id = ? "
        sub_params.append(class_id)

    sub_row = conn.execute(sub_sql, sub_params).fetchone()
    total_sub = sub_row["total"] or 0
    checkins = sub_row["checkins"] or 0
    checkin_rate = round(checkins * 100.0 / total_sub, 1) if total_sub else 0.0

    conn.close()
    return {
        "class_id": class_id,
        "days": days,
        "total_students": total_st,
        "bound_students": bound_st,
        "bound_rate": bound_rate,            # %
        "submissions_in_window": total_sub,
        "checkins_in_window": checkins,
        "checkin_rate": checkin_rate,        # %
    }


# ------------------ Health ------------------

@app.get("/api/health")
def api_health() -> dict[str, str]:
    return {"status": "ok", "db_exists": str(DB_PATH.exists())}
