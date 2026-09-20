# Packs and incremental training

Use when the user separates identity data from generalization data or asks to add
examples to an existing LoRA. This is an experiment design, not a claim that staged
training always beats a joint dataset.

## Keep three dimensions separate

- **Pack**: purpose and membership of source images, e.g. identity and generalization.
- **Family**: Anima vs Krea 2, with independent captions, caches, configs and weights.
- **Stage/run**: an actual optimization run over a frozen selection and sampling mix.

An identity pack may use white backgrounds and a few styles if requested. Describe
background and medium as variables; their captions alone do not guarantee disentanglement.
Test unseen backgrounds and styles even after stage A. A generalization pack changes
rendering/view/action/environment while preserving agreed identity and anatomy.
Do not infer body, age, appendage removal, or additional-character variation.

## Resume modes

| Mode | Meaning | Appropriate use |
|---|---|---|
| `fresh` | Initialize a new adapter on the chosen base | Baseline or joint-data control |
| `full_state` | Restore weights, optimizer/scheduler and training progress | Recover the same interrupted run |
| `weights_only` | Initialize from a previous compatible adapter; start a new run | New dataset/stage or changed training objective |

Do not assume live dataset folders hot-reload. Stop at a saved point, create a new
dataset/config version, and rebuild affected data/text caches before a new stage.
Do not use a pause/resume button to change a frozen run's recipe.

AnimaLoraStudio upstream checked at commit
`3d9d2e86045b879cd19c01ac4aa2337f45a283ab` exposes `resume_lora` (weights only)
and `resume_state` (full state). Pause snapshot recovery may override current settings.
Verify the user's installed trainer, adapter format/rank/target modules, base model,
and actual load logs; names here are not universal flags for every trainer.

- [Config fields](https://github.com/WalkingMeatAxolotl/AnimaLoraStudio/blob/3d9d2e86045b879cd19c01ac4aa2337f45a283ab/studio/domain/training.py)
- [Weight/family loading](https://github.com/WalkingMeatAxolotl/AnimaLoraStudio/blob/3d9d2e86045b879cd19c01ac4aa2337f45a283ab/runtime/training/phases/models.py)
- [Pause snapshot handling](https://github.com/WalkingMeatAxolotl/AnimaLoraStudio/blob/3d9d2e86045b879cd19c01ac4aa2337f45a283ab/runtime/training/phases/bootstrap.py)

## Stage handoff

Record in `训练记录.csv`: run ID, family, stage, manifests, config, trainer/base
version, resume mode, and parent checkpoint/run. For weights-only continuation,
preserve the parent unchanged; the new adapter already contains inherited weights
and is normally tested on the original base, not stacked with its parent again.

Mix reviewed old identity examples with new examples when testing retention. Record
effective sampling weights (including repeats/buckets), not merely raw file counts.
Neither a 1:1 mix nor a fixed LR reduction is a universal optimum. Set a fresh
schedule, compare early/mid/late checkpoints and stop when identity or prompt response
regresses. A new stage does not repair incorrect source designs automatically.

Test identity, anatomy, original outfit, unseen outfits, controllable forms/accessories,
unseen backgrounds and both seen/unseen styles using fixed prompts/seeds per family.
If resources permit, compare with a fresh A+B run to test the curriculum hypothesis.

Anima A → Anima B and Krea 2 A → Krea 2 B are independent weight lineages. Reuse
reviewed images and family-specific captions, never Anima weights as Krea 2 initialization.
Training is user-controlled; preparing these ledgers does not start any GPU job.
