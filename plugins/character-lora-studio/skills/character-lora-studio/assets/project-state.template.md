# {{DISPLAY_NAME}} LoRA 项目状态

- 角色 ID：`{{CHARACTER_ID}}`
- 触发词：`{{TRIGGER}}`
- LoRA 类型：`character`（待确认）
- 项目根目录：`{{ROOT}}`
- 最后更新：`{{TIMESTAMP}}`
- 当前阶段：人设锁定
- 目标模型族：待确认（Anima / Krea 2）

## 当前数量

| 分类 | 图片 | Caption |
|---|---:|---:|
| 原始素材 | 0 | 0 |
| 设计候选 | 0 | 0 |
| 训练候选 | 0 | 0 |
| 正式训练集 | 0 | 0 |
| 淘汰区 | 0 | 0 |
| 正则集 | 0 | 0 |

## 已确认决策

- 触发词：`{{TRIGGER}}`
- 概念类型：待确认（character / outfit / character_outfit / style）
- 目标模型族：待确认
- 固定身份：待填写
- 可控身份标签：待填写
- 默认服装：待填写
- alternate form：待填写
- 禁止偏移：待填写
- Anima caption profile：待确认
- Krea 2 caption profile：待确认
- 训练硬件与显存档位：待确认

## 待处理

- [ ] 完成人设与设计图
- [ ] 确认 LoRA 类型和目标模型族
- [ ] 确认服装和镜头矩阵
- [ ] 建立候选图清单
- [ ] 筛选并记录淘汰原因
- [ ] 分模型族完成 caption 与中文审查
- [ ] 完成正则集
- [ ] 生成并审查训练配置
- [ ] 完成 5–10 step 烟雾测试
- [ ] 分模型族导出并验证
- [ ] 训练与 checkpoint 对比

## 最近操作

- `{{TIMESTAMP}}`：初始化项目。

## 验证记录

- 尚未验证。

## 分包、批次与训练阶段

- 候选图下限 / 合格图目标：未决定；见 `角色配置.yaml`。
- 分包进度：从 `图片清单.csv` 按 pack / status 汇总；不要手工凑数。
- 已完成生成数：按实际保存的 generated 候选图 hash 去重；修图和双模型导出不重复计数。
- 双标注状态：Anima / Krea 2 分别统计 pending、draft、reviewed。
- 下一批补什么：从 `覆盖矩阵.csv` 与已通过图片的 coverage_cell_id 对照。
- 训练谱系：见 `训练记录.csv`，每个模型族独立记录阶段与父 checkpoint。
- 初审来源与 Hub 二审：分别记录图片 / Anima / Krea 2；插件、Hub 均可筛选与打标。
- Hub 同步时间 / 冲突：尚未同步；人工修改冲突需复核，不按修改时间静默覆盖。
- 冻结版本与审计报告：尚未生成。
