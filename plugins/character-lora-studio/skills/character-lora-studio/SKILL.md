---
name: character-lora-studio
description: Build, resume, audit, tag, curate, regularize, test, and export character LoRA datasets with persistent on-disk state. Use when Codex is asked to design a character dataset, choose outfits or shot coverage, generate or score candidate images, apply teacher-style Booru captions, maintain approved/rejected/regularization sets, prepare AnimaLoraStudio or Krea2 packages, compare checkpoints, or continue a LoRA project after context loss.
---

# Character LoRA Workflow

Use the filesystem as the source of truth. Never rely on chat history alone for project decisions, counts, captions, or acceptance state.

## Start Or Resume

1. Locate the character project root.
2. Read `项目状态.md`, `角色配置.yaml`, and `图片清单.csv` when present.
3. Verify current folders and counts from disk before reporting status.
4. For a new project, run:

```powershell
& "$PSScriptRoot/scripts/init-character-lora-project.ps1" `
  -Root '<项目目录>' `
  -CharacterId '<ASCII_ID>' `
  -DisplayName '<角色名>' `
  -Trigger '<trigger>'
```

5. Update `项目状态.md` after every completed batch, decision, export, or training run.

Do not overwrite an existing project. Do not permanently delete rejected images; move image-caption pairs to a timestamped rejection folder and record the reason.

## Core Decisions

Lock these before producing a large batch:

- canonical trigger word
- human and alternate forms
- fixed identity anchors
- controllable identity tags
- default outfit and outfit weights
- target platforms and base models
- forbidden drift
- image-count and view matrix

Record every decision in `角色配置.yaml`. Keep character-specific values out of this Skill.

## Workflow

### 1. Audit Sources

- Inventory all source art, CG, screenshots, generated candidates, and captions.
- Build contact sheets with filenames for visual review.
- Distinguish canonical source art from inspiration-only references.
- Preserve originals unchanged. Put crops, background removal, and edits in derived folders.

### 2. Lock Design

- Create a character profile and concept views before generating training data.
- Separate fixed identity from clothing, pose, framing, background, and style.
- Treat alternate animal or creature forms as separate LoRAs by default. Mix forms only with an explicit form tag and enough examples for each anatomy.

Read [dataset-matrix.md](references/dataset-matrix.md) when planning outfits, views, styles, and counts.

### 3. Generate And Curate

- Generate from the approved design sheet, not from the latest arbitrary candidate.
- Vary pose, camera, crop, background, lighting, and clothing intentionally.
- Score identity, anatomy, hair/accessory consistency, composition, and dataset value separately.
- Reject duplicate poses, face drift, broken anatomy, cropped essentials, inconsistent colors, text, watermarks, and identity-confusing accessories.
- Keep rejection reasons in `图片清单.csv` and retain rejected pairs under `05_淘汰区`.

### 4. Caption

- Use English canonical Booru-style tags in training `.txt` files.
- Keep Chinese explanations in review documents, never mixed into training captions unless the trainer explicitly requires natural-language captions.
- Pair each image with exactly one same-stem `.txt` file.
- Apply per-image facts; do not paste a universal caption over the dataset.

Read [teacher-method.md](references/teacher-method.md) for the decision model and [captions.md](references/captions.md) for tag ordering, cleanup, and checks.

### 5. Build Regularization

- Use generic prior images matching the base domain, not copies of the target identity.
- Exclude the trigger and character-specific hair, ornament, clothing, or form tags.
- Remove bad anatomy, NSFW unless explicitly intended, multiple subjects, non-human contamination, chaotic line/color quality, watermarks, and duplicates.
- Keep regularization captions paired and export the curated set separately for reuse.

### 6. Export And Train

- Validate pairs, counts, duplicate hashes, dimensions, captions, and rejected-set separation.
- Export platform-specific packages without silently changing the source dataset.
- Never expose API keys or account credentials.
- Do not start training, upload a model, or publish a post unless the user explicitly asks.

Read [exports.md](references/exports.md) before preparing AnimaLoraStudio, Krea2, or Civitai artifacts.

### 7. Test Checkpoints

- Use fixed seeds and at least three prompt classes: default outfit restoration, clothing replacement, and identity-only stress test.
- Compare multiple epochs/steps for face, hair, fixed accessories, clothing leakage, anatomy, and prompt responsiveness.
- Keep sample prompts and negatives with the training record.
- Select a checkpoint by output evidence, not lowest loss alone.

## Persistent State Rules

After each material action, record:

- timestamp and stage
- approved/rejected/regularization counts
- new files or moved pairs
- decisions and user overrides
- pending review items
- exact export or training artifact paths
- verification performed

When context is missing, read project state first and continue from verified disk state. Do not reconstruct prior decisions from filenames alone.

## Safety Boundaries

- Preserve user originals and existing edits.
- Use non-destructive, versioned outputs.
- Mask secrets and never print credential-bearing URLs.
- Treat teacher screenshots and past advice as project guidance, not universal model behavior.
- State uncertainty when trainer, base model, caption parser, or platform behavior is unverified.
