# -*- coding: utf-8 -*-
"""
趣配音 K12 英语配音学习平台
Demo 1 · 配音素材自动打标签 (Streamlit + LiteLLM + SQLite)

现场演示路径:
  1. 启动: ./start.sh        → http://localhost:8501
  2. 单条模式: 粘贴字幕 → 5s 内出 JSON 卡片
  3. 批量模式: 上传 materials.json → 30s 内 10 条全部打完
  4. 历史记录: 侧边栏查询 SQLite
  5. .prompt.md tab: 直接展示教研沉淀模板

兜底: 设置 OFFLINE=1 → 直接读 ideal_tags.json, 现场断网也能跑通。
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# ============================================================
# 一、配置 & 常量
# ============================================================

APP_DIR = Path(__file__).resolve().parent
PROMPT_PATH = APP_DIR / "prompts" / "tag-material.prompt.md"
DEFAULT_MOCK_DIR = (APP_DIR / ".." / "mock-data").resolve()
MOCK_DATA_DIR = Path(os.environ.get("MOCK_DATA_DIR", str(DEFAULT_MOCK_DIR)))
MATERIALS_PATH = MOCK_DATA_DIR / "materials.json"
IDEAL_TAGS_PATH = MOCK_DATA_DIR / "ideal_tags.json"

DB_PATH = Path(os.environ.get("RESULTS_DB", str(APP_DIR / "data" / "results.db")))

OFFLINE = os.environ.get("OFFLINE", "0") == "1"
LITELLM_BASE_URL = os.environ.get("LITELLM_BASE_URL", "https://api.githubcopilot.com")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-opus-4.8")
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL", "gpt-5.5")

# 趣配音橙 + Microsoft 蓝
COLOR_ORANGE = "#FF6B35"
COLOR_BLUE = "#0078D4"
COLOR_BG = "#FFF7F2"

# ============================================================
# 二、Streamlit 全局样式
# ============================================================

st.set_page_config(
    page_title="趣配音 · 配音素材自动打标签",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
    .main {{ background-color: {COLOR_BG}; }}
    h1, h2, h3 {{ color: {COLOR_ORANGE}; }}
    .stButton > button {{
        background-color: {COLOR_ORANGE};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }}
    .stButton > button:hover {{
        background-color: {COLOR_BLUE};
        color: white;
    }}
    .qpy-tag {{
        display: inline-block;
        padding: 4px 12px;
        margin: 4px 4px 4px 0;
        background-color: {COLOR_ORANGE}22;
        color: {COLOR_ORANGE};
        border-radius: 14px;
        font-size: 14px;
        font-weight: 600;
    }}
    .qpy-tag-blue {{
        display: inline-block;
        padding: 4px 12px;
        margin: 4px 4px 4px 0;
        background-color: {COLOR_BLUE}22;
        color: {COLOR_BLUE};
        border-radius: 14px;
        font-size: 14px;
        font-weight: 600;
    }}
    .qpy-card {{
        background: white;
        border-left: 4px solid {COLOR_ORANGE};
        padding: 18px 22px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 12px;
    }}
    .qpy-score {{
        font-size: 38px;
        font-weight: 800;
        color: {COLOR_BLUE};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 三、SQLite 数据层
# ============================================================

def db_connect() -> sqlite3.Connection:
    """创建/打开 SQLite 连接, 自动建表。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            material_title  TEXT    NOT NULL,
            tags_json       TEXT    NOT NULL,
            model           TEXT    NOT NULL,
            latency_ms      INTEGER NOT NULL,
            created_at      TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def db_insert(title: str, tags: dict, model: str, latency_ms: int) -> None:
    conn = db_connect()
    try:
        conn.execute(
            "INSERT INTO results (material_title, tags_json, model, latency_ms, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                title,
                json.dumps(tags, ensure_ascii=False),
                model,
                int(latency_ms),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def db_recent(limit: int = 50) -> list[dict]:
    conn = db_connect()
    try:
        cur = conn.execute(
            "SELECT id, material_title, tags_json, model, latency_ms, created_at "
            "FROM results ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = []
        for r in cur.fetchall():
            rows.append({
                "id": r[0],
                "material_title": r[1],
                "tags": json.loads(r[2]),
                "model": r[3],
                "latency_ms": r[4],
                "created_at": r[5],
            })
        return rows
    finally:
        conn.close()


def db_count() -> int:
    conn = db_connect()
    try:
        cur = conn.execute("SELECT COUNT(*) FROM results")
        return cur.fetchone()[0]
    finally:
        conn.close()

# ============================================================
# 四、GitHub Copilot Token 读取
# ============================================================

def read_copilot_token() -> str | None:
    """从 ~/.config/gh/hosts.yml 读取 oauth_token。"""
    hosts_yml = Path.home() / ".config" / "gh" / "hosts.yml"
    if not hosts_yml.exists():
        return None
    try:
        # 不强依赖 pyyaml, 简单正则就够
        text = hosts_yml.read_text(encoding="utf-8")
        m = re.search(r"oauth_token:\s*([^\s]+)", text)
        if m:
            return m.group(1).strip()
    except Exception:
        return None
    return None

# ============================================================
# 五、Prompt 加载
# ============================================================

@st.cache_data
def load_prompt_template() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "(prompt 文件缺失)"


SYSTEM_PROMPT = """你是"趣配音"K-12 英语教研团队的资深内容标签师, 有 10 年以上一线英语教学 + 配音素材审核经验。
为新上架的英文配音素材打出标准化标签。

【硬性约束】
1. 只输出合法 JSON, 不要 markdown 代码块、不要解释性文字。
2. 所有字段必须齐全, 严禁返回 null。
3. 字段值落在给定枚举内。

【输出 schema】
{
  "grade": ["K"|"G1"..."G12"],  // 1-4 个年级
  "genre": "经典绘本"|"动画日常"|"动画电影"|"电影歌曲"|"演讲"|"科普纪录"|"儿歌律动"|"文学戏剧"|"自然纪录"|"童话故事",
  "difficulty": "★☆☆☆☆"|"★★☆☆☆"|"★★★☆☆"|"★★★★☆"|"★★★★★",
  "keywords": [string × 4-6],   // 英文
  "suitable_voices": 1|2|3|4,
  "duration_band": "短(<5min)"|"中(5-10min)"|"长(>10min)",
  "scene": "教材同步/启蒙"|"口语/情感表达"|"家庭场景/对话练习"|"演讲/初中拓展"|"故事讲述/朗读"|"对话练习/兴趣"|"学科英语/STEM"|"启蒙/磨耳朵"|"高中拓展/文学"|"学科英语/自然",
  "recommendation_score": 0-100
}
"""


def build_user_prompt(title: str, subtitle: str, duration_sec: int | None = None,
                      source_url: str = "") -> str:
    return (
        "请为以下配音素材打标签, 严格按 system 中 schema 输出 JSON:\n\n"
        f"【素材标题】{title}\n"
        f"【时长(秒)】{duration_sec if duration_sec else '未知'}\n"
        f"【来源】{source_url or '现场粘贴'}\n"
        f"【字幕摘要】\n{subtitle}\n"
    )

# ============================================================
# 六、LLM 调用 (在线 + 离线兜底)
# ============================================================

@st.cache_data
def load_ideal_tags() -> dict[str, dict]:
    """加载离线 ideal_tags.json, 按 id 索引。"""
    if not IDEAL_TAGS_PATH.exists():
        return {}
    data = json.loads(IDEAL_TAGS_PATH.read_text(encoding="utf-8"))
    return {item["id"]: {k: v for k, v in item.items() if k != "id"} for item in data}


@st.cache_data
def load_materials() -> list[dict]:
    if not MATERIALS_PATH.exists():
        return []
    return json.loads(MATERIALS_PATH.read_text(encoding="utf-8"))


def offline_lookup(title: str, subtitle: str) -> dict | None:
    """离线兜底: 按 title 或 subtitle 关键词匹配 materials → ideal_tags。"""
    materials = load_materials()
    ideal = load_ideal_tags()
    # 1) 标题完全匹配
    for m in materials:
        if m["title"].strip() == title.strip():
            return ideal.get(m["id"])
    # 2) 字幕子串匹配 (取前 30 字符)
    snippet = (subtitle or "")[:30].strip()
    if snippet:
        for m in materials:
            if snippet and snippet in m.get("subtitle_excerpt", ""):
                return ideal.get(m["id"])
    # 3) 标题模糊
    title_low = title.lower()
    for m in materials:
        if title_low and title_low in m["title"].lower():
            return ideal.get(m["id"])
    return None


def _heuristic_tags(title: str, subtitle: str, duration_sec: int | None) -> dict:
    """实在匹配不上时的兜底启发式 (避免现场尴尬)。"""
    text = (title + " " + (subtitle or "")).lower()
    word_count = len((subtitle or "").split())
    # genre
    if any(k in text for k in ["song", "sing", "hello"]):
        genre, scene, voices = "儿歌律动", "启蒙/磨耳朵", 1
    elif any(k in text for k in ["peppa", "pig", "andy", "toys"]):
        genre, scene, voices = "动画日常", "家庭场景/对话练习", 3
    elif any(k in text for k in ["ted", "vaccine", "science", "documentary", "penguin", "bbc"]):
        genre, scene, voices = "科普纪录", "学科英语/STEM", 1
    elif any(k in text for k in ["shakespeare", "romeo", "juliet"]):
        genre, scene, voices = "文学戏剧", "高中拓展/文学", 2
    elif any(k in text for k in ["stanford", "speech", "commencement"]):
        genre, scene, voices = "演讲", "演讲/初中拓展", 1
    else:
        genre, scene, voices = "经典绘本", "教材同步/启蒙", 1
    # difficulty by avg word len
    avg = sum(len(w) for w in (subtitle or "").split()) / max(word_count, 1)
    if avg < 4: diff = "★☆☆☆☆"
    elif avg < 5: diff = "★★☆☆☆"
    elif avg < 6: diff = "★★★☆☆"
    elif avg < 7: diff = "★★★★☆"
    else: diff = "★★★★★"
    # duration band
    if duration_sec is None:
        band = "短(<5min)"
    elif duration_sec < 300:
        band = "短(<5min)"
    elif duration_sec < 600:
        band = "中(5-10min)"
    else:
        band = "长(>10min)"
    # keywords: 取出现 ≥ 2 次的高频名词候选
    words = re.findall(r"[A-Za-z]{4,}", subtitle or "")
    stop = {"this", "that", "with", "from", "into", "they", "have", "were",
            "their", "your", "what", "when", "then", "than", "some", "very"}
    freq: dict[str, int] = {}
    for w in words:
        wl = w.lower()
        if wl in stop: continue
        freq[wl] = freq.get(wl, 0) + 1
    kws = [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:5]] or ["english", "story"]
    return {
        "grade": ["G2", "G3"],
        "genre": genre,
        "difficulty": diff,
        "keywords": kws,
        "suitable_voices": voices,
        "duration_band": band,
        "scene": scene,
        "recommendation_score": 75,
    }


def call_llm(title: str, subtitle: str, duration_sec: int | None = None,
             source_url: str = "") -> tuple[dict, str, int]:
    """
    调用 LLM 打标签。返回 (tags_dict, model_name, latency_ms)。
    OFFLINE=1 时走 ideal_tags.json 兜底, 全程不联网。
    """
    t0 = time.perf_counter()

    # ---------- 离线模式 ----------
    if OFFLINE:
        time.sleep(0.6)  # 模拟"AI 思考" 让现场体验更真实
        cached = offline_lookup(title, subtitle)
        if cached is not None:
            label = "offline-ideal-tags"
        else:
            cached = _heuristic_tags(title, subtitle, duration_sec)
            label = "offline-heuristic"
        latency = int((time.perf_counter() - t0) * 1000)
        return cached, label, latency

    # ---------- 在线模式 ----------
    token = read_copilot_token()
    if not token:
        # token 缺失 → 自动兜底, 不抛错让现场尴尬
        cached = offline_lookup(title, subtitle) or _heuristic_tags(title, subtitle, duration_sec)
        latency = int((time.perf_counter() - t0) * 1000)
        return cached, "fallback-no-token", latency

    user_prompt = build_user_prompt(title, subtitle, duration_sec, source_url)

    try:
        import litellm  # 延迟导入, 离线时无需安装
    except ImportError:
        cached = offline_lookup(title, subtitle) or _heuristic_tags(title, subtitle, duration_sec)
        latency = int((time.perf_counter() - t0) * 1000)
        return cached, "fallback-no-litellm", latency

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    last_err: Exception | None = None
    for model in (DEFAULT_MODEL, FALLBACK_MODEL):
        try:
            resp = litellm.completion(
                model=f"openai/{model}",
                messages=messages,
                api_base=LITELLM_BASE_URL,
                api_key=token,
                temperature=0.2,
                max_tokens=800,
                timeout=15,
                extra_headers={
                    "Editor-Version": "vscode/1.95.0",
                    "Copilot-Integration-Id": "vscode-chat",
                },
            )
            content = resp["choices"][0]["message"]["content"]
            tags = _parse_json_lenient(content)
            if tags:
                latency = int((time.perf_counter() - t0) * 1000)
                return tags, model, latency
        except Exception as e:
            last_err = e
            continue

    # 全部模型失败 → 兜底
    cached = offline_lookup(title, subtitle) or _heuristic_tags(title, subtitle, duration_sec)
    latency = int((time.perf_counter() - t0) * 1000)
    model_label = f"fallback-llm-error ({type(last_err).__name__})" if last_err else "fallback"
    return cached, model_label, latency


def _parse_json_lenient(text: str) -> dict | None:
    """容错解析: LLM 偶尔会包 ```json ... ``` 或带前缀。"""
    if not text:
        return None
    # 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 提取 ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 提取第一个 { ... }
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None

# ============================================================
# 七、UI 渲染助手
# ============================================================

def render_tag_card(title: str, tags: dict, model: str, latency_ms: int) -> None:
    """把一份标签 JSON 渲染成漂亮的卡片。"""
    score = tags.get("recommendation_score", 0)
    st.markdown(
        f"""
        <div class="qpy-card">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <h3 style="margin:0;">📚 {title}</h3>
              <div style="color:#888; font-size:12px; margin-top:6px;">
                模型: <b>{model}</b> · 耗时 <b>{latency_ms} ms</b>
              </div>
            </div>
            <div style="text-align:right;">
              <div style="color:#888; font-size:12px;">推荐分</div>
              <div class="qpy-score">{score}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📐 适合年级**")
        grade_html = " ".join(f'<span class="qpy-tag">{g}</span>' for g in tags.get("grade", []))
        st.markdown(grade_html or "—", unsafe_allow_html=True)

        st.markdown("**🎭 题材**")
        st.markdown(f'<span class="qpy-tag-blue">{tags.get("genre", "—")}</span>',
                    unsafe_allow_html=True)

    with col2:
        st.markdown("**⭐ 难度**")
        st.markdown(f"### {tags.get('difficulty', '—')}")

        st.markdown("**🎤 适合人数**")
        st.markdown(f'<span class="qpy-tag-blue">{tags.get("suitable_voices", "—")} 人配音</span>',
                    unsafe_allow_html=True)

    with col3:
        st.markdown("**⏱ 时长档位**")
        st.markdown(f'<span class="qpy-tag-blue">{tags.get("duration_band", "—")}</span>',
                    unsafe_allow_html=True)

        st.markdown("**🎯 适用场景**")
        st.markdown(f'<span class="qpy-tag-blue">{tags.get("scene", "—")}</span>',
                    unsafe_allow_html=True)

    st.markdown("**🔑 核心词**")
    kw_html = " ".join(f'<span class="qpy-tag">#{k}</span>' for k in tags.get("keywords", []))
    st.markdown(kw_html or "—", unsafe_allow_html=True)

    with st.expander("查看原始 JSON"):
        st.json(tags)

# ============================================================
# 八、侧边栏
# ============================================================

with st.sidebar:
    st.markdown(f"<h2 style='color:{COLOR_ORANGE};'>🎬 趣配音 Demo 1</h2>",
                unsafe_allow_html=True)
    st.caption("配音素材自动打标签")

    mode_label = "🛟 OFFLINE 兜底" if OFFLINE else "🌐 GitHub Copilot 在线"
    st.markdown(f"**运行模式**: {mode_label}")
    if not OFFLINE:
        st.markdown(f"- 网关: `{LITELLM_BASE_URL}`")
        st.markdown(f"- 主模型: `{DEFAULT_MODEL}`")
        st.markdown(f"- 兜底: `{FALLBACK_MODEL}`")

    st.markdown("---")
    st.markdown(f"**📊 历史标签**: {db_count()} 条")

    if st.button("🔍 查看历史记录", use_container_width=True):
        st.session_state["show_history"] = True

    if st.button("🗑 清空历史", use_container_width=True):
        DB_PATH.unlink(missing_ok=True)
        st.success("已清空")
        st.rerun()

    st.markdown("---")
    st.caption("💡 提示: 现场断网时, 设置环境变量")
    st.code("OFFLINE=1 ./start.sh", language="bash")

# ============================================================
# 九、主区域 Tabs
# ============================================================

st.markdown(
    f"<h1>🎬 配音素材自动打标签</h1>"
    f"<p style='color:#666;'>"
    f"AI 5 秒帮教研老师完成 30 分钟的素材入库标签工作 · "
    f"<b style='color:{COLOR_BLUE};'>趣配音 × GitHub Copilot</b>"
    f"</p>",
    unsafe_allow_html=True,
)

tab_single, tab_batch, tab_history, tab_prompt = st.tabs(
    ["📝 单条打标", "📦 批量打标", "📜 历史记录", "📐 .prompt.md 教研沉淀"]
)

# ---------- TAB 1: 单条 ----------
with tab_single:
    st.subheader("粘贴新素材的字幕摘要, 5 秒出标签")

    col_left, col_right = st.columns([1, 1])

    materials = load_materials()
    sample_titles = ["— 不使用样例 —"] + [m["title"] for m in materials]

    with col_left:
        sel = st.selectbox("快速选择样例 (现场演示用)", sample_titles, index=1)
        if sel != "— 不使用样例 —":
            sample = next(m for m in materials if m["title"] == sel)
            default_title = sample["title"]
            default_sub = sample["subtitle_excerpt"]
            default_dur = sample["duration_sec"]
            default_url = sample["source_url"]
        else:
            default_title = ""
            default_sub = ""
            default_dur = 0
            default_url = ""

        title_in = st.text_input("素材标题", value=default_title,
                                 placeholder="例: The Very Hungry Caterpillar")
        duration_in = st.number_input("时长 (秒)", min_value=0, max_value=3600,
                                      value=int(default_dur), step=10)
        url_in = st.text_input("来源 URL (可选)", value=default_url)
        subtitle_in = st.text_area("字幕摘要 *", value=default_sub, height=180,
                                   placeholder="粘贴英文字幕节选, 越完整越准...")

        go = st.button("🚀 AI 打标签", use_container_width=True, type="primary")

    with col_right:
        st.markdown("#### 🏷 标签结果")
        if go:
            if not title_in.strip() or not subtitle_in.strip():
                st.error("请至少填写「素材标题」和「字幕摘要」")
            else:
                with st.spinner("AI 正在分析素材..."):
                    tags, model, latency = call_llm(
                        title_in.strip(), subtitle_in.strip(),
                        duration_sec=int(duration_in) or None,
                        source_url=url_in.strip(),
                    )
                if tags:
                    db_insert(title_in.strip(), tags, model, latency)
                    render_tag_card(title_in.strip(), tags, model, latency)
                    st.success(f"✅ 完成! 用时 {latency} ms (≈ {latency/1000:.2f}s)")
                else:
                    st.error("LLM 返回为空, 请重试或切换 OFFLINE 模式")
        else:
            st.info("👈 在左侧粘贴字幕摘要, 点击「AI 打标签」")

# ---------- TAB 2: 批量 ----------
with tab_batch:
    st.subheader("上传 materials.json, 一次性给整批素材打标")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        use_mock = st.checkbox("直接用 mock-data/materials.json", value=True)
        uploaded = None
        if not use_mock:
            uploaded = st.file_uploader("上传 materials.json", type=["json"])

    with col_b:
        st.markdown("**📋 待处理素材预览**")
        if use_mock:
            mats = load_materials()
        elif uploaded is not None:
            try:
                mats = json.loads(uploaded.read().decode("utf-8"))
            except Exception as e:
                st.error(f"JSON 解析失败: {e}")
                mats = []
        else:
            mats = []

        if mats:
            preview_df = pd.DataFrame([
                {"id": m.get("id", "-"),
                 "title": m.get("title", "-")[:50],
                 "duration_sec": m.get("duration_sec", "-")}
                for m in mats
            ])
            st.dataframe(preview_df, use_container_width=True, height=200)

    if mats and st.button(f"🚀 批量打标 ({len(mats)} 条)",
                          use_container_width=True, type="primary"):
        progress = st.progress(0.0, text="开始处理...")
        results_rows: list[dict] = []
        for i, m in enumerate(mats, start=1):
            title = m.get("title", f"item_{i}")
            progress.progress(i / len(mats),
                              text=f"({i}/{len(mats)}) 正在分析: {title[:40]}...")
            tags, model, latency = call_llm(
                title=title,
                subtitle=m.get("subtitle_excerpt", ""),
                duration_sec=m.get("duration_sec"),
                source_url=m.get("source_url", ""),
            )
            db_insert(title, tags, model, latency)
            results_rows.append({
                "id": m.get("id", "-"),
                "title": title,
                "grade": ",".join(tags.get("grade", [])),
                "genre": tags.get("genre", ""),
                "difficulty": tags.get("difficulty", ""),
                "voices": tags.get("suitable_voices", ""),
                "scene": tags.get("scene", ""),
                "score": tags.get("recommendation_score", 0),
                "keywords": ",".join(tags.get("keywords", [])),
                "model": model,
                "ms": latency,
            })
        progress.progress(1.0, text="✅ 全部完成!")
        df = pd.DataFrame(results_rows)
        st.success(f"🎉 共处理 {len(df)} 条, 平均耗时 {int(df['ms'].mean())} ms/条")
        st.dataframe(df, use_container_width=True, height=420)

        # 下载
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ 下载结果 CSV", data=csv,
                           file_name=f"tags_{int(time.time())}.csv",
                           mime="text/csv")

# ---------- TAB 3: 历史 ----------
with tab_history:
    st.subheader("📜 SQLite 历史记录 (最近 50 条)")
    rows = db_recent(50)
    if not rows:
        st.info("还没有历史记录。先去「单条打标」或「批量打标」跑一下吧。")
    else:
        hist_df = pd.DataFrame([
            {
                "id": r["id"],
                "title": r["material_title"],
                "genre": r["tags"].get("genre", ""),
                "grade": ",".join(r["tags"].get("grade", [])),
                "difficulty": r["tags"].get("difficulty", ""),
                "score": r["tags"].get("recommendation_score", 0),
                "model": r["model"],
                "latency_ms": r["latency_ms"],
                "created_at": r["created_at"],
            } for r in rows
        ])
        st.dataframe(hist_df, use_container_width=True, height=380)

        st.markdown("**🔍 详情查看**")
        pick = st.selectbox("选一条看完整 JSON",
                            options=[f"#{r['id']} · {r['material_title']}" for r in rows])
        if pick:
            pid = int(pick.split("·")[0].strip().lstrip("#"))
            picked = next(r for r in rows if r["id"] == pid)
            render_tag_card(picked["material_title"], picked["tags"],
                            picked["model"], picked["latency_ms"])

# ---------- TAB 4: .prompt.md ----------
with tab_prompt:
    st.subheader("📐 教研经验如何沉淀? → 一个 .prompt.md 文件")
    st.markdown(
        f"""
        <div style='background:{COLOR_BLUE}10; border-left:4px solid {COLOR_BLUE};
                    padding:14px 18px; border-radius:8px; margin-bottom:14px;'>
        <b>客户经常问:</b> "我们 8 位资深教研老师的标签判定经验, 怎么不被 AI 稀释、
        还能持续迭代?"<br>
        <b>答案:</b> 把规则写进 git 管控的 <code>.prompt.md</code>,
        Copilot 调用时一致复用 — 老师走了, 知识不走。
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"📄 文件路径: `{PROMPT_PATH.relative_to(APP_DIR)}`")
    st.markdown("---")
    st.markdown(load_prompt_template())

# ============================================================
# 十、首次启动 → 历史弹窗 (从侧边栏触发)
# ============================================================
if st.session_state.get("show_history"):
    st.session_state["show_history"] = False
    st.toast("切到「📜 历史记录」tab 即可查看", icon="📊")
