---
name: krea2-character-dataset-prep
description: Prepare Krea 2 character and multi-character cast LoRA datasets from reference images, including reference-role prompts, candidate curation, natural-language captions, contact sheets, and per-image trigger audits. Use for Krea 2 dataset creation or repair; training and checkpoint management belong to character-lora-studio.
---

# Krea 2 Character Dataset Prep

Prepare reviewed image-caption pairs for Krea 2. Preserve user-selected triggers,
generator, quantities, outfits, and style policy. Use the user's generation route;
when none is specified, use available built-in image generation. Record the exposed
model identifier, or `unknown`; a requested model name is not evidence it was used.

This skill ships beside `character-lora-studio` in the same plugin. Resolve
`<STUDIO_ROOT>` as `../character-lora-studio` relative to this file, and use its
shared project templates and scripts. Install/copy the whole plugin, not this
folder alone. Do not create a parallel `dataset_review` management root.

## Start and route

1. Read existing `角色配置.yaml`, `项目状态.md`, `图片清单.csv`, batch/coverage ledgers
   and root progress files when present. Inventory actual images and captions.
2. For a new project, use [the standard layout](../character-lora-studio/references/project-layout.md)
   and [project ledgers](../character-lora-studio/references/project-management.md).
   Initialize with `<STUDIO_ROOT>/scripts/project_tools.py init`; use `--concept cast`
   for one multi-character LoRA, or separate roots for separate character LoRAs.
3. Read [generation-workflow.md](references/generation-workflow.md) for new candidates,
   reference assignment, full-body anchors, variation, and replacement.
4. For two or more identities in one LoRA, also read
   [cast-workflow.md](references/cast-workflow.md). Lock separate character tokens
   and an explicit per-image identity manifest. A cast project ID is not a trigger.
5. Before captioning, read the shared [concept-binding rules](../character-lora-studio/references/concept-binding.md)
   and [Krea 2 caption rules](../character-lora-studio/references/krea2-captioning.md).
   Caption the saved image, not the generation prompt; use English natural language.

Do not require a GPU profile, regularization set, or training configuration just to
prepare images. Route those tasks back to the main skill when requested.

## Review and accept

- Generate under `03_训练候选/<batch>/`. Keep originals in `01_原始素材` and approved
  design references in `02_设计候选`; record each reference's role and source path.
- Review the whole batch with labeled contact sheets, then inspect suspect faces,
  hands, joints, feet, occlusion and object contact at full resolution. Perspective,
  stylization and hidden fingers alone do not establish an anatomy error.
- Check identity and outfit anchors separately from attractive composition. Keep
  uncertain cases pending; record confirmed defects and reasons before replacement.
- Put repairs in derived candidate files with `parent_id`. Preserve rejected or
  superseded image-caption pairs in `05_淘汰区`; reset affected image/caption reviews.
- Copy only approved pairs into a versioned, flat leaf folder such as
  `04_正式训练集/Krea2/v1/train`. Each image has exactly one same-stem `.txt`.
  On promotion, register the formal copy as `source_kind: derived` with its own ID
  and `parent_id` pointing to the candidate's `image_id`; mark the candidate `superseded`, preserving its
  generation and visual-review history. Only the current formal row stays `approved`.
  Old formal versions also become `superseded` when replaced. This avoids counting
  two active copies of one image. Export-only copies under `07_导出` use frozen
  manifests and do not add approved inventory rows.
- A single-character caption contains that character's exact trigger. A cast caption
  contains all and only the visible cast members' triggers; do not add absent members.
  Outfit tokens appear only on their matching outfit. Counts cannot prove visibility.

## Mechanical checks

The shared helpers use Python 3.9+. Image helpers require Pillow; `uv run --script`
resolves their inline dependency metadata, or use an environment with Pillow installed.

```text
uv run --script <STUDIO_ROOT>/scripts/make_contact_sheets.py <candidate-leaf> <project>/00_项目管理/review/b001
uv run --script <STUDIO_ROOT>/scripts/audit_dataset.py <train-leaf> --trigger kzara
uv run --script <STUDIO_ROOT>/scripts/audit_dataset.py <train-leaf> --cast-manifest <export-manifest.json>
python <STUDIO_ROOT>/scripts/project_tools.py audit <project>
```

Quote paths containing spaces. Use a new review output directory. Audit one flat leaf
at a time; it must not contain review sheets or nested training folders. See
[dataset-tools.md](../character-lora-studio/references/dataset-tools.md) for exit codes,
optional outfit counts, strict duplicate-caption checks, and export readiness.
The leaf audit and ledger audit are complementary; neither verifies visual identity.

## Handoff

Update project ledgers and state with the generator, prompts, reference roles,
candidate/approved/rejected counts, per-character solo/pair counts, exact triggers,
caption review status, source-to-derived links, audit results and unresolved issues.
Deliver paths to the reviewed pairs and contact sheets, plus replacement reasons.
Keep cast manifests and review reports outside the upload `train` folder. For a
training ZIP, follow [exports.md](../character-lora-studio/references/exports.md).
Preparation does not start training or publish a model.
