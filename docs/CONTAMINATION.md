# Contamination

A public benchmark contaminates itself. Once tasks are on GitHub they get crawled,
copied into tutorials, and swept into the next model's training data. Scores then
drift upward while real ability does not. This is well documented across the
field, and detection methods (n-gram overlap, membership inference, Min-K% Prob)
are unreliable enough that you should not lean on them.

So ToolPick does not claim to be contamination-proof. It is honest about the
tradeoff and mitigates where it can.

## What ToolPick does

- **Versioned, dated task sets.** Every result should record the suite version and
  the model's training cutoff. A score is only trustworthy when the tasks are
  newer than the model that took them.
- **A generative task template.** The failure modes (distractors, policy traps,
  pressure) are described in `docs/METHODOLOGY.md` precisely enough that fresh
  tasks can be authored on the same template, so the public set can be rotated and
  a private hold-out can be generated from the same rules.
- **Structural difficulty, not memorisable trivia.** The tasks turn on *policy*
  and *tool overlap*, not on facts a model could memorise. A model that has seen
  the exact prompt still has to obey the policy; that is harder to game than a QA
  pair.

## What it cannot do

It cannot guarantee that a given model has not seen these exact tasks. If you need
a number you can defend to a board, an auditor, or a customer, a public benchmark
is the wrong instrument by definition.

## The honest recommendation

For a real production decision, evaluate on **fresh, private tasks built from your
own tools and your own policy, after the model's training cutoff**. That is
structurally uncontaminated: data the model has never seen cannot have leaked into
it. Freshness beats forensics.

That private, in-VPC, contamination-free version, over your own MCP servers and
mapped to your compliance controls, is what [Groow Labs](https://groowlabs.com)
does as a service. This public benchmark is the generic, shareable slice of it.
