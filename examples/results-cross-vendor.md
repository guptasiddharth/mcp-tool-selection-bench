# ToolPick results: cross-vendor

Five current-generation flagships from five different vendors, served through
[Fireworks AI](https://fireworks.ai), on the full 156-task suite (10 domains),
single seed, first-tool selection under policy. Total inference cost for this
whole table was about 1 US dollar.

## Decision table (95% clustered CIs)

| Model | Vendor | Correct | Policy violations | Wrong-tool | Reads-first |
|---|---|---|---|---|---|
| Kimi K3 | Moonshot | 0.87 [0.82, 0.92] | **0** | 4 | 12 |
| gpt-oss-120b | OpenAI (open weights) | 0.85 [0.79, 0.90] | **6** | 8 | 9 |
| Qwen 3.8 Max | Alibaba | 0.83 [0.77, 0.89] | **0** | 6 | 18 |
| DeepSeek V4 Pro | DeepSeek | 0.81 [0.76, 0.86] | **0** | 10 | 20 |
| GLM 5.2 | Zhipu | 0.78 [0.73, 0.83] | 1 | 5 | 16 |

Policy adherence (the safety axis) as a rate: Kimi K3, Qwen 3.8 Max, and DeepSeek
V4 Pro score a clean 1.00; GLM 5.2 is 0.99; gpt-oss-120b is 0.96, the only model
that breaks policy at scale.

## What it shows

The five flagships are nearly tied on correctness (0.78 to 0.87, with overlapping
intervals). They separate on **safety**, not score. gpt-oss-120b is the
second-highest scorer yet the only model that violates policy at scale: 6
forbidden or destructive actions, against 0 or 1 for every other model. A
leaderboard that ranks on correctness alone would place gpt-oss near the top and
never surface those 6 violations. Kimi K3 is the exception that wins on both axes,
top score and zero violations.

This reproduces, on an entirely different vendor set (DeepSeek, Moonshot, Zhipu,
Alibaba, OpenAI), the same lesson as the Anthropic 5 lineup in the main README:
raw score does not tell you which model is safe for a job where a forbidden action
is costly. The result is not an Anthropic quirk. It is the shape of tool-use
evaluation across the market.

## Honesty and scope

- Single seed, first-tool selection only, not full multi-step trajectories.
- Models are the current hosted flagships on Fireworks AI; a vendor's own API may
  serve a slightly different build.
- GLM 5.2 had 12 endpoint errors (503 capacity), counted here as misses, so its
  0.78 is a floor (about 0.85 on completed tasks).
- Policy definitions are ours (see `docs/METHODOLOGY.md`); defensible design
  choices, not universal law.
- Reproduce with `toolpick run --provider litellm --model fireworks_ai/accounts/fireworks/models/<model>`
  then `toolpick report results/*.json` and `toolpick analyze results/*.json`.
