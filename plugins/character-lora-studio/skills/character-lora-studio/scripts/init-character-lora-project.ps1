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
    '07_导出\Anima',
    '07_导出\Krea2',
    '07_导出\正则复用包',
    '08_测试样图',
    '09_训练产物'
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
        $content = $content.Replace($entry.Key, $entry.Value)
    }
    Set-Content -LiteralPath $DestinationPath -Value $content -Encoding UTF8
    Write-Host "[CREATE] $DestinationPath"
}

New-FileFromTemplate `
    -TemplatePath (Join-Path $assetRoot 'project-state.template.md') `
    -DestinationPath (Join-Path $resolvedRoot '00_项目管理\项目状态.md')

New-FileFromTemplate `
    -TemplatePath (Join-Path $assetRoot 'character-profile.template.yaml') `
    -DestinationPath (Join-Path $resolvedRoot '00_项目管理\角色配置.yaml')

$inventoryPath = Join-Path $resolvedRoot '00_项目管理\图片清单.csv'
if (-not (Test-Path -LiteralPath $inventoryPath)) {
    'file,category,status,concept_type,target_family,identity_score,face_score,hair_score,anatomy_score,outfit_score,composition_score,value_score,reject_reason,anima_caption_status,krea2_caption_status,notes' |
        Set-Content -LiteralPath $inventoryPath -Encoding UTF8
    Write-Host "[CREATE] $inventoryPath"
}
else {
    Write-Host "[SKIP] 已存在：$inventoryPath"
}

Write-Host "[DONE] 角色 LoRA 项目已初始化：$resolvedRoot"
