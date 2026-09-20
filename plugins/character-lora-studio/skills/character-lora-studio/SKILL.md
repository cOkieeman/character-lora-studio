---
name: character-lora-studio
description: Build, resume, audit, tag, curate, regularize, configure, test, and export character, outfit, combined character-outfit, or style LoRA datasets with persistent on-disk state. Use for Anima Booru-tag workflows, Krea 2 natural-language workflows, hardware-aware AnimaLoraStudio profiles, candidate scoring, regularization, checkpoint comparison, or resuming a LoRA project after context loss.
---

# Character LoRA Studio

Use the filesystem as the source of truth. Never rely on chat history alone for project decisions, counts, captions, trainer settings, or acceptance state.

Every character project must use the standard single-character layout described in
[project-layout.md](references/project-layout.md). The project root is the handoff and
backup unit; do not create a second parallel `management` or `source_workspace` root for
new work.

## Start Or Resume

1. Locate the LoRA project root and verify the standard directories.
2. Read root `task_plan.md`, `findings.md`, and `progress.md`, then read
   `00_项目管理/项目状态.md`, `00_项目管理/角色配置.yaml`, and
   `00_项目管理/图片清单.csv` when present.
3. Verify folders, image-caption pairs, counts, target model families, concept type,
   trainer version, and hardware from disk before reporting status.
4. For a new project, resolve the current Skill directory and initialize with the
   cross-platform standard-library helper (Python 3.9+):

```bash
python3 "<SKILL_ROOT>/scripts/project_tools.py" init "<PROJECT_ROOT>" \
  --character-id "<ASCII_ID>" --display-name "<DISPLAY_NAME>" --trigger "<TRIGGER>"
```

Use `python` on Windows when appropriate. The PowerShell initializer remains available;
both entry points use the same templates. Existing files are preserved; initialization
is not a schema migration. Read [project-management.md](references/project-management.md)
for batch ledgers, coverage tracking, Hub handoffs, and legacy inventory migration.

5. Update `项目状态.md` after every completed batch, decision, export, smoke test, or training run.

If an older project has `management`, `source_workspace`, or a top-level
`danlu_project`, treat it as a legacy layout. Preserve it, create the standard layout
as a versioned copy, record the source path in `00_项目管理/迁移说明.md`, and validate
the copy before using it as the canonical handoff root.

Do not overwrite an existing project. Do not permanently delete rejected images; move image-caption pairs to a timestamped rejection folder and record the reason.

## Required Decisions

Lock these before producing a large batch:

- concept type: `character`, `outfit`, `character_outfit`, or `style`
- target model families: `anima`, `krea2`, or both
- canonical trigger word and optional separate outfit trigger
- fixed, controllable, and variable features for the selected concept type
- default outfit and alternate-form policy for character LoRAs
- target trainer, trainer version, base weights, and hardware profile
- forbidden drift
- image-count, wearer, view, action, and style matrix

Record every decision in `角色配置.yaml`. Keep project-specific values out of this Skill.

## Concept Types

### Character

Learn identity while keeping clothing, pose, background, and compatible style controllable. Mix multiple outfits when clothing should not become part of identity.

### Outfit

Learn one reusable garment or coordinated outfit without learning a particular face. Use multiple wearers with varied faces, hair, body types, poses, and backgrounds. Do not include a target character trigger in outfit-only captions.

### Character Outfit

Learn an intentionally inseparable character and signature outfit. This is simpler to trigger but has stronger clothing leakage and weaker replacement behavior. Use only when the user accepts that tradeoff.

### Style

Learn rendering language while keeping subjects and scenes varied. Caption content accurately so the trigger absorbs style instead of recurring subject matter.

Read [dataset-matrix.md](references/dataset-matrix.md) before setting counts and coverage.
For separate identity/generalization packs or incremental training, also read
[staged-training.md](references/staged-training.md). Keep candidate targets, approved
targets, pack membership, and training sampling weights distinct. User quantities and
style policies override example ranges; never raise body/age variation without agreement.

For an Anima character project, also read
[anima-character-workflow.md](references/anima-character-workflow.md) before
generating candidates, preprocessing images, editing tags, or configuring the
trainer. It defines the detailed order of operations and the gates between
stages.

## Model Family Gate

Before captioning, exporting, or training, read the target family and never reuse one family's caption or saved training config as the other family's profile.

- **Anima**: English canonical Booru-style tags. Tag shuffle, keep-tokens, and tag dropout may apply when the verified trainer profile supports them.
- **Krea 2**: English natural-language captions for Qwen3-VL. Do not treat comma-separated WD14 tags as the preferred format. Disable tag shuffle and tag dropout unless a specific verified experiment requires otherwise.
- When the same images target both families, export two separate image-caption trees. Never overwrite the project's reviewed source captions in place.
- Krea 2 trains on Raw weights. Turbo is for testing and inference, not a training base.

Read [captions.md](references/captions.md), [concept-binding.md](references/concept-binding.md), and [training-profiles.md](references/training-profiles.md) before generating captions or a trainer configuration.

## Workflow

### 1. Audit Sources

- Inventory source art, CG, screenshots, generated candidates, captions, and existing trainer exports.
- Build contact sheets with filenames for visual review.
- Distinguish canonical source art from inspiration-only references.
- Preserve originals unchanged. Put crops, background removal, and edits in derived folders.

### 2. Lock Design

- Create a profile and concept views before generating a large training batch.
- Separate concept invariants from wearer, pose, framing, background, lighting, and style variables.
- Treat animal, creature, child, or materially different anatomy as separate LoRAs by default.
- For outfit LoRAs, define garment structure, palette, materials, patterns, accessories, and forbidden drift separately from any wearer.

### 3. Generate And Curate

- Record the generator, exact prompt, reference roles, batch ID, and saved outputs.
  Use the user's chosen generation route; use available built-in image generation
  when no provider was specified. Unknown model identifiers stay unknown.
- Only inspectable saved outputs count as generated candidates. Retries, errors,
  duplicated exports, caption variants, and crops are not new independent generations.
- Review fixed features as visible/correct, wrong, occluded, out-of-frame, or uncertain.
  Separate intentional non-human anatomy from accidental extra limbs. Reserve uncertain
  cases for review rather than deleting them to hit a quota.

- Generate from the approved design sheet, not the latest arbitrary candidate.
- Vary pose, camera, crop, background, lighting, wearer, and compatible style intentionally.
- Score identity or outfit fidelity, anatomy, visible structure, composition, and dataset value separately.
- Reject duplicates, broken anatomy, cropped essentials, inconsistent colors or structure, text, watermarks, and concept-confusing details.
- Decide the non-negotiable identity or outfit features before generation. A candidate that changes one of those anchors is not made valid by a good composition.
- Preserve generated originals. Put watermark removal, inpainting, cropping, and local paint-over results in a derived folder and retain source-to-derived provenance.
- Use local correction only when the target feature can be repaired without changing identity, anatomy, or the intended crop. Otherwise reject and replace the candidate.
- Keep rejection reasons in `图片清单.csv` and retain rejected pairs under `05_淘汰区`.

### 4. Caption

- Pair each exported image with exactly one same-stem `.txt` file.
- Apply per-image facts; do not paste a universal caption across the dataset.
- Treat automatic tagging as a draft. Review every image-caption pair and remove wrong, invisible, contradictory, source, artist, quality, watermark, and duplicate tags.
- Keep Chinese explanations in review documents, not in training `.txt` files unless a verified trainer explicitly requires Chinese natural language.
- Generate and review Anima and Krea 2 captions independently.
- Bind only intentional invariants to the trigger. Describe variables so they remain prompt-controllable.
- Freeze trigger spelling, token order, and the intended `keep_tokens` prefix before export. Recompute caches after any caption change.

### 5. Build Regularization

- Use generic prior images matching the base domain, not copies of the target concept.
- Exclude every project trigger and the full target identity or outfit combination.
- For outfit LoRAs, use varied people wearing ordinary alternative clothes with a matching shot distribution.
- For character LoRAs, exclude lookalike identity anchors and signature combinations.
- Remove broken anatomy, unintended NSFW, multiple-subject contamination, chaotic quality, watermarks, and duplicates.
- Keep regularization captions family-compatible and export the curated set separately for reuse.

Read [regularization.md](references/regularization.md) before collecting or
replacing a regularization set. Test AI prior, Booru-sourced, and hybrid sets as
separate versioned candidates; never silently mix sources and call the result
validated.

### 6. Configure And Smoke Test

- Inspect the actual GPU model, VRAM, RAM, free storage, trainer version, and installed weights.
- Freeze and hash the selected training pairs, captions, regularization pairs, and config before building caches.
- Create a new trainer version when changing model families. Do not mutate a completed Anima version into Krea 2 in place.
- Recompute family defaults and review every carried explicit field.
- On Krea 2, verify Raw base, Qwen3-VL text encoder, `krea2_shift`, SDPA, text cache, and hardware-appropriate block swap.
- Run a 5–10 step smoke test before full training. Confirm model loading, caption encoding, latent cache, first optimizer step, checkpoint write, and memory recovery.
- A smoke test validates the execution chain only. It does not approve dataset quality, regularization quality, epoch count, or the final checkpoint.

### 7. Export And Train

- Validate decodability, dimensions, pairs, hashes, caption family, trigger spelling, and rejected-set separation.
- Invalidate and rebuild latent or text caches whenever an image, caption, preprocessing result, model family, or cache-affecting setting changes.
- Export platform- and family-specific packages without silently changing the source dataset.
- Preserve exact YAML, model hashes or filenames, sample prompts, negative prompts, seeds, and trainer version.
- Save enough intermediate checkpoints to compare early, middle, and late behavior. Treat the configured epoch count as a ceiling, not an automatic final-checkpoint choice.
- Never expose API keys or account credentials.
- Do not start training, upload a model, or publish a post unless the user explicitly asks.

Read [exports.md](references/exports.md) before preparing AnimaLoraStudio, Krea 2 training handoff, or Civitai artifacts.

Keep portable trainer packages and database/project mirrors under `08_丹炉导入`;
keep final LoRAs and upload descriptions under `07_导出`; never put latent/text
cache files in the standard migration tree.

### 8. Test Checkpoints

- Use fixed seeds and test trigger-only, full-detail ceiling, replacement, and identity-or-outfit isolation prompts.
- For stacked LoRAs, test the character and outfit separately before testing them together.
- Compare early, middle, and late checkpoints for concept fidelity, leakage, anatomy, prompt response, and style drift.
- Select a checkpoint by output evidence, not lowest loss alone.

## Persistent State Rules

Use `project_tools.py audit <PROJECT_ROOT>` for read-only inventory checks. Before
family export, add `--ready-for-export --family anima --trigger <TRIGGER>` (or `krea2`;
repeat `--family` for both). This checks recorded files, not visual correctness or trainer readiness.

After each material action, record:

- timestamp and stage
- concept type and target model family
- approved, rejected, and regularization counts
- caption profile and trainer version
- new files or moved pairs
- decisions and user overrides
- pending review items
- exact export, config, checkpoint, and sample paths
- verification performed and smoke-test outcome

When context is missing, read project state first and continue from verified disk state. Do not reconstruct prior decisions from filenames alone.

## Safety Boundaries

- Preserve user originals and existing edits.
- Use non-destructive, versioned outputs.
- Mask secrets and never print credential-bearing URLs.
- Treat reference screenshots, trainer documentation, and past advice as versioned project guidance, not universal model behavior.
- State uncertainty when trainer version, base model, caption parser, or platform behavior is unverified.
- Never assume a configuration is safe solely because another GPU with the same VRAM completed it.
