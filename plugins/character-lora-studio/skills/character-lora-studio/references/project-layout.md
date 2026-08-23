# Standard single-character project layout

Use one project root per character, outfit, combined character-outfit, or style LoRA.
That root is the unit copied to another device and the unit referenced by project indexes.

```text
角色项目/
├─ 00_项目管理/
├─ 01_原始素材/
├─ 02_设计候选/
├─ 03_训练候选/
├─ 04_正式训练集/
├─ 05_淘汰区/
├─ 06_正则集/
├─ 07_导出/
├─ 08_测试样图/
├─ 08_丹炉导入/
├─ 09_训练产物/
├─ outputs/
├─ findings.md
├─ progress.md
└─ task_plan.md
```

## Directory responsibilities

- `00_项目管理`: `项目状态.md`, `角色配置.yaml`, `图片清单.csv`, decision records,
  review contact sheets, hashes, and migration notes.
- `01_原始素材`: canonical references and source art. Do not overwrite.
- `02_设计候选`: identity sheets and design alternatives.
- `03_训练候选`: generated, cropped, inpainted, or otherwise derived candidates with
  provenance.
- `04_正式训练集`: approved train image-caption pairs, separated by model family/version.
- `05_淘汰区`: rejected image-caption pairs and the reason for rejection. Do not permanently
  delete rejected material.
- `06_正则集`: approved regularization image-caption pairs, separated by source/version.
- `07_导出`: platform/family-specific packages, configs, final LoRAs, and upload text.
- `08_测试样图`: fixed-seed checkpoint comparisons and user-facing samples.
- `08_丹炉导入`: AnimaLoraStudio project/version mirrors, portable import packages, and
  handoff notes. Do not place base models or secrets here.
- `09_训练产物`: smoke-test outputs, intermediate checkpoints, logs, and training metadata.
- `outputs`: optional trainer output scratch area; keep it project-local and exclude caches
  from migration packages.
- Root planning files: durable task plan, findings, and progress for context recovery.

## Legacy migration

Older projects may contain `management`, `source_workspace`, or `danlu_project` at the
project root. Do not delete or rename them automatically. Copy their reviewed contents into
the standard layout, record canonical and legacy paths, and validate image-caption pairing,
counts, hashes, and cache exclusion before switching the index to the standard root.

## Naming and portability

Use stable ASCII project IDs for paths and triggers where possible. Keep display names and
Chinese explanations in management documents. Training captions remain family-compatible:
Anima uses English Booru-style tags; Krea 2 uses English natural-language captions.
Portable packages must replace device-specific absolute model paths with explicit placeholders.
