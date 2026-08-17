# 角色 LoRA Studio

一个面向 Codex 的角色 LoRA 工作流插件。它把角色设定、数据集矩阵、图片筛选、Booru 打标、正则集、训练导出和 checkpoint 测试固化为可恢复的本地流程，避免任务上下文变化后丢失关键决策。

## 主要能力

- 新建或恢复角色 LoRA 项目
- 维护角色设定、触发词、固定特征和可控标签
- 规划景别、视角、动作、服饰与画风覆盖
- 筛选候选图并保留淘汰原因
- 生成和审查 Booru 风格英文 caption
- 建立不含角色身份特征的正则集
- 导出 AnimaLoraStudio、Krea2 等训练包
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

也可以让它从已有项目继续：

```text
使用 $character-lora-studio 读取 <角色项目目录> 的项目状态，并继续下一阶段。
```

常见用法：

```text
使用 $character-lora-studio 审查这批候选图，按身份、脸部、发型发饰、人体、服饰、构图和训练价值评分。
```

```text
使用 $character-lora-studio 按 Booru 标签规则检查 caption，并导出 Anima 和 Krea2 训练包。
```

## 项目初始化

插件附带 PowerShell 初始化脚本，可建立标准目录、角色配置、项目状态和图片清单。通常只需让 Codex “为角色初始化 LoRA 项目”，Codex 会从当前 Skill 安装目录解析脚本路径；手动调用时可使用：

```powershell
& "<插件目录>\skills\character-lora-studio\scripts\init-character-lora-project.ps1" `
  -Root "D:\LoRA\MyCharacter" `
  -CharacterId "my_character" `
  -DisplayName "角色名" `
  -Trigger "my_character"
```

脚本不会覆盖已经存在的项目管理文件。

## 工作原则

- 文件系统是项目状态的唯一事实来源。
- 原始素材保持不变，裁切、去背景和修改版放入派生目录。
- 每张训练图必须配有同名 `.txt` caption。
- 训练 caption 使用英文规范标签，中文仅用于审查说明。
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

当前版本：`0.1.0`
