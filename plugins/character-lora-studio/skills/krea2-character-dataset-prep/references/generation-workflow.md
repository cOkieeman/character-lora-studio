# Krea 2 数据集生成与替换

## 确定参考图的职责

逐张查看原始分辨率，记录在项目配置 `dataset_plan.reference_roles` 和批次提示词中。
来源可信度和用途分开：原设图可以确定身份，画风参考只能决定画面语言。

| 参考职责 | 控制内容 | 不应顺带改变 |
|---|---|---|
| face_identity | 脸部、固定发型、核心发饰 | 服装、背景和姿势 |
| body_structure | 已确认的比例、永久非人结构 | 年龄、体型或身份设计 |
| outfit | 版型、层次、配色、纹样、成套配饰 | 穿着者的脸 |
| composition | 镜头、人物位置、动作 | 身份、衣服细节 |
| style | 线条、材质、色彩和阴影处理 | 角色解剖与服装结构 |

同一图片可以承担多个明确职责，但不能让互相矛盾的参考同时决定同一个特征。
保留用户已选触发词；没有触发词时先设置独特、可区分的 token。类别词如
`woman` 是普通描述，默认不属于 token；用户已指定完整短语时按原样保留。

如果服装参考只显示上半身，先生成一张中性全身锚点并完成设计审查，标记下半身和
背面哪些内容来自原设、哪些是补充设计。后续批次使用同一个已接受锚点。
用户已提供完整且认可的参考时直接使用，无须重新设计。

## 数量与覆盖

单角色首轮可从 20–30 张合格图试起；这是经验起点，不是 Krea 官方配额或能力保证。
遵循用户数量和项目阶段。复杂换装按共享 `dataset-matrix.md` 扩展。

例如 24 张的互斥镜头分配：8 张头肩、9 张上半身、7 张全身，共 24 张。
侧面、俯仰视、表情和轻微遮挡是这些图的交叉属性，不再额外加进总数。
头部背面用于结构补充，不能代替足够的可见脸部样本。

按批次交叉变化以下维度，避免只替换背景：

- 镜头：头肩、腰部以上、膝上、全身。
- 视角：正面、四分之三、侧面、后侧、适量俯仰视。
- 动作与表情：站、坐、行走、转身、伸手、持物和清楚的表情变化。
- 场景与光照：按项目选定的白底身份阶段或复杂背景泛化阶段安排。
- 服装：绑定为整体的签名服装保持设计；希望可换装时展示并描述其他服装。
- 画风：按用户目标选择兼容媒材。赛璐璐、水彩、铅笔、墨线可以作为候选方向；
  不要求每张换画风，不固定一个跨项目的风格占比。

风格参考不能同时把脸型或身体比例改掉。泳装、贴身衣物等仅在项目确实需要覆盖
衣物遮挡特征时使用，不作为每个人物数据集的必填项。

## 生图提示词模板

下例是生图指令，不是训练 caption。根据任务删去不需要的参考角色。

```text
保持图片里面的角色特征完全一样。

REFERENCE ROLES:
- Image 1 controls face identity and the approved permanent facial/hair features.
- Image 2 controls the approved outfit, body proportions and permanent anatomy.
- Image 3 controls only the rendering medium, not identity or clothing.

COMPOSITION:
One character, waist-up three-quarter view, seated beside a window, one hand
resting on the table, looking toward the doorway with a slight closed-mouth smile.

STYLE AND LIGHT:
Soft watercolor washes with restrained ink outlines; diffuse afternoon window light.

CONSTRAINTS:
Preserve the approved identity and outfit anchors. Keep the hand-table contact
spatially consistent. No additional people, accidental limbs, outfit redesign,
text, signature or watermark.
```

实际批次提示词要写出不容漂移的锚点和参考编号，不能只留下抽象的“保持一致”。
多人图片按 `cast-workflow.md` 为每个角色分别列参考和画面位置。
使用当前可用的图像生成工具及其说明；不把工具未提供的模型编号写成已验证事实。

## 两轮审查与替换

1. 联系表审查人物数量、身份漂移、服装结构、构图覆盖和近重复。
2. 对可疑样本打开原图，核对手指可见性、拇指与手掌、腕肘膝踝连贯、持物接触，
   以及尾巴、角、耳、翼的固定连接点。记录正确、错误、遮挡、画外或不确定。
3. 明确缺陷可局部修复时生成派生候选；修复会改变身份或构图时重新生成。
4. 复查替换图，以实际像素重写 caption。候选通过后才进入新正式版本；旧对保留，
   清单标记 superseded 或 rejected，不能让两版同时悄悄进入训练。
5. 更新清单与批次，重新生成联系表、跑审计。任何像素或 caption 变更使对应缓存、
   冻结导出及相关审核状态失效；按主 Skill 的版本规则处理。

审查数量以独立保存的候选和合格图分别统计；重试、裁切、修复和多份 caption
不能当作额外独立生成图来凑目标数量。
