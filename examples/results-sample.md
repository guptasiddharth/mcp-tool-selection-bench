# ToolPick results

Suite `core` · 36 tasks · clustered by domain (95% bootstrap CIs).

| Model | Correct | Tool selection | Parameter acc. | Policy adherence |
|---|---|---|---|---|
| `baseline` | 0.28 [0.00, 0.42] | 0.75 [0.67, 0.83] | 0.28 [0.00, 0.42] | 0.86 [0.75, 1.00] |
| `anthropic/claude-haiku-4-5-20251001` | 0.89 [0.83, 1.00] | 0.89 [0.83, 1.00] | 0.89 [0.83, 1.00] | 0.92 [0.83, 1.00] |

## Correct, by domain

| Model | files | payments | support |
|---|---|---|---|
| `baseline` | 0.00 | 0.42 | 0.42 |
| `anthropic/claude-haiku-4-5-20251001` | 0.83 | 1.00 | 0.83 |

## Paired vs baseline `baseline` (correct)

| Model | Delta (paired, clustered CI) |
|---|---|
| `anthropic/claude-haiku-4-5-20251001` | delta +0.611 [+0.417, +0.833] (significant) |

_A delta whose interval excludes zero is a real difference on this suite; one that crosses zero is noise, however large the point estimate looks._
