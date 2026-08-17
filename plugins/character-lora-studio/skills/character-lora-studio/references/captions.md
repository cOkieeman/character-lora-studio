# Caption 规范

## 文件格式

- 每张训练图对应一个同名 `.txt`。
- 使用 UTF-8、英文小写、英文逗号分隔。
- 使用模型生态可识别的 Danbooru/Gelbooru canonical tags；不要自造近义标签。
- 中文说明单独写入 `caption_review_中文.md`，不混入训练 `.txt`。

## 推荐顺序

```text
1girl, <trigger>, solo, <shot/view>, <fixed-or-controllable identity>, <clothes>, <pose/action>, <expression>, <background>, <style/light>
```

顺序不是模型真理，但整个项目要保持一致，便于审查和 diff。

## 逐图事实

- 只标画面里看得到的内容。
- 正面不要误标 `from side`；半身不要误标 `full body`。
- 被裁掉或遮挡的饰品不要当作可见事实。
- 多人 CG 裁掉其他角色后，重新检查残留手臂、阴影和互动动作。
- 背景去除后，删除原背景标签并标注实际背景。

## 默认删除

除非基模或训练方案明确依赖，否则从训练 caption 删除：

- `newest`, `safe`
- `masterpiece`, `best quality`, `high quality`
- `score_1` 至 `score_9`
- `artist name`, 具体画师名
- `watermark`, `signature`, `logo`, `text`（相关图通常应直接淘汰）
- 互相冲突或明显错误的自动标签

不要把负面提示词写进训练 caption。

## 人形与兔形

人形示例：

```text
1girl, mirellevane, solo, upper body, looking at viewer, short hair, dark blue hair, two-tone hair, white hair tips, green eyes, leaf hair ornament, black jacket, necklace, smile, city street
```

兔形示例：

```text
mirellevane, rabbit form, animal focus, solo, dark blue fur, white ear tips, green eyes, round body, sitting, simple background
```

不要在兔形 caption 使用 `1girl`。若人形与兔形放入同一 LoRA，必须全量使用明确 form tag；默认建议分开训练。

## 审查清单

- 触发词拼写是否唯一且一致
- 图片与 `.txt` 是否一一对应
- 是否残留中文、句号、重复标签或双逗号
- shot/view 与实际裁切是否一致
- 固定身份标签策略是否一致
- 衣服、姿势和背景是否逐图变化
- 是否残留 `newest`, `safe` 或质量标签
- 是否存在角色名误写、`1gril` 等拼写错误
