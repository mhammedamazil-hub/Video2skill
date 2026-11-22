# Video2Skill — Evaluation Methodology

## Examination outcomes

Possible classifications (a skill is never universally verified based on one
successful task):

- `Experimental` — no conclusive evidence.
- `Failed` — learners could not perform the tasks.
- `Basic verified` — at least half the hidden tasks pass.
- `Strongly verified` — all hidden tasks pass.
- `Model-specific` — only the Teacher's model passes.
- `Cross-model transferable` — both same-model and cross-model learners pass.

## Hidden tasks

The Examiner Agent independently generates hidden tasks unknown to the
learners, covering:

1. Tutorial reproduction — perform the workflow exactly as demonstrated.
2. Task variations — same workflow, different parameter values.
3. Unseen tasks — apply the skill to a related task not shown in the video.
4. Troubleshooting — diagnose and resolve a common failure mid-workflow.
5. Error recovery — recover from an error introduced during execution.
6. Generalization — generalize the procedure to a new context.

## Objective verification

Verification is execution, not vibes. The Examiner does not accept an LLM's
self-declaration of success. Evidence used:

- Real files created/modified.
- Application state inspections.
- Automated assertions.
- Screenshots.
- Execution results (exit codes, stdout/stderr).
- Independent evaluation by a fresh learner instance.

Each learner runs in a sandbox with restricted filesystem, network, time, and
memory. Where no sandbox exists, execution is refused.

## Same-model vs cross-model

- **Learner A** uses the same foundation model as the Teacher, fresh isolated
  (no teacher history, no private notes, no hidden answers).
- **Learner B** uses a different foundation model, same skill package and
  equivalent permitted resources.

Equivalent testing conditions are enforced. Model IDs, versions,
configurations, tool permissions, and results are recorded.

## Scoring

For each learner: passed / failed across hidden tasks. Ratio determines the
outcome per the classifications above. The combined outcome reflects whether
the skill transfers across models.

## Regression testing

Any changed version is reset to `draft` and must be re-examined before
regaining verification status. Historical versions are preserved; a verified
skill never loses verification silently after modification.
