# AnimaLoraStudio 训练 Profiles

这些值是安全起点，不是跨版本保证。生成配置前必须读取本地 AnimaLoraStudio 文档、当前项目 YAML、实际 GPU 和已安装权重。

## 已验证依据

- 本插件 `0.2.0` 编写时核对了 AnimaLoraStudio 本地 `0.23.1`。
- 同时核对了上游 `0.24.1`（2026-08-14）的 Krea 2 Block 交换测试显存修复。
- 版本高于或低于上述范围时，先比较模型族默认值和变更日志。

## 模型族分离

| 项目 | Anima | Krea 2 |
|---|---|---|
| 训练底模 | Anima base | Krea 2 Raw |
| 测试底模 | Anima base | Raw 或 Turbo |
| 文本编码 | Qwen3-0.6B / 项目配置 | Qwen3-VL-4B |
| Caption | Booru tags | 英文自然语言 |
| Timestep | Anima profile | `krea2_shift` |
| Attention | 项目支持的 backend | SDPA，配置通常为 `none` |
| Tag shuffle/dropout | 可按实验启用 | 默认关闭 |
| NaViT/SRA/Leap | 按 Anima 能力 | 不可用或隐藏 |

不要把完成的 Anima YAML 复制后只改 `model_family`。创建新 version，通过 UI 的模型族切换重算默认值，再逐项审查显式保留字段。

## Krea 2 权重

- 训练：Krea 2 Raw bf16 或官方 Raw FP8。
- 测试：Raw，或 Turbo bf16/FP8。
- 禁止使用 Turbo 作为训练底模。
- 低显存优先使用 Raw FP8 与 Qwen3-VL FP8。
- Krea 2 与 Anima 可共享 Qwen Image VAE。

## Krea 2 必查字段

```yaml
model_family: krea2
grad_checkpoint: true
timestep_sampling: krea2_shift
text_encoder_cache: true
attention_backend: none
shuffle_caption: false
keep_tokens: 0
tag_dropout: 0.0
sample_sampler_name: euler
sample_scheduler: simple
sample_infer_steps: 28
sample_cfg_scale: 4.5
```

使用 FP8 底模时必须开启 `grad_checkpoint`，并保持 DoRA 关闭。LoRA、LoHa、LoKr 与 rs-LoRA 是否可用仍以当前版本 UI 和启动校验为准。

## 显存档位

| 显存 | Krea 2 起步方案 | 风险 |
|---:|---|---|
| 12GB | Raw FP8、Qwen3-VL FP8、`blocks_to_swap: 28`、batch 1 | 贴边方案，必须先烟雾测试 |
| 16GB | Raw FP8、Qwen3-VL FP8、先用 `blocks_to_swap: 28` | 推荐低显存起点，稳定后可减少换出层数试速 |
| 24GB | Raw FP8，按峰值决定少量 Block 交换 | 训练余量明显增加 |
| 32GB+ | Raw FP8 从容；bf16 仍需核对峰值 | 可减少搬运，但权重和 TE 仍很大 |

系统内存建议 32GB 起，Krea 2 + Block 交换推荐 64GB。FP8 全部 28 层换出约需额外 11GB pinned RAM；还要为权重加载、文本编码器、系统和其他程序留余量。

50 系 NVIDIA GPU 需要兼容 Blackwell 的驱动和 PyTorch/CUDA 组合。不要仅凭“16GB”判断兼容性；先在 AnimaLoraStudio 设置页确认 GPU、Torch、CUDA 和 SDPA 健康状态。

## 16GB / 64GB 起步 Profile

适用于 RTX 5060 Ti 16GB 一类 NVIDIA 设备的首轮验证：

```yaml
model_family: krea2
blocks_to_swap: 28
grad_checkpoint: true
mixed_precision: bf16
text_encoder_cache: true
batch_size: 1
grad_accum: 2
resolution:
  - 1024
vae_cache_batch_size: 1
timestep_sampling: krea2_shift
attention_backend: none
shuffle_caption: false
tag_dropout: 0.0
```

这是资源 profile，不是最终质量配方。学习率、rank、epoch、正则权重和 optimizer 必须按 concept type、图片数量和烟雾测试结果单独决定。

## 小数据集质量起点

用于 30–50 张角色或单套衣服数据集的第一轮对照，不作为保证：

- LoRA rank：16 或 32；复杂角色或复杂服装优先比较 32。
- AdamW learning rate：`5e-5` 至 `1e-4`。
- Batch：1；`grad_accum` 2–4。
- Resolution：1024，保持合理宽高比分桶。
- 每 2 epoch 保存和采样，至少保留早、中、晚 checkpoint。
- 完整训练前用 5–10 step 验证启动链路。

不要同时更换 optimizer、rank、学习率、caption 和数据集版本，否则无法判断差异来源。

## 烟雾测试

5–10 step 测试至少确认：

- Raw 权重和 Qwen3-VL 权重路径正确
- FP8 权重被识别为训练底模
- Caption 走自然语言编码且触发词存在
- 文本缓存完成后释放文本编码器
- Latent cache 可建立或复用
- Block 交换实际生效并记录换出层数
- 第一个 optimizer step 成功
- 无 NaN、OOM、RAM 护栏或磁盘空间错误
- 可写出测试 checkpoint
- 任务结束或失败后显存与 pinned RAM 能释放

烟雾测试通过只证明链路可运行，不证明数据或质量配置正确。

## 全量训练前记录

- GPU 型号、VRAM、RAM、驱动、Torch 和 CUDA
- AnimaLoraStudio commit/version
- Raw/Turbo、FP8/bf16 与文本编码器文件名
- Dataset 和 caption profile 版本
- Concept type、trigger 和正则策略
- 完整 YAML
- 烟雾测试日志、峰值显存与峰值 RAM
