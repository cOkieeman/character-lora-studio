# Caption 规范

Caption 必须先按目标模型族分流。Anima 与 Krea 2 可以复用图片，但不应共用同一份训练 `.txt`。

## 通用文件规则

- 每张导出图片对应一个同名 `.txt`。
- 使用 UTF-8 和英文内容。
- 只描述画面中真实可见的事实。
- 触发词拼写必须在全部 caption、测试 prompt 和发布说明中一致。
- 中文解释放入 `caption_review_中文.md`，不混入训练 caption。
- 同一图片需要同时训练两个模型族时，分别导出到 `Anima/` 与 `Krea2/`，不要原地覆盖。

## Anima Profile

Anima 使用英文 Danbooru/Gelbooru canonical tags，英文逗号分隔。不要自造同义标签。

推荐顺序：

```text
1girl, <trigger>, solo, <shot/view>, <controllable identity>, <clothes>, <pose/action>, <expression>, <background>, <style/light>
```

默认删除：

- `newest`, `safe`
- `masterpiece`, `best quality`, `high quality`
- `score_1` 至 `score_9`
- `artist name` 和具体画师名
- 错误、重复、冲突或不可见的标签
- `watermark`, `signature`, `logo`, `text`；相关图片通常应直接淘汰

负面提示词不得写入训练 caption。Tag shuffle、keep-tokens 和 tag dropout 只在已验证的 Anima trainer profile 中启用。

## Krea 2 Profile

Krea 2 使用 Qwen3-VL 英文自然语言 caption，不以 WD14 逗号标签作为首选格式。

- 使用完整、清楚、逐图不同的英文句子。
- 将触发词自然放入人物身份、服装名称或风格名称的位置。
- 描述镜头、视角、动作、表情、背景、光照和所有需要保持可控的变量。
- 不要重复展开希望主要绑定到触发词的固定概念细节。
- 训练 caption 按 AnimaLoraStudio 0.23.1 文档最多使用 512 token；版本变化时重新核对。
- 推荐 LLM/VLM caption 后人工审查。WD14 链路机制上可用，但不是 Krea 2 首选。
- 默认关闭 `shuffle_caption`、`keep_tokens` 和 `tag_dropout`。

角色示例：

```text
sulianyan is a young Chinese woman shown from the waist up in a three-quarter view. She is reading beside a wooden window in soft afternoon light, wearing a modern dark coat and looking thoughtful.
```

衣服示例：

```text
A woman with short black hair is wearing mirellenavyoutfit in a full-body three-quarter view. She is walking through a modern fantasy city at dusk while carrying a small shoulder bag.
```

## 概念绑定

| LoRA 类型 | 触发词绑定 | Caption 重点描述 | 不应混入 |
|---|---|---|---|
| `character` | 脸、关键发型、瞳色、核心发饰等身份锚点 | 服装、动作、镜头、背景、表情和兼容画风 | 另一个角色触发词 |
| `outfit` | 固定版型、配色、材质、纹样和成套配件 | 穿着者外貌、动作、镜头、背景和光照 | 目标角色触发词 |
| `character_outfit` | 人物与签名服装的整体组合 | 动作、镜头、背景和表情 | 暗示服装可自由替换的错误描述 |
| `style` | 稳定画面语言和渲染方式 | 人物、物体、场景、构图和内容 | 反复出现的单一角色或场景 |

“不写固定细节”不是机械删除全部特征。希望能单独开关的发饰、服装组件或道具应保留统一表达；希望只由触发词召回的固定组合才少写或不写。

## Outfit Caption 规则

- Outfit-only 数据必须使用多个穿着者。
- Anima caption 保留穿着者的发色、发型、瞳色和其他变量标签，让服装触发词与特定脸解绑。
- Krea 2 caption 用自然语言描述穿着者变量，并写成 `wearing <outfit_trigger>`。
- 固定服装细节如果希望整体随触发词出现，不要在每张 caption 里完整复述。
- 希望独立控制的外套、帽子、手套或饰品，应使用稳定 canonical tag 或稳定英文短语。

## Alternate Form

Anima 人形示例：

```text
1girl, mirellevane, solo, upper body, looking at viewer, short hair, dark blue hair, white hair tips, green eyes, black jacket, smile, city street
```

Anima 兔形示例：

```text
mirellevane, rabbit form, animal focus, solo, dark blue fur, white ear tips, green eyes, sitting, simple background
```

兔形不要使用 `1girl`。不同解剖形态默认分开训练；确需混合时全量使用明确 form 表达，并分别测试污染。

## 审查清单

- 模型族与 caption profile 是否一致
- 图片与 `.txt` 是否一一对应
- 触发词是否唯一、拼写一致
- 是否残留中文、占位符、重复内容或自动打标错误
- Shot/view 与实际裁切是否一致
- 被遮挡或裁掉的特征是否被误写
- 固定概念与可控变量的策略是否一致
- Outfit-only 是否混入角色触发词或单一穿着者偏置
- Anima 是否残留 `newest`, `safe` 或质量标签
- Krea 2 是否仍是机械 WD14 标签串
