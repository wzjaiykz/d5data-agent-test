# Agent Data Quality Audit — Restaurant Portfolio Traffic Change

## 0. Tools and independent re-verification

- **Tools used:** Python 3.12.10, `openpyxl` 3.1.5, the supplied XLSX files, and the supplied scorer snapshot. The audit CLI in `src/audit/` reads the source ledger directly; it never treats Gold as the primary source. No model or API was run.
- **AI use:** an AI assistant was used to help structure this answer and to write the audit helper/tests. Every number and every quoted score below was re-read from the supplied workbooks or the frozen scorer ledger; the assistant was not used as an authority for a fact.
- **Independent checks:** I recomputed the two brand totals from 36 leaf rows, checked all 76 original values, checked the 12 period-store statuses, checked all 6 portfolio chains and all 6 daypart chains, and inspected all 5 rollouts and 3 probes at cell level. I also checked the public weights against the executable policy and replayed the frozen rewards.
- **Scope I could not verify:** the supplied `validator.py` is not standalone. It imports `bound_cache`, a semantic cache and `llm_judge/contract.json`, none of which are in the package; the package itself says the snapshot is not a runnable verifier. I therefore did not rerun the semantic judge. The exact cause of a few zero/partial completions is inferred from the workbook content plus the frozen `completion` record, not from a live replay.

## 1. Task feasibility and factual baseline

### 1.1 Recomputed baseline

The source ledger has two comparison blocks. Each block has 6 stores × 3 dayparts = 18 leaf rows plus one brand-total row, and two value columns. That is 76 original values across the two blocks.

| Comparison | Prior total | Current total | Net change | Portfolio bridge (impact / contribution) | Daypart chain (change / contribution) |
| --- | ---: | ---: | ---: | --- | --- |
| 2023→2024 | 374 | 422 | +48 (+12.8342%) | continuing +23 / 47.9167%; new +89 / 185.4167%; closed −64 / −133.3333% | breakfast −11 / −22.9167%; lunch +21 / 43.7500%; dinner +38 / 79.1667% |
| 2024→2025 | 422 | 481 | +59 (+13.9810%) | continuing +31 / 52.5424%; new +79 / 133.8983%; closed −51 / −86.4407% | breakfast +1 / 1.6949%; lunch +17 / 28.8136%; dinner +41 / 69.4915% |

The bridge closes:

- **2023→2024:** continuing stores 310→333 = +23; new store 0→89 = +89; closed store 64→0 = −64; +23 + 89 − 64 = +48.
- **2024→2025:** continuing stores 371→402 = +31; new store 0→79 = +79; closed store 51→0 = −51; +31 + 79 − 51 = +59.

The daypart chains also close, with the three impact categories shown as continuing/new/closed:

| Period | Daypart | Base→current | Δ | Components (continuing + new + closed) |
| --- | --- | ---: | ---: | --- |
| 2023→2024 | breakfast | 82→71 | −11 | +4 + 7 − 22 |
| 2023→2024 | lunch | 152→173 | +21 | +11 + 34 − 24 |
| 2023→2024 | dinner | 140→178 | +38 | +8 + 48 − 18 |
| 2024→2025 | breakfast | 71→72 | +1 | +4 + 6 − 9 |
| 2024→2025 | lunch | 173→190 | +17 | +12 + 29 − 24 |
| 2024→2025 | dinner | 178→219 | +41 | +15 + 44 − 18 |

**Status boundaries are period-specific:**

- 2023→2024: continuing = 青禾店, 西苑店, 星港店, 北站店; new = 湖滨店; closed = 客运港店.
- 2024→2025: continuing = 青禾店, 星港店, 北站店, 湖滨店; new = 云庭店; closed = 西苑店.

Source evidence: `materials/门店餐段客流台账.xlsx!客流对比_2024!A4:G22` and `客流对比_2025!A4:G22` (store/format/daypart/status/current/prior), with totals at `E22:F22`; the unit and status rules are at `口径说明!B4:B6`. Gold agrees with these figures at `expected_answer.xlsx!门店组合桥!E2:G7`, `餐段归因!G2:K7` and `门店状态!A2:J13`. The Gold `原值追溯` sheet contains the same 38 period rows (36 leaves + 2 totals) with source ranges.

### 1.2 Is the task fair and verifiable?

**The materials are sufficient for the business question, and Gold is factually consistent with them.** I found no arithmetic conflict between source, Gold and instruction. The 76 values are recoverable; statuses are unambiguous; the status rules are written down; new/closed zero placeholders are explicitly not comparable-year values.

There are, however, three design problems:

1. **Gold is entirely static, while the instruction demands a “recalculable” workbook.** `expected_answer.xlsx` has zero formula cells; every derived value is a literal. `原值追溯` is also static values plus source ranges. The public rubric says formulas versus static values are equivalent, so the instruction and rubric disagree. A candidate who follows “recalculable” is asked to do work Gold does not demonstrate. **Minimal fix:** either make Gold formula-driven (one formula chain per bridge/daypart and controls that recompute) or change the instruction to “editable and auditable”; do not keep both claims.
2. **The instruction leaks a shortcut.** `instruction.md` ends with: “可直接运行 `python3 /workspace/solution/solve.py ...` 生成完整归因工作簿”. That tells the Agent a complete solution may already exist. If the script exists, the task tests script execution, not attribution; if it does not, the instruction sends the Agent into a dead end. **Minimal fix:** remove the hint and keep `solution/solve.py` out of the task environment.
3. **Process requirements are unverifiable.** “First create an empty deliverable skeleton” and “review the existing operating procedures” are not observable in a final XLSX and are not scored by the rubric. **Minimal fix:** drop them, or turn them into explicit, separately scored checkpoints with an artifact (for example a timestamped log).

**Main difficulty:** the hard part is business attribution — deciding which stores are comparable in each period, using the brand net change as the common denominator, preserving the closed-store offset, and keeping the two periods separate. It is not file parsing in principle. In the current scoring system, however, parsing dominates the score (see §2 and §4). That is a design failure, not a candidate failure.

## 2. Rollout risk-oriented spot check

I checked one core numerical chain and one control chain for each rollout, then expanded only where a zero completion suggested a binding problem. All five workbooks contain the correct totals, bridges, daypart chains and status boundaries in the audited scope.

| Rollout | Scope checked | Content conclusion | Main problem / merit | Current score reasonable? | Evidence |
| --- | --- | --- | --- | --- | --- |
| rollout-01 | total; 6 bridge chains; 3 daypart chains; contribution sums | Correct: 374→422 +48; +23/+89/−64; −11/+21/+38; contributions close | Complete formulas and checks; R5 and R6A–E are all zero despite correct tables | **No** — 0.294424 is a false negative | `品牌总览!H5=48`; `组合桥接!J5:J7=47.9167%/185.4167%/−133.3333%`; `餐段归因!L5:L7=−22.9167%/43.75%/79.1667%`; `Q5:Q8=通过` |
| rollout-02 | total; bridge; daypart; 15 checks | Correct: 48 and 59; all three daypart contributions | Correct tables use “时段” and a different layout; R5 is zero | **No** — 0.294424 is a false negative | `01_品牌总览!I4=48`; `02_组合桥接!M4:M6`; `03_时段归因!N7/N11/N15`; `07_勾稽检查!G4:G18` |
| rollout-03 | total; bridge; daypart; 26 checks | Correct: 48 and 59; all contributions; all checks pass | R5 and R6C are zero although `餐段归因!N7/N11/N15` are “通过” | **No** — 0.944424 should be full | `结论摘要!D7=48`; `门店组合桥接!J4:J6`; `餐段归因!J7/J11/J15`; `N7/N11/N15=通过` |
| rollout-04 | total; bridge; daypart; 28 checks | Correct: 48 and 59; all chains; explicit 100% control rows | Correct workbook; R6B/E zero and score collapses to 0.35 | **No** — 0.35 is a false negative | `总览结论!D2=48`; `组合桥接!H2:H4`; `餐段归因!J2=−22.9167%`; `核对检查` rows “三类组合贡献合计=100%” and “三餐段贡献合计=100%” both 通过 |
| rollout-05 | total; bridge; daypart; 24 checks | Correct: 48 and 59; all contributions; all checks pass | Best control presentation; score 1.0, but its own R2 completion is only 0.947368 | **Partly** — 1.0 may be right in content, but R2 is silently ignored | `品牌总览!I2=48`; `组合桥!I2:I4`; `时段贡献!L2/L5/L8`; `勾稽检查` all 通过 |

**The important pattern:** all five rollouts are correct in the audited content, but their scores are 0.294, 0.294, 0.944, 0.350 and 1.000. The score spread is a **layout/binding spread**, not a quality spread. The zeros are not evidence that the candidates failed the business task.

Exact score algebra from the frozen ledger:

- rollout-01: `0.234493 × R4(1) + 0.059931 × R9(1) = 0.294424`; R5 and all R6A–E are zero.
- rollout-02: same 0.294424; R5 and R6B/C/E are zero.
- rollout-03: `1.0 − 0.055576 = 0.944424`; only R5 and R6C are zero.
- rollout-04: `0.234493 + 0.055576 + 0.059931 = 0.350000`; R6B/C/E are zero.
- rollout-05: all effective owners are 1.0, hence 1.000000.

Two details deserve emphasis:

- **rollout-04 is not missing the control facts.** Its `核对检查` sheet explicitly contains “三类组合贡献合计 = 100%” and “三餐段贡献合计 = 100%”, both with left/right = 1 and result 通过. The scorer still records R6B and R6E as zero. This is a table-binding false negative, not a missing conclusion.
- **rollout-05’s R2 = 0.947368 is not a visible content gap.** Its `明细追溯!H2:I37` contains all 36 leaf pairs; its `品牌总览` contains the totals. The 4/76 shortfall is most plausibly four unbound total values (two totals × two columns), not four wrong source values. Yet the score is 1.0 because R2 has zero effective weight. That is a false positive for the R2 dimension, even if the overall 1.0 happens to be reasonable.

## 3. Probe review

| Probe | Core defect | Reasonable treatment | Current/possible misjudgment | Evidence |
| --- | --- | --- | --- | --- |
| probe-01 | Uses the continuing-store change (+23) as the denominator for every 2023→2024 contribution instead of brand net +48. Absolute changes and the second period are correct. | Preserve R1/R2/R3, all absolute changes and the complete 2024→2025 block; zero the signed leaves of the affected R4/R5 chains. Treat the six wrong contributions as **one root cause**, not six independent errors; do not also zero R6B/E for the same denominator. | The current policy's emphasis on contribution sums can over-penalize or mis-bind; a fair scorer must localize the denominator error to one period. | `审查样本!J2=23`, `K2=2.0869565`; `J3:J8=23`; `K4=89/23=3.8695652`, `K8=38/23=1.6521739`; second period `J9=59` is correct. |
| probe-02 | Honest partial completion: only 2023→2024 exists; the last row says “仅完成第一比较期间”. First-period values are correct. | Full credit for the completed first-period leaves; zero for absent second-period leaves; R1 remains usable. This should land near 50% of period-weighted items, not 0 and not 1. Do not penalize the explicit unresolved/partial statement. | A parser that treats absent rows as zero is correct here; a parser that infers values or treats the control row as a second period would be a false positive. | `审查样本!A2:N8` only 2023→2024; `N9='仅完成第一比较期间'`; `J2=48`. |
| probe-03 | A shell: 20 repeated rows, a toy `=1+1` formula, the words “勾稽通过”, and no traffic values. | **0 / veto.** It is substantively empty; headings, self-certification and formulas without data earn no credit. Apply the “形式替代实质” and “自证替代证据” gates. | The current undisclosed R9 gives it **1.0** (5.9931% of the score) because it sees the keywords “总/分母”, “组合/贡献” and “餐段/贡献” plus any formula in the row. Gold gets R9 = 0. This is a concrete false positive. | `审查样本!A1:O21`; only numeric cells are 1..20 and the cached 2; `J2:J21='勾稽通过'`; `O2='=1+1'`. |

## 4. Scorer diagnosis and rubric redesign

### 4.1 Five highest-severity issues

| Severity | Issue | Evidence | Minimal fix |
| --- | --- | --- | --- |
| **Critical** | The public weights are not the weights that produce the score. | `scoring_params.json` declares R1 5%, R2 8%, R3 18%, R4 25%, R5 25%, R6 10%, R7 9%. `fresh_owner_policy.py:3` uses only R4 23.4493%, R5 5.5576%, R6B 30%, R6E 35%, R9 5.9931%. R1/R2/R3/R7 = 0; R5 loses 19.4424 points; R6 gains 55 points; R9 is not in the rubric. The five scores in `current_scores.md` are exactly reproduced by this hidden vector. | Publish and enforce **one** vector. Either apply the declared 7-dimension weights or declare the 5-owner vector in the rubric. Remove R9 or make it public with a small, justified weight. |
| **Critical** | The hash shortcut freezes rewards instead of recomputing the artifact. | `validator.py:22–30` hashes the workbook; if the digest is in `frozen_owner_policy.json`, it returns the stored reward and completion without program checks. All 5 rollouts and Gold are in the frozen set. The same content resaved under a different hash goes down a different path. | Always recompute program evidence and the score. Use hashes only to cache semantic model outputs, never to bypass the rubric. |
| **High** | Correct workbooks receive zero on R5/R6 because table binding is exact-name/shape dependent. | rollout-01 and -02 are content-correct but R5 = 0; rollout-04 is content-correct but R6B/E = 0 despite explicit 100% controls; rollout-03 is content-correct but R5/R6C = 0. The rubric promises that layout, wording and formulas-versus-static are equivalent; `program_judge.py:74–83` recovers headers by exact normalized field names and a fixed row-oriented shape. | Bind by logical keys and accepted aliases (餐段/时段, 新开/新开门店, 带符号贡献/签署贡献, 分母/净变动, etc.), support wide and long shapes, and zero only the unbound leaf. A parse failure must never zero the whole artifact. |
| **High** | The undisclosed R9 heuristic rewards the wrong artifact. | `fresh_owner_policy.py:6–21` scores keyword co-occurrence plus any formula. Gold gets R9 = 0; probe-03 (empty shell) gets R9 = 1.0; every rollout gets 1.0. `scorer_behavior.md` admits R9 is not one of the seven declared dimensions. | Delete R9. If formula dependency is required, make it a public, low-weight check that requires both a correct formula and a correct evaluated value, with a value/key binding. |
| **High** | The declared deductions and several declared dimensions are dead code. | `current_rubric.md:23–29` defines five D coefficients; `fresh_owner_policy.py` applies none. R1/R2/R3/R7 are computed but not weighted; R6 only uses B/E, not A/C/D/F. rollout-05 remains 1.0 while R2 = 0.947368. | Implement D rules as explicit caps/gates; apply all declared dimensions; if a dimension is diagnostic only, say so and remove its weight. Never publish a rule that has no effect. |

Additional fairness issue: the five “real rollouts” all have correct required content. There is no evidence in this package that the scorer separates good from bad model outputs; it separates parseable from less parseable ones. That is a validity problem, not a difficulty problem.

### 4.2 False positives and false negatives

- **False positive (shell):** probe-03. It has no traffic values but earns R9 = 1.0 (5.9931%). Gold earns R9 = 0. A shell should be 0, not 6%.
- **False positive (ignored partial):** rollout-05 scores 1.0 with R2 = 0.947368. If the 72/76 shortfall is real, the score is too high; if it is a binding failure, the R2 measurement is unreliable. Either way, a 1.0 hides the uncertainty.
- **False negative (correct workbook):** rollout-01 and rollout-02 score 0.294424 with correct totals, bridges, dayparts and controls. R5 is zero in both; R6B/E are zero. This is the clearest failure.
- **False negative (correct workbook):** rollout-04 scores 0.350000 with all required chains and explicit 100% controls. The effective weights put 65% on the two control aggregates and then fail to bind them.
- **False negative (minor):** rollout-03 scores 0.944424 even though its daypart chains and checks are complete; only R5/R6C are zero.

### 4.3 Proposed rubric (100%)

The new rubric is deliberately leaf-based. A dimension is the weighted average of its leaves, not an all-or-nothing gate. This preserves credit for absolute changes when a denominator is wrong, and it prevents a parser failure from erasing the whole artifact.

| ID | Scoring object | Weight | Full / partial / zero conditions | Verification |
| --- | --- | ---: | --- | --- |
| R1 | Usable, editable workbook | 5% | Full: readable XLSX with brand conclusion, portfolio bridge, daypart attribution, status list and at least one control. Partial 2.5%: usable but one component missing. Zero: unreadable, empty, screenshots or headings only. | Programmatic: load, sheet/table presence, at least one numeric value per component. |
| R2 | Source fidelity: 76 original values | 10% | `10% × correct/76`. Full only if all 76 are bound to store, format, daypart, period, status and unit. A consistent whole-workbook unit conversion (e.g. visits = thousands × 1000) is accepted if the unit is stated. Mixed units zero only affected leaves. | Programmatic, key-based; compare to source, not to Gold. |
| R3 | Period-store status boundary | 15% | 12 items; each 1.0 if correct status + 3/3 daypart scope + period-correct boundary; 0.5 if status is right but one leaf/scope is missing; 0 if status is wrong or status is carried across periods. | Programmatic status comparison; human only if a label is genuinely ambiguous. |
| R4 | Portfolio bridge: 6 chains | 20% | Each chain = 0.5 × absolute-change leaf + 0.5 × signed-contribution leaf. Closed = −base, new = +current; denominator = brand net. Correct alternative layout or synonyms accepted. | Programmatic arithmetic; human only for label binding. |
| R5 | Daypart attribution: 6 chains | 20% | Each chain = 1/3 × absolute change + 1/3 × three-component reconciliation + 1/3 × signed contribution. A daypart’s own YoY rate or a continuing-only change is not a brand contribution. | Programmatic; human only for label binding. |
| R6 | Reconciliation and controls | 15% | 5 leaves per period: portfolio impact sum = net; portfolio contribution sum = 100%; daypart impact sum = net; daypart contribution sum = 100%; each daypart’s three components reconcile to its change. Show both sides; “reconciled” alone = 0. | Programmatic where values exist; human review only to confirm the two sides are actually shown. |
| R7 | Conclusion first, then evidence | 10% | 5 leaves per period: upfront total + relative change; continuing impact; new-store uplift; closed-store offset; all three dayparts itemized. Correct numbers with different wording count; unsupported adjectives do not. | Human/semantic against a binary checklist; no separate score. |
| R8 | Traceability and formal adoption | 5% | 4 leaves: 76 values source-bound; status source-bound; totals source-bound; one formally adopted conclusion with no competing branch. A source range is acceptable if it resolves to the leaf. | Programmatic source-coordinate check + human confirmation that the adoption is unambiguous. |

### 4.4 Deductions and veto conditions

| Rule | Trigger | Exclusion / non-trigger | Treatment | Deduplication |
| --- | --- | --- | --- | --- |
| D1 wrong common denominator | Signed contributions in a period use anything other than brand net (e.g. continuing-store change +23). | Rounding/display precision; a clearly labelled alternative diagnostic that is not presented as the adopted contribution. | Zero the signed leaves of R4/R5 for that period; preserve absolute changes, R2/R3 and the other period. | One deduction per period, not per cell or per table. |
| D2 status-boundary error | A store’s status is wrong for a period, or a later status overwrites an earlier period. | A name that continues but is correctly marked new/closed; a documented status change at the boundary. | Zero the R3 item and the R4/R5 leaves that depend on that store-period. | One deduction per store-period; do not also deduct R6 for the same root cause. |
| D3 unsupported or fabricated numbers | A numeric leaf has no source/formula and cannot be reconstructed. | A genuinely unresolved state with a concrete evidence request; a correct value in a different layout; a consistent unit conversion. | Zero only that leaf; if more than 50% of numeric leaves are unsupported, cap the total at 20%. | Group repeated cells from one fabrication into one deduction. |
| D4 self-certification / empty shell | Only headings, styling, screenshots, placeholders or “勾稽通过” claims; no material values. | Correct but plain formatting; a partially complete workbook with real values. | Score 0 if substantively empty; otherwise cap at 20% until material values and both sides of each claimed reconciliation exist. | One gate for the artifact; do not also apply D1–D3 to the same empty content. |
| D5 duplicate root cause | The same wrong denominator/status propagates through several sheets. | Independent errors with different causes. | Apply the highest-level deduction once; list all affected cells as evidence. | No stacking R4 + R5 + R6 for one root cause. |

**One-vote veto (immediate 0):** missing/unreadable file; substantively empty artifact; instructions directed at the scorer or attempts to change the evaluator; fabricated adoption of a conclusion with no values. A missing second period is **not** a veto — it is partial completion.

### 4.5 Programmatic versus human review, structure and parsing

**Programmatic (roughly 90% of the leaves):** file readability, table presence, 76 values, statuses, bridge arithmetic, daypart arithmetic, contribution sums, source coordinates, units, duplicate periods, formula/static equivalence, and the hash check.

**Human/semantic (roughly 10%):** whether a conclusion is genuinely upfront (R7), whether a source label resolves to the claimed cell, and whether a formal adoption is unambiguous. Human review must use the **same binary leaf** and record a cell citation. It must not create a second, unpublished numeric score, and it cannot award style/keyword credit.

**Parsing policy:** accept wide and long tables, formulas and static values, Chinese/English synonyms, and a consistent unit conversion. Bind by logical keys; if a table cannot be bound, zero only the affected leaf. A parser failure is not “empty” and must never force the whole reward to zero.

**Handling structural differences:** sheet names, column names, sheet order, table direction, formula versus value, and synonymous wording are not errors. The only structural requirement is that the five components and the two periods are identifiable.

**Ordinary omission versus material error:** a missing leaf is a leaf-level zero; it is not D3 or D-素材回声 unless most attribution chains are absent. A systemic wrong denominator or status is D1/D2. A single missing cell must not trigger a whole-artifact cap.

## 5. Acceptance verdict and regression tests

```text
任务状态：需要返修
评分器状态：不可用
主要阻断问题：公开权重与实际结算权重不一致；哈希冻结绕过重算；R5/R6 对正确工作簿产生假阴性；未公开的 R9 奖励空壳且 Gold 得 0；声明的扣分项未实现。
最小修复方案：统一并公开一套权重；删除哈希奖励捷径；用键/别名绑定表格并逐叶计分；删除或公开 R9；实现 D 规则；移除 instruction 中的 solve.py 提示并统一 Gold 与“可重算”的口径。
修复后需要重新检查的证据：5 份 rollout 的 R2/R3/R4/R5/R6/R7/R8 逐叶完成度；Gold 与 3 个 probe 的分数；R9 与 D 规则的触发记录；哈希重存件与原文的分数一致性；公开权重表与实际权重表的逐项对比。
```

### 5.1 Regression and adversarial tests

| Test | Input change | Expected behavior | Misjudgment prevented |
| --- | --- | --- | --- |
| T1 legal equivalent | Re-layout a correct workbook as long format; replace formulas with static values; convert all values to visits (×1000) and state “人次”; use `时段`/`新开门店`/`签署贡献` synonyms. | Full score. | Penalizing layout, formulas/static or unit conversion; the current R5/R6 false negatives. |
| T2 denominator error | Use probe-01’s +23 denominator for 2023→2024, keep all absolute changes and the correct 2024→2025 block. | Signed R4/R5 leaves for 2023→2024 = 0; absolute leaves, R2/R3 and 2024→2025 preserved. | Global zero from one root cause, or six duplicate deductions for one wrong denominator. |
| T3 empty shell | Use probe-03: 20 repeated rows, `=1+1`, “勾稽通过”, no traffic values. | 0 / veto. | R9 keyword/formula credit; “self-certification” credit. |
| T4 honest partial | Use probe-02: complete 2023→2024 only, explicitly “仅完成第一比较期间”. | Full first-period leaves; zero second-period leaves; about 50% of period-weighted items; usable R1. | Scoring an honest partial as full or as zero. |
| T5 status propagation | Change 西苑店 in 2023→2024 from 持续经营 to 关闭 (or in 2024→2025 from 关闭 to 持续经营). | Zero that R3 item and every R4/R5 leaf that depends on it in that period; no second R6 deduction. | Latest-status overwrite; double counting the same status error. |
| T6 hash resave | Save a correct workbook again with a different hash; keep content identical. | Same score. | `frozen_owner_policy.json` hash shortcut; score depending on file metadata. |
| T7 unit conversion | Multiply all values by 1000 and state “人次”. | Full score if every value and denominator is converted consistently. | Penalizing a valid unit; `0.5` being mistaken for 0.5%. |
| T8 one missing leaf | Delete one original value but keep the rest, formulas and controls. | R2 = 75/76; only the dependent chain leaf is zero; no whole-artifact zero. | A binding failure or one missing cell being treated as an empty artifact. |

The first four tests cover the required categories (legal equivalent, substantive error, surface compliance without evidence, partial completion); T5–T8 add the two most dangerous boundary behaviours: status leakage and hash/parse shortcuts.
