# 数据集审计与联系表工具

所有路径从当前安装的 Skill 解析，示例 `<STUDIO_ROOT>` 是 `character-lora-studio` 目录。
Python 3.9+；`project_tools.py` 只用标准库。两个图像工具需要 Pillow，可用
`uv run --script` 自动解析内联依赖，或直接在已安装 Pillow 的 Python 环境运行。

## 文件审计与账本审计

`audit_dataset.py` 检查一层实际图片-caption 文件，不修改输入：

```text
uv run --script <STUDIO_ROOT>/scripts/audit_dataset.py <train-leaf> --trigger kzara
uv run --script <STUDIO_ROOT>/scripts/audit_dataset.py <train-leaf> --trigger kzara --outfit-token kzaradress --expected-per-outfit 12
uv run --script <STUDIO_ROOT>/scripts/audit_dataset.py <train-leaf> --cast-manifest <export-manifest.json>
```

- 图片/标注缺对、空文件、损坏图片、同 stem 多种扩展名、空数据集、重复图片、
  不满足指定最小尺寸、错误身份词或 manifest 映射使审计失败。
- 默认最小宽高各 512，可用 `--min-width` / `--min-height` 明确调整。它是本地
  检查阈值，不是 Krea 官方分辨率要求。不能靠放大低质图规避质量审查。
- 相同 caption 默认警告，可用 `--strict` 将警告作为失败；简短的相同可见事实
  有时合理，所以不自动改写文字来消除重复。
- `--outfit-token` 可重复，数量包括零次命中。`--expected-per-outfit` 只在用户
  确定等量目标时使用；无指定衣服时不默认寻找任何项目专有词。
- `--outfit-regex` 为显式兼容选项，不能取代有明确目标清单的零计数检查。
- `--trigger` 可重复，表示每张 caption 都必须包含所有指定词。Cast 使用
  `--cast-manifest`，按出场成员检查，不能给所有单人图强加全部角色词。
- 标准输出为 JSON；需要保存时使用 `--json-output <新的管理报告路径>`。报告放在
  `00_项目管理`，不覆盖已有报告、图片、caption 或 manifest。
- 退出码：0 机械检查通过（仍需阅读 warnings）；1 数据检查失败；2 参数、
  manifest 或依赖错误。缺少 Pillow 不能当成“跳过图片检查后通过”。

只传入平铺叶子目录，如 `04_正式训练集/Krea2/v1/train`；子目录数据应分别审计。
近重复、人体、身份、服装可见性和左右映射仍需视觉审核。

`project_tools.py audit` 检查清单、路径、来源、哈希和 caption 审核状态，
不替代图片解码或尺寸检查。导出前两种审计都应运行：

```text
python <STUDIO_ROOT>/scripts/project_tools.py audit <project> --ready-for-export --family krea2 --trigger kzara
python <STUDIO_ROOT>/scripts/project_tools.py audit <project> --ready-for-export --family krea2 --cast-manifest <project-manifest.json>
```

Cast 项目/导出 manifest 的根路径不同，参见
[cast-workflow.md](../../krea2-character-dataset-prep/references/cast-workflow.md)。

## 联系表

```text
uv run --script <STUDIO_ROOT>/scripts/make_contact_sheets.py <candidate-leaf> <project>/00_项目管理/review/b001 --per-sheet 15 --columns 5
```

每页带文件名，按自然文件名排序，处理 EXIF 方向和透明背景。中文字体可自动寻找，
或用 `--font <字体文件>` 指定。`--thumb-width` / `--thumb-height` 控制缩略图区，
`--format png` 可替换默认 JPG。长名字以工具输出的标签布局为准，逐图判断仍打开原图。
输出使用候选目录之外的新建或空文件夹；拒绝覆盖旧联系表。发现坏图先报告错误，
不能用一张漏图联系表声称整批审查完成。
