# 正则集来源、筛选与对照

正则集用于维持基础分布和降低概念过拟合，不是训练目标的弱化复制品。它必须与模型族兼容，并与正式训练集分开版本化。

## 1. 先定义正则目标

记录：

- 模型族与 concept type
- 人物数量、主体类型和安全范围
- 镜头、宽高比和构图分布
- 需要排除的角色身份、服装组合、形态和 trigger
- 目标数量与允许来源

Character LoRA 的正则应是多样的通用人物。不要出现目标角色近似脸、标志性发型组合、完整签名服装或角色 trigger。

## 2. AI prior 首轮

AI prior 可以先做一次有边界的候选批次：

1. 使用通用人物提示，不写项目 trigger 或目标身份细节。
2. 匹配训练集的特写、上半身、全身、侧面和背面比例。
3. 变化脸、发型、发色、衣服、动作、背景、光照和兼容画风。
4. 生成后制作联系表，筛掉人体错误、文字、水印、多人污染、异常裁切、近重复和目标角色近似图。
5. 为保留图生成独立的 Anima canonical tag caption。

如果首轮 AI prior 在身份距离、人体质量、画风分布或镜头覆盖上不合格，不要默认无限重抽。记录失败原因并切换来源。

## 3. Gelbooru 回退

使用 Gelbooru 或其他 Booru 来源时：

- 使用通用内容 tag 搜索，不使用目标角色名、trigger、系列名或标志服装组合。
- 候选抓取量可先按目标正则数量额外增加约 10 张，给人工删坏图留余量；最终数量仍由实际合格图决定。
- 题材与训练集保持接近，同时让兼容画风分散到约 3–4 种，避免全部来自同一画师或同一种渲染。
- 保存来源信息和原始 tag，但训练 caption 仍需按当前 Anima profile 清洗。
- 排除未成年风险、意外 NSFW、多人、文字、水印、签名、低清、严重裁切和目标身份近似图；Caption 清洗同时排除 `artist name`、`logo`、`text`、`words` 以及目标重点特征。
- 检查下载重复、感知近重复和与训练集的交叉重复。
- 不因为原站 tag 存在就跳过视觉审查。

## 4. 来源隔离与版本对照

至少保留这些字段：

```yaml
regularization_candidate:
  source: ai_prior | gelbooru | hybrid
  images: 0
  captions: 0
  rejected: 0
  source_manifest: ""
  selection_manifest: ""
  train_overlap: 0
  trigger_hits: 0
  lookalike_review: pending
```

AI prior、Gelbooru 和 hybrid 必须先作为不同版本存在。若建立 hybrid，记录每个来源的数量；不要把旧正则、AI 图和 Booru 图混在同一目录后丢失来源。

## 5. 数量与分布

角色 LoRA 可从接近 1:1 的 train/reg 图片数开始，但这不是跨项目定律。更重要的是：

- shot 与 aspect-ratio 分布大致匹配
- 正则身份足够分散
- 没有目标概念近似图
- 每张图有独立、正确、无 trigger 的 caption

增加低质量正则不会自动改善泛化。

## 6. 正则验收

放入训练版前检查：

- 图片和 caption 一一对应
- trigger、outfit trigger 和禁止 tag 命中为 0
- 图片可解码，尺寸和桶分布合理
- 文件哈希重复、感知近重复和 train/reg 交叉重复为 0
- 无目标身份近似、完整签名组合、动物形态或项目禁止概念
- 无明显人体错误、多人、文字、水印、签名或异常裁切
- 来源清单、筛选清单和联系表完整

## 7. 何时判定某来源不合适

单看 smoke loss 不能判断正则质量。使用固定训练集、caption、config 和测试 prompt，比对不同正则候选的早期 checkpoint：

- 身份召回
- 签名服装泄漏
- 换装能力
- 一般人体与画面质量
- 风格漂移
- trigger 以外的基础模型能力

只有在完整训练获得授权时才执行付费或耗时的来源对照。对照后把选中的来源、版本和理由写回项目状态。

## 8. 变更后的缓存规则

新增、删除、替换正则图片或修改正则 caption 后：

- 创建新 regularization version
- 更新数量、哈希和来源清单
- 删除或隔离旧版本对应的 latent cache
- 重新运行当前版本的 smoke

不得让旧 cache 继续代表已经变化的正则集。
