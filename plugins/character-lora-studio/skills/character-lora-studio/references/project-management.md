# Project ledgers and recovery

Use this when a project spans generation batches, multiple packs, two caption families,
Hub review, or more than one training run. All paths in CSV ledgers are relative to the
project root with `/` separators. External reference/model paths belong in config or
handoff notes, not in the portable inventory.

## Sources of truth

| File | Owns |
|---|---|
| `角色配置.yaml` | Confirmed identity boundaries, trigger status, target counts, packs, generator, family order |
| `图片清单.csv` | One row per physical source/derived image; stable ID, path, hash, pack, provenance, decision and two caption states |
| `生成批次.csv` | Batch intent, provider/model, planned count, prompts/references, execution status |
| `覆盖矩阵.csv` | Planned cells across outfit, veil/form, shot, view, pose, style and background |
| `训练记录.csv` | Family, stage, frozen manifests/config, parent run/checkpoint and resume mode |
| `项目状态.md` | Dated human-readable summary of verified ledgers, next action and unresolved decisions |

Counts in a summary never override files. A generated batch is not complete just
because its API call returned success. Register actual saved, inspected outputs.
Use a stable ASCII `image_id`; it is not the current row number. Filenames need not
be changed. A derived crop or repair has its own ID and a `parent_id`; preserve the
original, and mark superseded versions so they do not silently remain approved.

For a Krea 2 Cast, record member identities/triggers in `角色配置.yaml` and a versioned
membership manifest under management. Each manifest path matches an approved training
row's `file`, with a list of visible member IDs. Use `solo_a`, `solo_b`, `pair_ab` or
other project-defined packs without changing the CSV schema. Root `trigger` stays empty.
Run readiness audit with `--cast-manifest` instead of `--trigger`; regenerate the
export-relative manifest from the same frozen rows. See
[cast-workflow.md](../../krea2-character-dataset-prep/references/cast-workflow.md).

## Inventory fields

- `category`: `source`, `design`, `training_candidate`, `formal`, `rejected`,
  `regularization`, or `evaluation`.
- `status`: `candidate`, `needs_review`, `needs_repair`, `approved`, `rejected`,
  or `superseded`. A rejected row must have a reason. Approval is visual approval;
  export additionally requires the selected family's caption to be reviewed.
  `approved` also means the active training selection, not every historically approved
  copy. When copying an approved candidate into `04_正式训练集`, mark the original
  `superseded` (keep its review evidence and `source_kind: generated`), and register
  the formal copy with a new ID, `source_kind: derived`, `parent_id` pointing to the
  original, and `status: approved`. Both hashes remain recorded; generation totals
  count only the original. Keep only the current formal version approved. A superseded
  formal row must change `category` to `training_candidate` (its path may remain in
  the versioned archive); `formal` is reserved for the active approved selection.
  Alternatively, move the candidate to the formal path and update its existing row
  while preserving the generated original elsewhere with provenance. Do not create
  two approved rows or leave an unregistered copy under `03`/`04`/`05`.
  Final platform/family copies under `07_导出` are tracked by frozen export manifests,
  not additional approved physical-image rows in the working inventory.
- `source_kind`: `source`, `generated`, or `derived`. Only `generated` training
  rows count toward completed candidate generation. Preserve those rows after
  repair/rejection so the history remains countable.
- `pack`: a project-defined ID, required for training rows. Pack membership is
  separate from stage membership: stage B may replay A without copying inventory rows.
- `batch_id`, `prompt_file`, `reference_files`: provenance for generated candidates.
  Store the exact executed prompt in the project; reference paths can be separated by `;`.
  The batch records its generator and model; use `unknown` for an unexposed model ID.
- `sha256`: current file hash, not a guessed or inherited parent hash.
- `coverage_cell_id`: the primary planned cell filled by this image. Extra observations
  go in notes. Compare approved counts with targets; do not count one image multiple
  times to inflate a total. Near-duplicate groups are manually assigned for review.
- `anima_caption_status`, `krea2_caption_status`: `pending`, `draft`, `reviewed`,
  or `not_applicable`. Each family uses its own same-stem `.txt` path.
- `hub_record_id`: optional mapping to a verified Hub record, not an invented identifier.

Count candidate generations by unique file hash of saved `generated` training images.
Count approved training images separately. Caption variants, family exports, stage
replay, retries without outputs, crops and repairs do not increase generation totals.
Exact hash deduplication does not detect perceptual duplicates; review contact sheets.

## Batches and coverage

Record the batch before generation (`planned` → `running` → `completed`, `partial`,
or `failed`). Do not mark failed requests as images. Let the next batch address actual
coverage gaps or repeated defects. A user minimum/target is project configuration;
neither equal pack sizes nor an arbitrary rejection percentage is a universal rule.

For each candidate record observable reasons. Fixed traits may be correct, wrong,
occluded, outside the crop, or indeterminate. Perspective and stylized anatomy need
evidence-based review. For non-human characters, distinguish permanent appendages
from accidental extra human limbs. Never add age or body-shape variation by inference.

## Hub handoff

Both the plugin and Hub can perform visual curation and generate/review both caption
families. A normal route is plugin first-pass curation + dual captioning, followed by
Hub second review; Hub-first or plugin-only routes are also valid. The project
filesystem is the durable handoff unit. This plugin provides no automatic Hub API
sync implementation; agent review/caption capabilities do not imply an API connector.

1. Record the first-pass reviewer in `review_source` (`plugin`, `hub`, or `user`),
   and keep the first-pass artifact/snapshot. When using Hub, import a versioned batch,
   retain image IDs and hashes, and record verified Hub IDs.
2. Keep image, Anima and Krea 2 approval independent. Record optional second review
   in `hub_image_review_status`, `hub_anima_review_status`, `hub_krea2_review_status`:
   `not_requested`, `pending`, `approved`, or `changes_requested`. One Hub approval
   must not silently approve the other two dimensions. If the project requires Hub
   review, run export audit with `--require-hub-review`; plugin approval alone is then
   insufficient. Otherwise do not make Hub a mandatory gate.
3. Export reviewed captions/decisions and reconcile by image ID + hash.
4. If pixels changed, reset visual, both caption reviews and all affected Hub reviews. If only a caption changed,
   reset that family's review and affected export/cache versions.
5. Conflicting manual edits require explicit resolution; never silently choose newest.
6. Freeze approved file lists/hashes, two caption manifests and config together before
   training export. Rejected and evaluation images remain outside training manifests.

## Recovery and legacy projects

Read config, ledgers and the last audit before reporting progress. Initialization
creates missing files with exclusive writes, never overwrites existing files, and
never upgrades a populated CSV in place. For schema 2:

1. Preserve originals and make a dated migration copy.
2. Add stable IDs/provenance using actual files, retain old score columns and notes;
   unknown historical batches remain explicitly unknown rather than fabricated.
3. Verify file hashes, paths, counts and family caption status. Update a copied YAML
   to schema 3 only after the ledger migration is complete.
4. Review the migration and switch the canonical path; keep the old copy.

`project_tools.py audit` is read-only. `PASS` means only the listed mechanical checks
passed; it does not certify identity, image decodability, near-duplicate quality,
frozen manifests, the Hub database, or training results.
