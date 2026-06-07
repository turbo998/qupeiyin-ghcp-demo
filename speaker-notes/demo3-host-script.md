# 🎤 Demo 3 主持词 · 审核服务多 Agent 流水线(8 分钟)

> **用途**:FDE 现场逐段照读;30 秒一段细化
> **核心承诺**:一个 Issue → 一个 Release · 5 个 Copilot Agent 接力 · 8 分钟跑完设计/编码/测试/三视角评审/发布全链路
> **哇点标记**:✨ 表示当场要把 IT 客户情绪推高的瞬间
> **场景代入**:全程以"研发负责人 / 架构师 / 安全工程"视角说话;不说"模型/参数",多说"PR / CI / 审计痕迹 / sign-off / Boundaries"
> **本 demo 最大哇点**:`4:00-5:00` 那 1 分钟——三个 Chat 窗口同步回车,30 秒拿到 code-reviewer + red-team + security-reviewer 三份视角完全不同的报告

---

## 🎯 进入 demo 前 15 秒缓冲(从 PPT 第 14 页切到 VS Code 时)

[画面] PPT 第 14 页 → Cmd+Tab 切到 VS Code 全屏
[话术] "切 demo 3。这个节奏更快,8 分钟,5 个 Agent,5 个步骤。请研发负责人和架构师特别注意第 4 步——三个 Chat 窗口同时工作那一段。"
[错挥腿提示] 切屏前确认 3 件事:① VS Code 已经 `Open Folder` 到 `demo3-review-pipeline/` ② 终端里跑过一次 `npm test` 显示 `# pass 9` 可见 ③ 已经打开 3 个文件页签(`ISSUE.md` / `src/moderation.js` / `tests/moderation.test.js`)和 1 个 Copilot Chat 窗口(Step 4 再开 2 个)。

---

## ⏱ 0:00-0:30 · Step 1 启动 · 展示 ISSUE,召唤 @architect

[画面] VS Code 全屏。左侧文件页签切到 `ISSUE.md`,镜头从顶部慢速滚到"验收标准",高亮"方言混入""低俗词""PASS / WARN / BLOCK"。右侧 Copilot Chat 已经粘好 `/design-feature` prompt(整段 ISSUE 作为上下文)。
[话术] "Step 1。这是一个真实工单:学生录音方言混入和低俗词识别,要求出 REST API,三档风险等级。**现在我召唤 @architect 来做技术设计**。注意我用的不是直接'写代码',我用的是 `/design-feature`——一个 slash command,内置了我们公司的设计流程。回车。"
[错挥腿提示] 强调 "**召唤 @architect**" 这个动作。每个 Agent 出场都要有明确的"召唤"声明,这是整个 demo 3 的叙事结构。

---

## ⏱ 0:30-1:00 · @architect 开始输出技术设计

[画面] Copilot Chat 输出:先 `@product-reviewer` 5 秒快速复核 user story → 然后 `@architect` 开始流式输出:① `## Architecture Overview` ② ASCII 数据流图(transcript → validateInput → detectProfanity / detectDialectMix → decide → response)③ API 表格(Method/Path/Request/Response/Errors)④ 边界用例清单。
[话术] "看,它先调了 @product-reviewer 快速复核需求合不合理,然后切给 @architect 出设计。ASCII 数据流图、API 表、边界用例——这些就是你们工程师入职第一周交付的标准产物。10 个 Agent 把这套标准固化下来了。"
[错挥腿提示] 当 ASCII 图出来时,鼠标在图上轻轻划过,让客户看清"5 个函数模块清晰分层"——这是后面 Step 2 写代码的依据。

---

## ⏱ 1:00-1:30 · Step 1 完成,口播价值

[画面] Chat 区出现完整 API 表(POST /api/moderate, 输入 transcript+audio_meta, 输出 decision+risk_level+reasons+evidence, 400/422/500 错误码),底下是边界用例清单(空 / 超长 4000+ / 全方言 / 全低俗词 / Unicode 同形字)。
[话术] "30 秒里它给出了 API 契约、错误码、边界用例。这一步价值在哪?在传统流程里,这是架构师写一份 confluence 文档,业务方评审 2 天的产物。现在 30 秒,而且产物质量是有 Boundaries 段约束的——@architect 不会越界写代码。"
[错挥腿提示] **"Boundaries"** 是 IT 听众的关键词。强调每个 Agent 都有边界,不会越权。

---

## ⏱ 1:30-2:00 · Step 2 启动 · 切 Agent 模式,召唤实现

[画面] 在同一个 Chat 窗口里(带着 Step 1 的上下文),点齿轮图标切到 **Agent 模式**(图标变色)。输入框粘 prompt:"按上面 @architect 的设计实现 src/moderation.js,要求函数式分层 validateInput/detectProfanity/detectDialectMix/decide/moderate,阈值常量化,JSDoc 全覆盖,响应不回显原始词库,同步更新 tests/moderation.test.js 至少覆盖 PASS/WARN/BLOCK 三档"。回车。
[话术] "Step 2。**现在我切到 Agent 模式,让 Copilot 按 @architect 的设计实现代码**。注意 Agent 模式跟 Chat 不一样——它能跨多个文件编辑,能自己开终端跑命令,能根据测试结果回头修代码。"
[错挥腿提示] **"切到 Agent 模式"** 是个关键交互。鼠标点齿轮的动作要给客户看清,否则他们以为还是普通 Chat。

---

## ⏱ 2:00-2:30 · ✨ 哇点 1:Copilot 自己改 3 个文件

[画面] 左侧文件树跳动:`src/moderation.js`、`src/lexicon.js`、`tests/moderation.test.js` 三个文件依次出现"●"未保存标记。Chat 区滚动展示 diff:moderation.js 5 个函数 + JSDoc 全部生成、lexicon.js 注入 200 词词库 mock、test 文件加了 PASS/WARN/BLOCK 各 1 条用例。
[话术] "✨ 看左边的文件树——Copilot 自己在改 3 个文件:业务代码、词库、单元测试。这就是 Agent 模式跟普通补全的本质区别:它能跨文件编辑。注意它没有去装新的 npm 包——为什么?因为我们在仓库的 `.github/copilot-instructions.md` 里写了'不要在未经确认的情况下安装新依赖'。**规则倒灌**。"
[错挥腿提示] **"规则倒灌"** 是 IT 金句。强调 Copilot 不是失控的,它被 `.github/` 下的规则文件约束。

---

## ⏱ 2:30-3:00 · Copilot 自己跑 npm test

[画面] Copilot Agent 完成代码后,自己调出底部 terminal,输入 `npm test` 回车。终端输出 `# tests 9` `# pass 9`,9 条用例全绿。
[话术] "看终端,它自己跑 npm test。9 条用例全绿。整个过程我没有点任何按钮,它读测试结果、看到通过、自己结束。如果有红,它会回去修代码再跑一次。这才是真正的'Agentic'。"
[错挥腿提示] "Agentic" 是行业热词,IT 客户喜欢听。如果 npm test 真的有红(很少见),立刻口播"今天我们时间紧,这条用例我们 Step 3 让 @test-engineer 来处理"——绝不在客户面前 debug。

---

## ⏱ 3:00-3:30 · Step 3 启动 · 召唤 @test-engineer 补强测试

[画面] 在 Chat 输入框粘:"@test-engineer 请基于 src/moderation.js 当前实现,补全 tests/moderation.test.js:对 detectProfanity/detectDialectMix/decide 三个函数分别加单元测试;对 PASS/WARN/BLOCK 三档分别覆盖等价类(每档至少 3 条);加边界用例(4000 字符恰好上限、4001 超限、含 emoji 全角空格);加安全测试(响应里绝对不出现原始词库词条)"。回车。
[话术] "Step 3。**现在我召唤 @test-engineer**。它是 10 个 Agent 里专门做测试的。我让它做三件事:补三个函数的单测、PASS/WARN/BLOCK 三档等价类、边界和安全用例。"
[错挥腿提示] 召唤声明明确化。强调"专门做测试的角色",突出 Agent 不是同质的。

---

## ⏱ 3:30-4:00 · @test-engineer 输出 + 跑测试

[画面] Chat 区先输出一个 Markdown 表格 **Test Plan**(列:用例 / 输入 / 期望),约 15 条用例。然后输出 `tests/moderation.test.js` 的补丁代码块。FDE 手动复制粘贴到测试文件,再跑 `npm test`。终端输出从 `# pass 9` 涨到 `# pass 18` 或更高。
[话术] "@test-engineer 给的不是直接代码,它先列了一个 Test Plan 表格——这就是它的角色边界,它要把测试策略可解释化。然后给代码。我跑一下,看 # pass 从 9 涨到 18。等价类、边界、安全三类用例,这是企业级测试的最低标准,一个 prompt 让它按这个标准来。"
[错挥腿提示] "Test Plan 表格"是亮点,展示 Agent 输出有结构化产物,不是一坨代码。

---

## ⏱ 4:00-4:30 · Step 4 准备 · 打开第 2 和第 3 个 Chat 窗口

[画面] Ctrl/Cmd+Shift+I 按两次,屏幕上出现 3 个 Copilot Chat 窗口并排(左 / 中 / 右)。把 3 段 prompt 提前复制好,准备分别贴。
[话术] "Step 4。这是今天 IT 部分的高光。**我现在要同时召唤 @code-reviewer、@red-team、@security-reviewer 三个 Agent**,让它们从代码质量、攻击视角、安全合规三个完全不同的视角同时评审。"
[错挥腿提示] **三个 Chat 窗口必须提前排好版**,不能现场调整。屏幕分辨率建议 1920x1080,每个窗口宽 640。

---

## ⏱ 4:30-5:00 · ✨ 哇点 2(全场 IT 最大哇点):同步回车 + 30 秒三份报告

[画面] FDE 把 3 段 prompt 分别贴到 3 个窗口,然后用极短间隔(<1 秒)按 Enter 三次。三个窗口几乎同时开始流式输出:
- **左 @code-reviewer**:`Findings Table` 列出命名建议、DRY 违反、JSDoc 缺失
- **中 @red-team**:`PoC Table` 列出同形字攻击(巴适→巴適)、零宽空格 bypass、超长 transcript ReDoS、JSON 嵌套滥用
- **右 @security-reviewer**:`Severity Table` 按 Critical / High / Medium / Low 排序的安全发现

[话术] "✨ 同步回车!三个窗口同时跑——这是多 Agent 流水线的核心价值。原来 code review 是工程师 A review 一两天,然后工程师 B review security——串行,等三天。现在 30 秒内拿到三份**视角完全不同**的报告,而且是三个**专业角色**的报告,不是三个同质 LLM 的输出。"
[错挥腿提示] **这是整个 60 分钟 IT 高光**。说完后停 5 秒不动,让客户的眼睛在三个窗口间扫描。IT 负责人会自己开始读 Findings Table——给他读的时间。

---

## ⏱ 5:00-5:30 · 解读 @red-team 输出,讲"攻击向量固化"

[画面] 镜头特写中间的 @red-team 窗口。PoC Table 列出:① 同形字(巴适 vs 巴適 U+9069)② 零宽空格 ZWJ U+200D 插入 ③ 超长 transcript 4000 字符 ReDoS ④ JSON 超深嵌套 ⑤ 大小写全角变体。
[话术] "看 red-team 给的攻击向量——同形字、零宽空格、ReDoS、JSON 滥用。这些不是模型瞎想的,这是真实安全工程师的攻击 checklist。我们把这个 checklist 写进了 `.github/agents/red-team.md`,**固化成 Agent 定义**。下次任何项目用这个 Agent,自动获得同一份 checklist。"
[错挥腿提示] **"固化进 Agent 定义"** 是金句。安全工程师听到这句会立刻明白价值。

---

## ⏱ 5:30-6:00 · 解读 @security-reviewer + @code-reviewer 收束

[画面] 镜头扫到右边 @security-reviewer,展示 Severity Critical 一条(词库泄漏风险)、High 两条(输入校验缺失)、Medium 三条(日志脱敏不全)。最后扫到左边 @code-reviewer,展示 Findings Table 3-5 条命名 / DRY 建议。
[话术] "右边 security 按严重程度排序:Critical 一条词库泄漏、High 两条校验缺失。左边 code-reviewer 找了几个命名和 DRY 问题。三个视角不重叠不打架,因为每个 Agent 的 `.md` 里都明确写了它管什么不管什么——这就是 Agent **边界设计**。"
[错挥腿提示] "不重叠不打架"——直接回答 IT 负责人最常问的"会不会扯皮"。

---

## ⏱ 6:00-6:30 · 复盘第一段:讲完 Step 4 价值

[画面] 三窗保持可见,FDE 离开键盘,面向观众。
[话术] "做个 30 秒小复盘。Step 4 在传统流程里:代码评审 1 天 + 红队渗透 2 天 + 安全评审 1 天 = 4 天,而且是串行的,前一个不出报告下一个不能开始。今天 **30 秒并行拿到三份**,不只是快,是让安全和质量评审从'瓶颈'变成'随时调用'。"
[错挥腿提示] "瓶颈变成随时调用"——重定向客户的思维,从"省时间"到"流程重构"。

---

## ⏱ 6:30-7:00 · Step 5 启动 · 召唤 @release-engineer

[画面] 切回单个 Chat 窗口(中间那个,关掉左右两个或缩到角落)。输入框粘 `/ship-release` prompt + release_notes 内容(包含 Added / Changed / Security 三段)。回车。
[话术] "Step 5,最后一步。**现在我召唤 @release-engineer**。注意我用的是 `/ship-release` 这个 slash command——又是一个 prompt 模板。它内置了我们公司发布流程的所有动作:pre-flight 检查、CHANGELOG 段落、release notes 模板、PR 描述 + sign-off checkbox。"
[错挥腿提示] 强调 "slash command 是公司流程的封装",这是给"DevOps / 平台工程"角色听的。

---

## ⏱ 7:00-7:30 · @release-engineer 输出 5 件产物

[画面] Chat 区依次流式输出:① Pre-flight Checklist(要求看 npm test 输出、CHANGELOG.md 更新、版本号 bump) ② `## [0.2.0] - 2026-XX-XX` 风格的 CHANGELOG 段落 ③ Release Notes 完整 markdown(Added / Changed / Security / Migration Notes / Rollback Steps) ④ PR 描述模板(含审核运营 sign-off checkbox) ⑤ 最后一句"未执行 git commit,等待人工 sign-off"。
[话术] "看它出了什么:发布检查清单、CHANGELOG 段落、完整 release notes、PR 描述含 sign-off 框。注意——**它没有真的 git commit**。为什么?因为我们在 copilot-instructions.md 里写了'绝不 force-push 到 main、提交前必须 npm test 通过、release 必须人工 sign-off'。**Copilot 尊重发布纪律**。"
[错挥腿提示] **"尊重发布纪律"** 是 IT 信任的核心。AI 不是不可控的,它在你定义的边界内工作。

---

## ⏱ 7:30-8:00 · 复盘 + 收尾:"刚才发生了什么 + 审计痕迹"

[画面] 镜头切到 VS Code 的 source control 面板,展示 3 个文件的改动状态(unstaged),终端展示 npm test 历史。如果有 git log 可以快速 `git log --oneline -5` 让客户看到提交历史的清洁性。
[话术] "刚才 8 分钟发生了什么?一个 issue,5 个 Agent 接力,5 个 prompt 输入,产出 1 份设计、3 个文件代码、9 条 +9 条单测、3 份评审报告、1 份 release 包。**全过程在 Chat 里有完整对话记录,所有文件改动在 git diff 里,所有测试结果在 terminal 里——审计痕迹一条不少**。"
[错挥腿提示] **"审计痕迹一条不少"** 是合规负责人听的话。如果在场有合规 / 安全负责人,这一句要重读。

---

## 🎯 Demo 3 收束(切回 PPT 第 14 页之前的最后 30 秒)

[画面] 切回 PPT 第 14 页。
[话术] "Demo 3 到这里。一句话:这套流水线不是'AI 写代码',是'AI 按你们公司的工程纪律办事'。10 个 Agent + 6 个 prompt 模板,**整个工程文化被 Copilot 复制 N 倍**。下面我们用三个数字收尾,然后给 90 天落地路线图。"
[错挥腿提示] 这一段不在 8 分钟内,是切回 PPT 的衔接句。说完立刻进 PPT 第 15 页(三个数字)。

---

## 🆘 全流程兜底速查(贴在屏幕侧边)

| Step | 故障 | 即时动作 | 兜底文件 |
|---|---|---|---|
| 1 | @architect 90 秒没出图 | 切到 `fallback/01-architect-output.md`,口播"这是我们昨晚跑同样 prompt 的输出" | `fallback/01` |
| 2 | Agent 模式卡住 / 改文件失败 | `git diff src/moderation.js` 给客户看预填实现,口播"这是 Copilot 完成后的等效代码",打开 `fallback/02` | `fallback/02` |
| 3 | @test-engineer 给的代码有红 | **绝不现场 debug**,打开 `fallback/03-test-output.md` 讲"这是预跑过的输出,现场我们一会儿单独修" | `fallback/03` |
| 4 | 任一窗口卡 30 秒不动 | 不要等,直接打开 `fallback/04-review-reports.md`,口播"我们看一下三份预跑报告关注的角度完全不同" | `fallback/04` |
| 5 | @release-engineer 没出 CHANGELOG | 打开 `fallback/05-release-notes.md`,"这是预生成的完整版本,PR 模板直接可用" | `fallback/05` |
| 通用 | Copilot 整体响应慢 | 不要解释技术原因,只说"网络小波动,我直接给大家看产物",立刻切 fallback | 任意 fallback |
| 通用 | VS Code 卡死 | Cmd+Tab 切回 PPT 第 14 页,**5 个 fallback 文件全部在浏览器上打开切换讲解** | 5 个 md |

> 🎯 核心纪律:**Demo 3 严禁超过 8 分钟**。
> Step 4 那 1 分钟是 IT 全场最大哇点,前 3 步任一超时立刻砍 Step 1 的"@product-reviewer 复核"环节。
> 整个 demo 主线就一句:**"每个 Agent 都有边界,Copilot 按你的纪律办事"**——任何细节问题都把客户带回这一句。
