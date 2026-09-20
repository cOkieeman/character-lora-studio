[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Root,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9][a-z0-9_-]*$')]
    [string]$CharacterId,

    [Parameter(Mandatory = $true)]
    [string]$DisplayName,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9][a-z0-9_-]*$')]
    [string]$Trigger
)

$ErrorActionPreference = 'Stop'

$resolvedRoot = [System.IO.Path]::GetFullPath($Root)
$skillRoot = Split-Path -Parent $PSScriptRoot
$assetRoot = Join-Path $skillRoot 'assets'

$directories = @(
    '00_项目管理',
    '01_原始素材',
    '02_设计候选',
    '03_训练候选',
    '04_正式训练集',
    '05_淘汰区',
    '06_正则集',
    '07_导出/Anima',
    '07_导出/Krea2',
    '07_导出/正则复用包',
    '08_测试样图',
    '08_丹炉导入',
    '09_训练产物',
    'outputs'
)

[System.IO.Directory]::CreateDirectory($resolvedRoot) | Out-Null
foreach ($relativePath in $directories) {
    [System.IO.Directory]::CreateDirectory((Join-Path $resolvedRoot $relativePath)) | Out-Null
}

$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
$replacements = @{
    '{{CHARACTER_ID}}' = $CharacterId
    '{{DISPLAY_NAME}}' = $DisplayName
    '{{TRIGGER}}' = $Trigger
    '{{ROOT}}' = $resolvedRoot
    '{{TIMESTAMP}}' = $timestamp
}

function New-FileFromTemplate {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TemplatePath,

        [Parameter(Mandatory = $true)]
        [string]$DestinationPath
    )

    if (Test-Path -LiteralPath $DestinationPath) {
        Write-Host "[SKIP] 已存在：$DestinationPath"
        return
    }

    $content = Get-Content -LiteralPath $TemplatePath -Raw -Encoding UTF8
    foreach ($entry in $replacements.GetEnumerator()) {
        $value = [string]$entry.Value
        if ($TemplatePath.EndsWith('.yaml')) {
            $quoted = ConvertTo-Json -InputObject $value -Compress
            $value = $quoted.Substring(1, $quoted.Length - 2)
        }
        $content = $content.Replace($entry.Key, $value)
    }
    Set-Content -LiteralPath $DestinationPath -Value $content -Encoding UTF8
    Write-Host "[CREATE] $DestinationPath"
}

New-FileFromTemplate `
    -TemplatePath (Join-Path $assetRoot 'project-state.template.md') `
    -DestinationPath (Join-Path $resolvedRoot '00_项目管理/项目状态.md')

New-FileFromTemplate `
    -TemplatePath (Join-Path $assetRoot 'character-profile.template.yaml') `
    -DestinationPath (Join-Path $resolvedRoot '00_项目管理/角色配置.yaml')

New-FileFromTemplate `
    -TemplatePath (Join-Path $assetRoot 'task_plan.template.md') `
    -DestinationPath (Join-Path $resolvedRoot 'task_plan.md')

New-FileFromTemplate `
    -TemplatePath (Join-Path $assetRoot 'findings.template.md') `
    -DestinationPath (Join-Path $resolvedRoot 'findings.md')

New-FileFromTemplate `
    -TemplatePath (Join-Path $assetRoot 'progress.template.md') `
    -DestinationPath (Join-Path $resolvedRoot 'progress.md')

$ledgerTemplates = @{
    'inventory.template.csv' = '图片清单.csv'
    'batches.template.csv' = '生成批次.csv'
    'coverage.template.csv' = '覆盖矩阵.csv'
    'runs.template.csv' = '训练记录.csv'
}
foreach ($entry in $ledgerTemplates.GetEnumerator()) {
    New-FileFromTemplate `
        -TemplatePath (Join-Path $assetRoot $entry.Key) `
        -DestinationPath (Join-Path (Join-Path $resolvedRoot '00_项目管理') $entry.Value)
}

Write-Host "[DONE] 角色 LoRA 项目已初始化：$resolvedRoot"
