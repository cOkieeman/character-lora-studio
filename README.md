# 角色 LoRA Studio

一个面向 Codex 的角色、衣服、角色+衣服与画风 LoRA 工作流插件。它把概念设定、数据集矩阵、图片筛选、Anima/Krea 2 caption、正则集、硬件配置、训练导出和 checkpoint 测试固化为可恢复的本地流程，避免任务上下文变化后丢失关键决策。

## 主要能力

- 新建或恢复角色、衣服、角色+衣服或画风 LoRA 项目
- 维护触发词、固定概念、可控概念和变量
- 规划角色镜头或衣服穿着者、视角、动作与结构覆盖
- 筛选候选图并保留淘汰原因
- 分别生成 Anima Booru caption 与 Krea 2 英文自然语言 caption
- 建立不含目标身份或目标服装组合的正则集
- 按 GPU/VRAM/RAM 生成并审查 AnimaLoraStudio profile
- 导出 Anima、Krea 2 训练交付与 Civitai 发布包
- 使用固定测试提示词比较不同 epoch 或 step

## 安装

先添加 marketplace：

```powershell
codex plugin marketplace add cOkieeman/character-lora-studio
```

再安装插件：

```powershell
codex plugin add character-lora-studio@character-lora-studio
```

安装后建议新建一个 Codex 任务，确保插件与 Skill 已加载。

## 调用

在 Codex 中可以直接写：

```text
使用 $character-lora-studio 为这个角色建立 LoRA 数据集项目。
```

建立独立衣服 LoRA：

```text
使用 $character-lora-studio 为这套服装建立 outfit LoRA 项目，目标模型族为 Krea 2，触发词为 mirellenavyoutfit。
```

也可以让它从已有项目继续：

```text
使用 $character-lora-studio 读取 <角色项目目录> 的项目状态，并继续下一阶段。
```

常见用法：

```text
使用 $character-lora-studio 审查这批候选图，按身份、脸部、发型发饰、人体、服饰、构图和训练价值评分。
```

```text
使用 $character-lora-studio 为同一批图片分别生成 Anima Booru caption 和 Krea 2 英文自然语言 caption，并分目录导出。
```

```text
使用 $character-lora-studio 根据 RTX 5060 Ti 16GB、64GB RAM 和当前 AnimaLoraStudio 版本生成 Krea 2 烟雾测试配置，不要启动完整训练。
```

## 项目初始化

插件附带 Python 3.9+（仅标准库）与 PowerShell 初始化入口，可建立标准目录、概念配置、项目状态、图片清单、生成批次、覆盖矩阵和训练记录。通常只需让 Codex“初始化 LoRA 项目”，Codex 会从当前 Skill 安装目录解析脚本路径；手动调用时可使用：

```powershell
& "<插件目录>\skills\character-lora-studio\scripts\init-character-lora-project.ps1" `
  -Root "D:\LoRA\MyCharacter" `
  -CharacterId "my_character" `
  -DisplayName "角色名" `
  -Trigger "my_character"
```

脚本不会覆盖已经存在的项目管理文件。

初始化后的项目统一采用单角色完整目录：

```text
角色项目/
├─ 00_项目管理/
├─ 01_原始素材/
├─ 02_设计候选/
├─ 03_训练候选/
├─ 04_正式训练集/
├─ 05_淘汰区/
├─ 06_正则集/
├─ 07_导出/
├─ 08_测试样图/
├─ 08_丹炉导入/
├─ 09_训练产物/
├─ outputs/
├─ findings.md
├─ progress.md
└─ task_plan.md
```

旧项目如果存在 `management`、`source_workspace` 或顶层 `danlu_project`，
会作为 legacy 来源保留；整理时复制进标准目录并验证，不自动删除旧内容。

## 工作原则

- 文件系统是项目状态的唯一事实来源。
- 原始素材保持不变，裁切、去背景和修改版放入派生目录。
- 每张导出训练图必须配有同名 `.txt` caption。
- Anima 使用英文 Booru tags；Krea 2 使用英文自然语言，二者分目录保存。
- Outfit-only 数据使用多个穿着者，不混入目标角色触发词。
- 更换模型族时创建新 trainer version，不原地复用已完成配置。
- 完整训练前先做 5–10 step 烟雾测试。
- 淘汰图不永久删除，需记录淘汰原因。
- 不在插件仓库中保存角色私有素材、训练产物、API key 或账号凭据。

## 仓库结构

```text
.agents/plugins/marketplace.json
plugins/character-lora-studio/
  .codex-plugin/plugin.json
  skills/character-lora-studio/
README.md
```

当前版本：`0.3.0`

## 双包与分阶段项目管理

候选图目标、合格图目标、包的用途、背景与画风策略都在角色项目配置中填写。
不预设所有项目必须做两包，也不把某个角色的数量或身体特征写入插件。

跨平台初始化与只读审计：

```bash
python3 "<技能目录>/scripts/project_tools.py" init "<项目目录>" --character-id my_character --display-name "角色名" --trigger my_character
python3 "<技能目录>/scripts/project_tools.py" audit "<项目目录>"
python3 "<技能目录>/scripts/project_tools.py" audit "<项目目录>" --ready-for-export --family anima --family krea2 --trigger my_character
```

审计检查清单、文件、hash、图片衍生关系和双 caption 状态，不替代图片解码、人体/身份审查和训练验证。
已保存原始生成候选按 hash 去重统计；裁切、修图、双模型导出不能虚增生成量。
从旧 schema 升级时先备份并转换副本，不以再次初始化覆盖旧记录。

插件与 Hub 均可完成筛选和双模型标注；可先由插件处理，再在 Hub 二次审核。图片、Anima、Krea 2 的初审和二审分别记录；将审核后的图片 ID、hash、caption 与状态导出回项目目录。
插件不包含 Hub API 客户端，不声称自动双向同步已实现。训练数据版本与运行记录分别冻结，
使用旧 LoRA 加练时记录父 checkpoint，并为 Anima/Krea 2 分别建立训练谱系。
详见技能中的 `references/project-management.md` 与 `references/staged-training.md`。

开发验证：`python3 -m unittest discover -s tests -v`。
