# Krea 2 多角色 Cast

## 选择项目结构

需要独立复用角色时，优先每个角色一个 LoRA、一个标准项目根；组合推理仍需测试串扰。
用户要一个包含多位角色的文件时使用 `concept.type: cast`，一个 Cast 项目根管理全部角色。
不自动把已存在的独立角色项目合并或迁移。Cast 是这份 Krea 2 流程的概念类型，
不代表其他模型族已验证多人训练效果。

```text
python <STUDIO_ROOT>/scripts/project_tools.py init <cast-project> --character-id cast_ab --display-name "双角色" --concept cast
```

Cast 项目根配置的 `trigger` 留空；项目 ID 不能作为所有图片的共同身份词。
初始化后将 `caption_profiles.krea2.enabled` 设为 `true`，记录 Krea 2 为目标模型族，
保持 Anima profile 关闭；初始化只创建模板，不代表配置和数据已经审核完成。
在配置中填写 `cast.characters`，每个成员保存 id、trigger、class_noun、参考图和
fixed/controllable/variable/forbidden_drift。`trigger_confirmed` 表示这些成员词已确认。
为独立角色保留原有词，禁止擅自改拼写或把类别词重复拼进去。

```yaml
concept:
  type: cast
trigger: ""
cast:
  characters:
    - id: a
      trigger: kzara
      class_noun: woman
      references: ["01_原始素材/a.png"]
      fixed: ["已确认的角色 A 身份锚点"]
    - id: b
      trigger: mivon
      class_noun: man
      references: ["01_原始素材/b.png"]
      fixed: ["已确认的角色 B 身份锚点"]
  important_pairs: [[a, b]]
  fixed_duo: false
  project_manifest: "00_项目管理/cast-project-v1.json"
```

## 数量是实验参数

下表来自资料包的经验配方，未作为官方比例或硬门禁。用户计划优先，先做小规模验证。

| 用途 | 每人单人图 | 重要组合配对图 |
|---|---:|---:|
| 两个可独立使用的身份 | 18–30 | 8–15 |
| 主要作为固定搭档 | 12–20 | 20–30 |
| 三角色阵容 | 18–25 | 每个重要配对 6–10 |

双角色示例：24 A 单人 + 24 B 单人 + 12 配对 = 60 张，配对占 20%。
独立控制场景可把 15%–25% 作为首轮配对占比参考。三人以上按总量重新计算，
不要把“每对加十张”与上述比例同时机械执行。只生成需要学习的关系。
较多身份可以拆成独立项目或少数重要组合；数量增长本身不能解决身份串扰。

批次与覆盖矩阵用 `solo_a`、`solo_b`、`pair_ab` 等项目自定 pack 区分。
每张图只计一次物理总量，另统计每个角色出现次数和每个组合数量。
两人左右位置都要覆盖，交互与非交互、不同距离、衣服和背景交叉变化。
大多数配对图应能辨认两张脸，少量轻遮挡用于泛化；不能把错误身份当成遮挡。

## 参考与 caption 映射

生成提示词逐个分配，例如“Image 1 决定 A 的脸，Image 2 决定 B 的脸；
Image 3 只决定背景；A 位于画面左侧，B 位于右侧”。下一批交换空间位置，
但不交换参考归属。左右均指画面方向，人体自身左右另作说明。

```text
kzara, a woman, sits beside a cafe window wearing a green jacket in soft daylight.

kzara, a woman, stands on the left holding a map. mivon, a man, stands on the
right pointing toward a station. Both are shown from the waist up in daylight.

mivon, a man, sits on the left while kzara, a woman, stands on the right beside
a wooden bench. Evening light falls across the courtyard.
```

只写当前图中出现的身份；每个可见角色都需要 token 与自身动作、服装、位置对应。
不用含糊的“他们”代替映射。稳定身份锚点按绑定策略处理，变量逐图描述。
不默认添加一个通用 duo token。固定搭档确需额外 token 时在项目配置记录，
只在配对图使用并人工检查；目前自动 manifest 检查覆盖成员词，不核验 duo 条件。

## 双层 manifest 与审计

人工按图确认出场名单，保存 JSON，不能仅根据 caption 自动推断再拿它自证。
`characters` 的值是精确 token（或用户明确指定的完整短语），不是全部外貌提示词。
`images` 的键相对于本次审计的根目录，值是可见成员 ID 的非空列表。

项目审计清单的键使用 `图片清单.csv` 中已批准训练行的 `file` 路径：

```json
{
  "characters": {"a": "kzara", "b": "mivon"},
  "images": {
    "03_训练候选/b001/a.png": ["a"],
    "03_训练候选/b001/b.png": ["b"],
    "03_训练候选/b002/pair.png": ["a", "b"]
  }
}
```

正式导出的平铺 `train` 文件夹另建版本化 export manifest，成员不变、键映射为
`a.png`、`b.png`、`pair.png` 等实际导出文件名。两者必须与同一冻结清单一致，
不能把项目路径 manifest 直接传给平铺审计器。

```text
python <STUDIO_ROOT>/scripts/project_tools.py audit <project> --ready-for-export --family krea2 --cast-manifest <project-manifest.json>
uv run --script <STUDIO_ROOT>/scripts/audit_dataset.py <train-leaf> --cast-manifest <export-manifest.json>
```

检查包含所需成员词、排除缺席成员词，检测漏图、过期路径和未知 ID。
不要对 Cast 使用 `--trigger A --trigger B`：该参数语义是每张都需要所有给定词。
审计通过只能证明文件和文字与清单一致，不能证明画中人真实身份正确。

## 训练后测试交接

记录固定 prompt、seed 和推理参数，交给主 Skill 做：A 单人、B 单人、A+B、
左右互换、各角色特写/全身、未训练服装和无触发词。与早中晚 checkpoint 对比，
检查身份串扰、位置绑定、服装泄漏和未请求角色出现。
普通 LoRA 全局作用；多份叠加或 Cast 都不保证空间隔离。仍有串扰时可测试降低强度、
区域/遮罩或边界框工作流，不宣称单凭 caption 就解决。

经验来源：归档资料包 `KREA2_MULTI_CHARACTER_LORA_RESEARCH.md`（2026-09-16）。
其官方入口包括 [Krea training](https://www.krea.ai/blog/krea-2-lora-training) 和
[Krea 2 Raw model card](https://huggingface.co/krea/Krea-2-Raw)。本模块未把社区配比当成当前官方规定。
