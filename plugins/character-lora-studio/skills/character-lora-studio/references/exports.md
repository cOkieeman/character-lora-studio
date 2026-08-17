# 导出与交付

## 通用预检

- 图片可解码、尺寸合理、无零字节文件
- 图片与 caption 同名配对
- 无重复 hash 和高相似近重复构图
- 训练集、淘汰区、正则集物理分离
- 触发词拼写一致，无中文占位符或错误角色名
- Concept type、模型族、caption profile 和 trainer version 已记录
- 图片数量、caption 数量、生成日期和来源版本已记录

## 双模型族导出

同一素材同时训练 Anima 与 Krea 2 时使用两个独立导出树：

```text
07_导出/
  Anima/
    train/
    reg/
    config/
  Krea2/
    train/
    reg/
    config/
```

- Anima `train/` 使用 Booru tag caption。
- Krea2 `train/` 使用英文自然语言 caption。
- 不要通过修改同一个 `.txt` 目录来切换模型族。
- 正则 caption 也必须与目标模型族兼容。

## AnimaLoraStudio

- 保留项目原始训练目录，不直接把导出包当编辑源。
- 为不同模型族创建不同 trainer version；不要原地把完成的 Anima version 改成 Krea 2。
- 切换模型族后审查所有显式保留值，不能只看 `model_family`。
- 训练集和正则集分别导入。
- 保存 YAML、trainer commit/version、模型文件名、训练参数、sample prompts、negative prompt、epoch/step 产物和测试 seed。
- 完整训练前必须保存 5–10 step 烟雾测试结果。
- 训练完成后至少比较早、中、晚三个 checkpoint。

## Krea 2

- 训练底模必须是 Krea 2 Raw；Turbo 只用于测试推理。
- 记录 Raw 与 Qwen3-VL 使用 bf16 还是官方 FP8。
- 导出前确认自然语言 caption、`krea2_shift`、SDPA、text encoder cache、tag shuffle 关闭状态和硬件 profile。
- 12GB/16GB 显存使用 Block 交换时记录 `blocks_to_swap` 与系统内存占用。
- Krea 2 权重受其独立模型许可证约束，发布时重新核对当前模型卡。

## Krea 2 训练交付包

- 压缩包命名：`krea2-【角色或服装名】训练集.zip`。
- 压缩包内只放目标训练流程需要的训练文件夹及图片-caption 对。
- Caption 格式以实际训练入口为准；Krea 2 原生链路默认交付英文自然语言版本。
- 不混入正则、淘汰区、说明、contact sheet、脚本或中间产物，除非接收方明确要求。
- 中文说明和 caption 审查报告单独提供，不塞进训练压缩包。
- 上传前解压到临时目录并重新验证配对数和 caption profile。

## Outfit LoRA 交付

- 说明触发词、固定服装结构、可控组件和明确排除项。
- 提供穿着者数量与单个穿着者占比。
- 提供角色身份泄漏、服装替换和角色+衣服叠加测试结果。
- 不在 outfit-only 包中混入目标角色触发词或角色专属正则。

## 正则集复用包

- 单独导出，不与训练交付包混合。
- 保留图片-caption 对和中文来源／筛选说明。
- 标注适用模型族和 caption profile。
- 不包含 API key、抓取 URL 或账户信息。

## Civitai

- 模型文件按实际 concept type、模型族、checkpoint 或 epoch 命名。
- 填写 base model、epoch、steps、推荐 strength 和 trigger words。
- Outfit LoRA 明确说明是否需要角色 LoRA、推荐叠加强度和已知身份泄漏。
- 示例图保留生成参数，并检查资源关联正确。
- 上传和发布是外部副作用，必须由用户明确要求。
