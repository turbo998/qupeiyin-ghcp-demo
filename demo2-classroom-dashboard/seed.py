"""
seed.py  -  趣配音 班级作业看板 mock 数据生成器
固定 seed=42，保证可复现。FDE 现场跑一次即可。

生成内容：
  - 10 个班级 (G3-1 ~ G6-1)
  - ~50 学生/班 (共 500 人)
  - 10 个素材 (从 ../mock-data/materials.json 加载)
  - 30 个作业 (每个素材作业布置 3 次)
  - ~8000 条提交记录 (近 30 天，含完成/未完成/已打分 3 种状态)

输出: data/classroom.db (SQLite)
"""
import json
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "data" / "classroom.db"
MATERIALS_JSON = BASE.parent / "mock-data" / "materials.json"

# ------------------ 基础配置 ------------------
CLASS_DEFS = [
    ("G3-1", 3), ("G3-2", 3), ("G3-3", 3),
    ("G4-1", 4), ("G4-2", 4), ("G4-3", 4),
    ("G5-1", 5), ("G5-2", 5), ("G5-3", 5),
    ("G6-1", 6),
]
STUDENTS_PER_CLASS = 50      # 共 500
ASSIGNMENT_TIMES_PER_MAT = 3 # 30 个作业
# 每个作业平均分发到的班级数（控制提交总量约 8000+）
CLASSES_PER_ASSIGNMENT_MIN = 5
CLASSES_PER_ASSIGNMENT_MAX = 8
DAYS_SPAN = 30

# 中文姓氏 / 名字（公开常见用字，纯生成用）
SURNAMES = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
            "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗"]
GIVEN_NAMES_1 = ["子", "梓", "宇", "欣", "嘉", "思", "雨", "佳", "俊", "睿",
                 "诗", "天", "若", "馨", "可", "心", "悦", "皓", "晨", "怡"]
GIVEN_NAMES_2 = ["轩", "涵", "豪", "怡", "琪", "瑶", "妍", "翔", "杰", "萱",
                 "霖", "辰", "彤", "宁", "然", "婷", "颖", "希", "乐", "宸"]


def gen_student_name() -> str:
    return random.choice(SURNAMES) + random.choice(GIVEN_NAMES_1) + random.choice(GIVEN_NAMES_2)


# ------------------ 建表 ------------------
SCHEMA = """
DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS assignment_classes;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS classes;
DROP TABLE IF EXISTS materials;

CREATE TABLE classes (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    grade     INTEGER NOT NULL
);

CREATE TABLE students (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    class_id  INTEGER NOT NULL,
    -- 扩展点: 家长是否绑定打卡（为'家长打卡参与度'指标预留）
    parent_bound INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

CREATE TABLE materials (
    id            TEXT PRIMARY KEY,         -- m001 ... m010
    title         TEXT NOT NULL,
    duration_sec  INTEGER NOT NULL,
    source_url    TEXT
);

CREATE TABLE assignments (
    id           INTEGER PRIMARY KEY,
    material_id  TEXT NOT NULL,
    title        TEXT NOT NULL,
    assigned_at  TEXT NOT NULL,             -- ISO datetime
    due_at       TEXT NOT NULL,
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE TABLE assignment_classes (
    assignment_id INTEGER NOT NULL,
    class_id      INTEGER NOT NULL,
    PRIMARY KEY (assignment_id, class_id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

CREATE TABLE submissions (
    id              INTEGER PRIMARY KEY,
    student_id      INTEGER NOT NULL,
    assignment_id   INTEGER NOT NULL,
    status          TEXT NOT NULL,          -- 'pending' | 'completed' | 'graded'
    score           INTEGER,                -- 0-100，仅 graded 有值
    submitted_at    TEXT,                   -- ISO datetime，pending 为 NULL
    -- 扩展点: 家长是否在该次作业打卡（为'家长打卡参与度'指标预留）
    parent_checkin  INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id)
);

CREATE INDEX idx_subm_assignment ON submissions(assignment_id);
CREATE INDEX idx_subm_student    ON submissions(student_id);
CREATE INDEX idx_subm_status     ON submissions(status);
CREATE INDEX idx_subm_submitted  ON submissions(submitted_at);
CREATE INDEX idx_ac_class        ON assignment_classes(class_id);
"""


def load_materials():
    with open(MATERIALS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print(f"[seed] DB → {DB_PATH}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    # ---- classes ----
    classes = []
    for idx, (name, grade) in enumerate(CLASS_DEFS, start=1):
        classes.append((idx, name, grade))
    conn.executemany("INSERT INTO classes(id,name,grade) VALUES (?,?,?)", classes)

    # ---- students ----
    students = []
    student_id = 1
    for cls_id, _, _ in classes:
        for _ in range(STUDENTS_PER_CLASS):
            name = gen_student_name()
            parent_bound = 1 if random.random() < 0.62 else 0  # ~62% 已绑定家长
            students.append((student_id, name, cls_id, parent_bound))
            student_id += 1
    conn.executemany(
        "INSERT INTO students(id,name,class_id,parent_bound) VALUES (?,?,?,?)",
        students,
    )
    total_students = len(students)

    # ---- materials ----
    mats = load_materials()
    conn.executemany(
        "INSERT INTO materials(id,title,duration_sec,source_url) VALUES (?,?,?,?)",
        [(m["id"], m["title"], m["duration_sec"], m.get("source_url", "")) for m in mats],
    )

    # ---- assignments (30 = 10 素材 × 3) ----
    now = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    assignments = []
    assignment_classes = []
    aid = 1
    for m in mats:
        for occ in range(ASSIGNMENT_TIMES_PER_MAT):
            # 在过去 DAYS_SPAN 天内随机分布
            days_ago = random.randint(0, DAYS_SPAN - 1)
            assigned_at = now - timedelta(days=days_ago, hours=random.randint(0, 5))
            due_at = assigned_at + timedelta(days=random.randint(3, 7))
            title = f"{m['title'].split(' - ')[0]} #第{occ + 1}次"
            assignments.append(
                (aid, m["id"], title, assigned_at.isoformat(timespec="seconds"),
                 due_at.isoformat(timespec="seconds"))
            )
            # 选 5-8 个班布置该作业
            k = random.randint(CLASSES_PER_ASSIGNMENT_MIN, CLASSES_PER_ASSIGNMENT_MAX)
            chosen = random.sample([c[0] for c in classes], k)
            for cls_id in chosen:
                assignment_classes.append((aid, cls_id))
            aid += 1
    conn.executemany(
        "INSERT INTO assignments(id,material_id,title,assigned_at,due_at) VALUES (?,?,?,?,?)",
        assignments,
    )
    conn.executemany(
        "INSERT INTO assignment_classes(assignment_id,class_id) VALUES (?,?)",
        assignment_classes,
    )

    # ---- submissions ----
    # 对每个 (作业, 该作业所属班级中的每个学生) 生成一条 submission
    # 状态分布：completed/graded 综合 ~ 60%，pending ~40%（用于"待补做名单"）
    # 在 completed 中 ~85% 已打分（graded）

    # 预取 class → student_ids
    class_students = {cid: [] for cid, _, _ in classes}
    for sid, _, cid, _ in students:
        class_students[cid].append(sid)

    # 预取每个学生的 parent_bound（用于家长打卡指标）
    parent_bound_map = {sid: pb for sid, _, _, pb in students}

    # 预取每个 assignment 的 assigned_at
    assigned_at_map = {a[0]: datetime.fromisoformat(a[3]) for a in assignments}

    submissions = []
    subm_id = 1
    for aid_, cls_id in assignment_classes:
        a_dt = assigned_at_map[aid_]
        for sid in class_students[cls_id]:
            r = random.random()
            if r < 0.40:
                # pending - 未提交
                status = "pending"
                score = None
                submitted_at = None
                checkin = 0
            elif r < 0.49:
                # completed 未打分
                status = "completed"
                score = None
                hours = random.randint(2, 96)
                submitted_at = (a_dt + timedelta(hours=hours)).isoformat(timespec="seconds")
                checkin = 1 if (parent_bound_map[sid] and random.random() < 0.55) else 0
            else:
                # graded 已打分
                status = "graded"
                # 分数倾向 70-95，长尾低分
                base = random.gauss(82, 8)
                score = max(45, min(100, int(base)))
                hours = random.randint(2, 96)
                submitted_at = (a_dt + timedelta(hours=hours)).isoformat(timespec="seconds")
                checkin = 1 if (parent_bound_map[sid] and random.random() < 0.60) else 0
            submissions.append((subm_id, sid, aid_, status, score, submitted_at, checkin))
            subm_id += 1

    conn.executemany(
        "INSERT INTO submissions(id,student_id,assignment_id,status,score,submitted_at,parent_checkin) "
        "VALUES (?,?,?,?,?,?,?)",
        submissions,
    )

    conn.commit()

    # ---- 统计输出 ----
    cur = conn.cursor()
    counts = {
        "classes":    cur.execute("SELECT COUNT(*) FROM classes").fetchone()[0],
        "students":   cur.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "materials":  cur.execute("SELECT COUNT(*) FROM materials").fetchone()[0],
        "assignments":cur.execute("SELECT COUNT(*) FROM assignments").fetchone()[0],
        "assignment_classes": cur.execute("SELECT COUNT(*) FROM assignment_classes").fetchone()[0],
        "submissions":cur.execute("SELECT COUNT(*) FROM submissions").fetchone()[0],
        "pending":    cur.execute("SELECT COUNT(*) FROM submissions WHERE status='pending'").fetchone()[0],
        "completed":  cur.execute("SELECT COUNT(*) FROM submissions WHERE status='completed'").fetchone()[0],
        "graded":     cur.execute("SELECT COUNT(*) FROM submissions WHERE status='graded'").fetchone()[0],
        "parent_checkin": cur.execute("SELECT COUNT(*) FROM submissions WHERE parent_checkin=1").fetchone()[0],
    }
    conn.close()

    print(f"[seed] ✅ done. seed={SEED}")
    for k, v in counts.items():
        print(f"  {k:>20}: {v}")

    if counts["submissions"] < 5000:
        print("[seed] ❌ submissions < 5000，请检查配置", file=sys.stderr)
        sys.exit(1)
    print(f"[seed] ✅ 总学生 {total_students}，提交 {counts['submissions']} 条 (达标 ≥ 5000)")


if __name__ == "__main__":
    main()
