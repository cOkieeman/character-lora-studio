# 导出与交付

## 通用预检

- 图片可解码，尺寸合理，无零字节文件
- 图片与 caption 同名配对
- 无重复 hash 和近重复构图
- 训练集、淘汰区、正则集物理分离
- caption 不含触发词拼写错误、中文或禁用质量标签
- 记录图片数量、caption 数量、触发词和生成日期

## AnimaLoraStudio

- 保留项目原始训练目录，不直接把导出包当编辑源。
- 训练集和正则集分别导入。
- 正则集必须保持通用，不含角色触发词。
- 保存 YAML、训练参数、sample prompts、negative prompt、epoch/step 产物和测试 seed。
- 训练完成后至少比较早、中、晚三个 checkpoint。

## Krea2 交付

- 压缩包命名：`krea2-【角色名】训练集.zip`。
- 压缩包内只放老师需要的训练文件夹及图片-caption 对。
- 不混入正则、淘汰区、说明、contact sheet、脚本或中间产物，除非老师明确要求。
- 说明和 caption 审查报告用中文单独提供，不塞进训练压缩包。
- 上传前解压到临时目录并重新验证配对数。

## 正则集复用包

- 单独导出，不与 Krea2 训练包混合。
- 保留图片-caption 对和一份中文来源／筛选说明。
- 不包含 API key、抓取 URL 或账户信息。

## Civitai

- 模型文件按实际 checkpoint/epoch 命名。
- 填写 base model、epoch、steps、推荐 strength 和 trigger words。
- 示例图保留生成参数，并检查资源关联正确。
- 上传和发布是外部副作用，必须由用户明确要求。
