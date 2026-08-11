# ToolPick results

Suite `core` · 108 tasks · clustered by domain (95% bootstrap CIs).

| Model | Correct | Tool selection | Parameter acc. | Policy adherence |
|---|---|---|---|---|
| `anthropic/claude-haiku-4-5-20251001` | 0.92 [0.87, 0.97] | 0.92 [0.87, 0.97] | 0.92 [0.87, 0.97] | 0.95 [0.91, 1.00] |
| `anthropic/claude-fable-5` | 0.92 [0.88, 0.96] | 0.92 [0.88, 0.96] | 0.92 [0.88, 0.96] | 0.99 [0.97, 1.00] |
| `anthropic/claude-sonnet-5` | 0.84 [0.78, 0.91] | 0.84 [0.78, 0.91] | 0.84 [0.78, 0.91] | 0.99 [0.97, 1.00] |
| `anthropic/claude-opus-5` | 0.74 [0.68, 0.80] | 0.74 [0.68, 0.80] | 0.74 [0.68, 0.80] | 1.00 [1.00, 1.00] |

## Correct, by domain

| Model | calendar | crm | devops | files | payments | support |
|---|---|---|---|---|---|---|
| `anthropic/claude-haiku-4-5-20251001` | 0.83 | 1.00 | 0.92 | 0.88 | 1.00 | 0.88 |
| `anthropic/claude-fable-5` | 0.92 | 0.92 | 0.92 | 0.88 | 0.88 | 1.00 |
| `anthropic/claude-sonnet-5` | 0.83 | 0.83 | 0.83 | 0.83 | 0.96 | 0.75 |
| `anthropic/claude-opus-5` | 0.58 | 0.83 | 0.83 | 0.67 | 0.79 | 0.75 |

## Paired vs baseline `anthropic/claude-haiku-4-5-20251001` (correct)

| Model | Delta (paired, clustered CI) |
|---|---|
| `anthropic/claude-fable-5` | delta +0.000 [-0.074, +0.076] (not significant) |
| `anthropic/claude-sonnet-5` | delta -0.074 [-0.117, -0.037] (significant) |
| `anthropic/claude-opus-5` | delta -0.176 [-0.213, -0.131] (significant) |

_A delta whose interval excludes zero is a real difference on this suite; one that crosses zero is noise, however large the point estimate looks._
