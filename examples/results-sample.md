# ToolPick results

Suite `core` · 36 tasks · clustered by domain (95% bootstrap CIs).

| Model | Correct | Tool selection | Parameter acc. | Policy adherence |
|---|---|---|---|---|
| `baseline` | 0.28 [0.00, 0.42] | 0.75 [0.67, 0.83] | 0.28 [0.00, 0.42] | 0.86 [0.75, 1.00] |
| `cross-domain-tools` | 0.19 [0.00, 0.42] | 0.50 [0.42, 0.58] | 0.19 [0.00, 0.42] | 0.86 [0.75, 1.00] |

## Correct, by domain

| Model | files | payments | support |
|---|---|---|---|
| `baseline` | 0.00 | 0.42 | 0.42 |
| `cross-domain-tools` | 0.00 | 0.42 | 0.17 |

## Paired vs baseline `baseline` (correct)

| Model | Delta (paired, clustered CI) |
|---|---|
| `cross-domain-tools` | delta -0.083 [-0.250, +0.000] (not significant) |

_A delta whose interval excludes zero is a real difference on this suite; one that crosses zero is noise, however large the point estimate looks._
