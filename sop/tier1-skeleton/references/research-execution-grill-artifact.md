# Research execution Grill artifact contract

`execution-grill.json` 是已经批准的 proposal 到实现/实验之间的阻断型契约。它不评价 idea 是否值得做。

## 顶层字段

| 字段 | 要求 |
|---|---|
| `schema_version` | 固定为 `1` |
| `proposal_id` | 稳定 ID,非空 |
| `proposal_source` | 本地权威 proposal 文件路径 |
| `proposal_hash` | 当前 proposal 文件的实际 SHA-256 |
| `controller_context_id` | 生成/实施契约的主控 context ID |
| `checkpoint` | `pre_implementation` 或 `pre_scale` |
| `status` | `blocked`、`implementation_ready` 或 `scale_ready` |
| `claims` | 非空 claim 列表,每项有 `id` 与 `text` |
| `non_goals` | 非空字符串列表 |
| `ambiguities` | 歧义列表;ready 时不得有未解决的 P0/critical/high 项;blocking resolution 必须由 `proposal:<locator>` 或带 SHA-256 的 human decision artifact 授权 |
| `claim_experiment_matrix` | 每个核心 claim 的 experiment/metric/oracle/success/kill 映射 |
| `baseline_fairness` | 每个 baseline 的七个 `comparability` 对象;每项只有一个 `status`,可取 `matched`、`not_applicable`、`mismatch_mitigated`,并绑定 evidence/mitigation |
| `design` | 实验/replication 单位、assignment、blocking、nuisance、estimand、MDE、分析、multiplicity、missing data、单一结构化 holdout 与 sequential-analysis 对象 |
| `oracle_attack` | 单一 `independence` 对象要求 independent=true、shared implementation path=false 并绑定证据;另含带 control type 的 shortcut controls |
| `pilot_scale` | 结构化 pilot pass、scale、kill condition 列表;要求 all scale conditions、any kill stop,且 look schedule 长度等于 max;`pre_scale` 还绑定可机器重算的 pilot evidence JSON 及 SHA-256 |
| `reproducibility` | 环境、代码、数据与 manifest 策略 |
| `budget` | 至少一个正数资源上限和触顶停止规则 |
| `review_plan` | 生成 review 前预冻结的 reviewer 列表;每项绑定唯一 ID、type、隔离 context 与 allowlisted GPT model;它属于 Grill core,不得在看到 verdict 后删 reviewer |
| `reviews` | 必须完整兑现 `review_plan`;输入 packet 与 review JSON 是不同非空文件,各有实际 SHA-256,并交叉绑定 proposal/checkpoint/Grill core hash;ready 时至少一份 internal pass,且全部计划内审查均不得 blocked 或保留 open blocking finding |
| `unresolved_human_gates` | ready 时必须为空 |

## Blocking ambiguity 的 HUMAN decision

`human_decision` 不能是任意说明文件。decision artifact 必须是严格 JSON,交叉绑定 `proposal_id`、`proposal_hash`、`ambiguity_id` 与最终 `resolution`,声明 `approved_by` 和 `evidence_source`,并再绑定一份不同文件的 `evidence_artifact` 及实际 SHA-256。`proposal_source` 裁决必须使用非空的 `proposal:<section-or-line-locator>`。

```json
{
  "schema_version": 1,
  "authority": "human_decision",
  "proposal_id": "approved-proposal-001",
  "proposal_hash": "sha256:<actual-proposal-file-hash>",
  "ambiguity_id": "A1",
  "resolution": "the exact approved resolution",
  "approved_by": "named decision owner",
  "evidence_source": "recorded author decision",
  "evidence_artifact": "decisions/A1-author-evidence.md",
  "evidence_artifact_hash": "sha256:<actual-evidence-hash>"
}
```

## Pre-scale pilot evidence

`pre_scale` 不能用任意日志、截图或“pilot 看起来不错”的说明解锁。`pilot_scale.pilot_evidence` 必须指向严格 JSON,其 SHA-256 写入 `pilot_evidence_hash`;JSON 必须绑定当前 proposal 和 `pilot_plan_hash`,并为 `pilot_pass_conditions`、`scale_conditions`、`kill_conditions` 中每个唯一 condition ID 提供恰好一个实际观测值。每个观测还必须用 `source_artifact`、实际 `source_hash` 与 RFC 6901 风格 `source_json_pointer` 绑定原始 JSON 结果;validator 从原文件重新取值、严格核对 JSON 类型,再根据冻结的 operator/threshold 重算。所有 pilot pass 与 scale condition 都成立且没有 kill condition 成立时,`scale_ready` 才合法。

`pilot_plan_hash` 是 `pilot_scale` 去除 `pilot_evidence` 与 `pilot_evidence_hash` 后,按排序 key 与紧凑分隔符编码所得的 SHA-256。失败结果仍应如实写入同一结构,但顶层状态必须保持 `blocked`。

```json
{
  "schema_version": 1,
  "proposal_id": "approved-proposal-001",
  "proposal_hash": "sha256:<actual-proposal-file-hash>",
  "checkpoint": "pre_scale",
  "pilot_plan_hash": "sha256:<canonical-pilot-plan-hash>",
  "condition_results": [
    {"condition_id": "P1", "observed": "pass", "source_artifact": "runs/pilot-results.json", "source_hash": "sha256:<raw-results-hash>", "source_json_pointer": "/conditions/P1"},
    {"condition_id": "S1", "observed": 0.04, "source_artifact": "runs/pilot-results.json", "source_hash": "sha256:<raw-results-hash>", "source_json_pointer": "/conditions/S1"},
    {"condition_id": "K1", "observed": 0.05, "source_artifact": "runs/pilot-results.json", "source_hash": "sha256:<raw-results-hash>", "source_json_pointer": "/conditions/K1"}
  ]
}
```

## Reviewer 类型

- `internal_blind_gpt`:隔离上下文的 GPT/Codex 只读审查;`reviewer_model` 必须是当前 allowlist 中的 `gpt-5.6-sol`、`gpt-5.6-terra` 或 `gpt-5.6-luna`;是 ready 的必需门,但不等于外部审查。
- `human_domain_reviewer`:项目内部或合作方的人类领域审查。
- `external_human_reviewer`:有可核验来源的真实外部人类审查。

不得使用 `external_review`、`simulator_review=false` 或伪造的 `gpt-*` 名称把模型审查升级成外部/允许模型。人类审查可作为追加证据,不能替代 `internal_blind_gpt`。先把完整 reviewer 集合写入 `review_plan`,再计算 Grill core hash 和发起审查;任一计划内 review 缺失、blocked,或仍有 open P0/critical/high finding,都会阻断 ready。一份 pass 不得覆盖或删除另一份反对意见;修改 review plan 会改变 core hash,使旧 review 失效。

## 最小示例

```json
{
  "schema_version": 1,
  "proposal_id": "approved-proposal-001",
  "proposal_source": "docs/proposal.md",
  "proposal_hash": "sha256:<actual-proposal-file-hash>",
  "controller_context_id": "controller-session-001",
  "checkpoint": "pre_implementation",
  "status": "implementation_ready",
  "claims": [{"id": "C1", "text": "Method improves the primary outcome under matched budget."}],
  "non_goals": ["Do not redesign the approved research question."],
  "ambiguities": [],
  "claim_experiment_matrix": [{
    "claim_id": "C1",
    "experiment_id": "E1",
    "metric": "primary_metric",
    "oracle": "independent_reference_evaluator",
    "success_criterion": "pre-registered lower bound is exceeded",
    "kill_criterion": "correctness fails or effect lower bound is not exceeded"
  }],
  "baseline_fairness": {"rows": [{
    "baseline": "strongest_public_baseline",
    "comparability": {
      "data": {"status": "matched", "evidence": "same frozen split manifest"},
      "model": {"status": "matched", "evidence": "same model hash"},
      "tuning_budget": {"status": "matched", "evidence": "same trial cap"},
      "inference_budget": {"status": "matched", "evidence": "same token cap"},
      "tools": {"status": "matched", "evidence": "same tool allowlist"},
      "stopping_rule": {"status": "matched", "evidence": "same stop rule"},
      "judge": {"status": "matched", "evidence": "same blind judge"}
    }
  }]},
  "design": {
    "experimental_unit": "task instance",
    "replication_unit": "independent seed by task block",
    "assignment": "paired seeded assignment",
    "blocking_strategy": "block by task family and checkpoint",
    "nuisance_factors": ["task family", "model checkpoint"],
    "primary_estimand": "paired mean primary-metric difference",
    "target_effect_or_mde": "primary-metric delta of 0.03",
    "variance_basis": "variance estimate from a frozen baseline pilot",
    "sample_size_or_seed_plan": "paired power plan requires five seeds across all task blocks",
    "analysis_plan": "paired interval with preregistered robustness analysis",
    "multiplicity_policy": "one primary endpoint; Holm correction for secondary endpoints",
    "missing_data_policy": "execution failures count as failures; no silent exclusion",
    "holdout": {
      "access": "sealed",
      "tuning_access": false,
      "evidence": "split manifest hash and access log",
      "unsealing_authority": "named final-evaluation owner"
    },
    "sequential_analysis": {
      "optional_stopping_allowed": false,
      "registered_max_looks": 1,
      "evidence": "one frozen pilot look in the preregistration"
    }
  },
  "oracle_attack": {
    "independence": {
      "independent": true,
      "shared_implementation_path": false,
      "evidence": "separate reference evaluator and fixtures"
    },
    "rows": [{
      "risk": "judge shortcut",
      "detection": "blind label permutation and adversarial negative control",
      "control_type": "both"
    }]
  },
  "pilot_scale": {
    "pilot_pass_conditions": [{"id": "P1", "measure": "correctness", "operator": "==", "threshold": "pass"}],
    "scale_conditions": [{"id": "S1", "measure": "effect_lower_bound", "operator": ">=", "threshold": 0.0}],
    "kill_conditions": [{"id": "K1", "measure": "failure_rate", "operator": ">=", "threshold": 0.2}],
    "scale_requires_all_conditions": true,
    "stop_on_any_kill": true,
    "max_interim_looks": 1,
    "interim_look_schedule": ["after frozen pilot completion"]
  },
  "reproducibility": {
    "env_lock": "environment lock path",
    "code_ref_policy": "clean immutable commit",
    "data_ref_policy": "versioned data manifest",
    "manifest_path": "runs/manifest.json"
  },
  "budget": {"limits": {"gpu_hours": 10}, "stop_rule": "halt at or above limit"},
  "review_plan": [{
    "reviewer_type": "internal_blind_gpt",
    "reviewer_id": "isolated-review-1",
    "reviewer_context_id": "review-session-001",
    "reviewer_model": "gpt-5.6-sol"
  }],
  "reviews": [{
    "reviewer_type": "internal_blind_gpt",
    "reviewer_id": "isolated-review-1",
    "reviewer_context_id": "review-session-001",
    "reviewer_model": "gpt-5.6-sol",
    "input_artifact": "reviews/grill-review-packet-1.json",
    "input_hash": "sha256:<actual-review-packet-hash>",
    "artifact": "reviews/grill-review-1.json",
    "artifact_hash": "sha256:<actual-review-json-hash>",
    "status": "pass"
  }],
  "unresolved_human_gates": []
}
```

每个 review input packet 至少是以下严格 JSON object;`grill_core_hash` 是最终 Grill JSON 去除顶层 `reviews` 后按排序 key、紧凑分隔符编码得到的 SHA-256:

```json
{
  "schema_version": 1,
  "proposal_id": "approved-proposal-001",
  "proposal_hash": "sha256:<actual-proposal-file-hash>",
  "checkpoint": "pre_implementation",
  "grill_core_hash": "sha256:<canonical-core-hash>"
}
```

对应的 review artifact 必须是不同文件,并逐字段交叉绑定:

```json
{
  "schema_version": 1,
  "reviewer_type": "internal_blind_gpt",
  "reviewer_id": "isolated-review-1",
  "reviewer_context_id": "review-session-001",
  "reviewer_model": "gpt-5.6-sol",
  "input_hash": "sha256:<actual-review-packet-hash>",
  "proposal_hash": "sha256:<actual-proposal-file-hash>",
  "grill_core_hash": "sha256:<canonical-core-hash>",
  "verdict": "pass",
  "findings": []
}
```

`findings` 的每项必须包含 `id`、`severity`(`p0`/`critical`/`high`/`medium`/`low`/`info`)、`status`(`open`/`resolved`)与 `summary`。ready 契约的全部当前审查都不得 blocked 或存在 open P0/critical/high finding。

参考验证命令:

```sh
python3 scripts/validate_research_execution_grill.py execution-grill.json --required-checkpoint pre_implementation
```

退出码:ready 为 `0`;结构/内容违约为 `1`;读取或解析失败为 `2`;结构完整但状态仍 blocked 为 `3`。
