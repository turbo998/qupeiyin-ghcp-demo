---
variables:
  - name: feature_name
    description: Name of the feature to design
  - name: user_story
    description: User story describing the feature need
---

# 🎨 Feature Design: {{feature_name}}

## User Story
{{user_story}}

## Design Process

### Step 1: Product Review — @product-reviewer
Invoke @product-reviewer to evaluate the user story:
- Is the user story clear and complete?
- Are acceptance criteria well-defined?
- Are there edge cases or ambiguities to resolve?
- Does this align with existing product patterns?

### Step 2: Technical Design — @architect
Invoke @architect to design the technical approach:
- Which files/modules need changes?
- What new components are required?
- API contract (endpoints, request/response shapes)
- Data model changes
- Dependencies and integration points

### Step 3: Implementation Plan
Break down into ordered tasks:

| # | Task | File(s) | Estimated Effort | Dependencies |
|---|------|---------|-----------------|--------------|
| 1 | | | | |

### Step 4: Complexity & Risk Assessment

**Complexity:** Low / Medium / High
**Risks:**
- Risk 1: _description_ — Mitigation: _approach_

---

### 📌 适用于趣配音内容审核 — 调用示例

```text
/design-feature
feature_name: 学生录音方言混入与低俗词识别
user_story: |
  作为内容审核运营,
  我希望在学生上传配音后:
  - 自动检测录音中的方言混入比例 (粤语/四川话/东北话等)
  - 自动识别低俗词 (维护一个 200 词的初始词库)
  - 输出风险等级: PASS / WARN / BLOCK 并给出可读理由
  验收: REST API POST /api/moderate, 输入 transcript + audio_meta, 返回 JSON 决策
```

预期：`@architect` 会先出 ASCII 数据流图，再给 `POST /api/moderate` 的 API 表格、边界用例（空 transcript / 超长 / 全方言 / 全低俗词）和测试矩阵。

## Output: Design Document

```markdown
# Design: {{feature_name}}

## Overview
_Summary of the feature and its purpose_

## User Story
{{user_story}}

## Technical Approach
_Architecture decisions and rationale_

## Implementation Plan
_Ordered task list with estimates_

## Risks & Mitigations
_Identified risks and how to address them_

## Open Questions
_Anything needing further discussion_
```
