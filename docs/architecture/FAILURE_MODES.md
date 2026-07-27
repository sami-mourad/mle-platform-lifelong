# Failure-Mode Matrix

| Failure | Detection | Immediate behavior | Recovery | Evidence |
|---|---|---|---|---|
| Repository 1 schema/version drift | bridge gate | block integration | align compatible contract version | cross-repository contract test |
| Duplicate or incomplete snapshot grain | bridge gate | block training | repair Repository 1 snapshot | snapshot validation |
| Feast returns missing feature | retrieval service | manual review; no probability | repair materialization or contract | incomplete-vector test |
| Feast returns ambiguous qualified names | retrieval service | manual review; no arbitrary selection | fix feature service/naming | ambiguity test |
| Candidate lacks required metric | promotion policy | reject candidate | rerun evaluation | policy tests |
| Candidate regresses beyond allowance | promotion policy | retain incumbent | improve/retrain candidate | direction-aware regression tests |
| MLflow alias move fails | release controller | active release unchanged | retry registry operation | release-controller tests |
| Active-manifest publication fails after alias move | release controller | compensate alias to previous version; serving retains prior manifest | repair release store and retry | compensation test |
| Active release missing or corrupt | readiness/load | service not ready or manual review | restore immutable release history | manifest validation tests |
| Bento artifact cannot load | runtime | manual review; no fabricated score | restore artifact or roll back | runtime failure tests |
| Model inference fails | serving application | explicit degraded response | quarantine and roll back | serving failure tests |
| Prediction trace cannot append | serving application | do not return a successful scored decision | restore durable trace sink | prediction-log tests |
| Pending labels dominate | monitoring policy | `no_data` or investigate | wait for maturity / repair label feed | delayed-label tests |
| Evidently JSON shape changes | adapter parser | fail closed if required metric cannot be found | update compatibility adapter | Evidently shape regressions |
| Monitoring recall unavailable when required | monitoring policy | not healthy | obtain matured labels/metrics | monitoring-policy tests |
| Dagster unavailable | orchestration boundary | core functions remain importable/runnable | restore orchestrator | dependency-light orchestration test |
