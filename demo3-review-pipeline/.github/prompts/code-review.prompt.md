---
variables:
  - name: files_to_review
    description: Comma-separated list of files to review
  - name: pr_description
    description: Pull request description and context
---

# 🔍 Code Review Checklist

## Context
**Files:** {{files_to_review}}
**PR Description:** {{pr_description}}

## Review Pipeline

### Phase 1: Code Quality — @code-reviewer
Invoke @code-reviewer on {{files_to_review}} to evaluate:
- Code correctness and logic errors
- Naming conventions and readability
- DRY violations and dead code
- Error handling completeness
- Test coverage adequacy

### Phase 2: Security — @security-reviewer
Invoke @security-reviewer on {{files_to_review}} to check:
- Input validation and sanitization
- Authentication/authorization gaps
- Injection vulnerabilities (SQL, NoSQL, command)
- Sensitive data exposure
- Dependency vulnerabilities

### Phase 3: Adversarial — @red-team
Invoke @red-team to attempt:
- Edge case exploitation
- Race conditions and concurrency issues
- Resource exhaustion vectors
- API abuse scenarios

## Unified Review Report

Collect all findings and produce a single report:

### Findings Table

| # | Severity | Category | File | Line | Finding | Recommendation |
|---|----------|----------|------|------|---------|----------------|
| 1 | 🔴 Critical | | | | | |
| 2 | 🟠 High | | | | | |
| 3 | 🟡 Medium | | | | | |
| 4 | 🔵 Low | | | | | |

Sort by severity: Critical → High → Medium → Low.

### Summary
- **Total findings:** _count_
- **Blockers:** _count of Critical/High_
- **Recommendation:** Approve / Request Changes / Needs Discussion

---

### 📌 适用于趣配音内容审核 — 调用示例

```text
/code-review
files_to_review: src/moderation.js, src/server.js
pr_description: |
  实现 POST /api/moderate, 三档决策 PASS/WARN/BLOCK.
  方言检测使用 mock 关键词命中,
  低俗词词库 200 条, 内置在 src/lexicon.js.
```

在三个独立的 Copilot Chat 窗口中**并行**调用：
- `@code-reviewer src/moderation.js` — 关注 DRY、错误处理、可读性
- `@security-reviewer src/moderation.js` — 关注词库泄漏、ReDoS、输入校验
- `@red-team src/moderation.js` — 用方言 Unicode 同形字、超长 transcript 攻击

预期 30 秒内拿到 3 份评审报告，由人工合并为统一 Findings Table。
