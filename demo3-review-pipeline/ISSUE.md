# [需求] 学生录音方言混入与低俗词识别

**Issue ID**: QPY-MOD-001
**优先级**: P1
**提出方**: 内容审核运营组 (审核日均工单 ~12k 条)
**关联模块**: 内容审核服务 (Moderation Service)

---

## 用户故事

> **作为** 内容审核运营，
> **我希望** 在学生上传配音后，系统能自动给出风险等级，
> **以便** 把人力集中在 WARN 档复核，BLOCK 档直接拦截，PASS 档零打扰，
> **从而** 把当前人均 280 条/日的处理量翻倍到 600 条/日。

---

## 需求细节

学生上传一段英语配音后（ASR 转写已存在），审核服务需要：

1. **自动检测录音中的方言混入比例** —— 至少识别粤语 / 四川话 / 东北话三种常见方言；
2. **自动识别低俗词** —— 内置一个 **200 词** 的初始词库（可热更新）；
3. **输出风险等级**：`PASS` / `WARN` / `BLOCK` 三档；
4. **给出可读理由**：reasons 字段是面向运营的中文短句数组，不暴露原始词库词条。

---

## 验收标准 (Acceptance Criteria)

### AC-1：API 契约

- **REST API**: `POST /api/moderate`
- **Request body**:
  ```json
  {
    "transcript": "Hello, my name is Alice ...",
    "audio_meta": {
      "duration_sec": 8.5,
      "sample_rate": 16000
    }
  }
  ```
- **Response 200**:
  ```json
  {
    "decision": "allow | review | reject",
    "risk_level": "PASS | WARN | BLOCK",
    "reasons": ["未命中低俗词，未检测到方言混入"],
    "evidence": {
      "profanity_hits": 0,
      "dialect_ratio": 0.0,
      "top_dialect": null,
      "audio_meta_passthrough": { "...": "..." }
    }
  }
  ```
- **Response 400**：`transcript` 为空 / 非字符串 / >4000 字符 → `{"error":"..."}`

### AC-2：三档决策规则（初版）

| 触发条件 | risk_level | decision |
|---|---|---|
| 无低俗词命中 + 方言比例 < 5% | PASS | allow |
| 低俗词命中 1-2 次 **或** 方言比例 5%-15% | WARN | review |
| 低俗词命中 ≥3 次 **或** 方言比例 ≥15% | BLOCK | reject |

### AC-3：安全 / 合规

- 响应体 **不得** 回显原始词库词条（只能给计数 + 分类）；
- 响应体 **不得** 出现 stack trace；
- 词库文件视为敏感配置，**不进**业务日志。

### AC-4：性能

- 单次审核 P95 延迟 ≤ 50ms（4000 字符 transcript，无 IO）。

### AC-5：测试

- 至少覆盖 PASS / WARN / BLOCK 三档各 1 条等价类用例；
- 至少覆盖输入校验 3 条边界用例（空 / 超长 / 非字符串）。

---

## 不在本期范围

- 词库的可视化运营后台（下个迭代）
- 多语种支持（仅中英文场景）
- 声学方言检测（本期仅基于 ASR 转写做关键词命中，后续接声学模型）

---

## FDE 备注（给客户演示用）

这个 issue 是 Demo 3 的"输入材料"，演示流程见 [SOP.md](./SOP.md)：
1. 把本 issue 整段贴进 Copilot Chat → `/design-feature` → `@architect` 出技术设计
2. Agent 模式生成 `src/moderation.js` + 单测
3. `@test-engineer` 补全等价类
4. **并行**调 `@code-reviewer` + `@red-team` + `@security-reviewer`
5. `@release-engineer` 出 CHANGELOG + release notes
