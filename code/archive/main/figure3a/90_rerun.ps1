$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:PATH='D:/xuexi/canshuhua/anaconda/Anaconda/envs/geogis/Library/bin;'+$env:PATH
$py='D:/xuexi/canshuhua/anaconda/Anaconda/envs/geogis/python.exe'
foreach ($script in @('绘制Figure3a_县域供给.py','复核最终交付.py','复核地名标签.py')) {
    & $py (Join-Path $PSScriptRoot $script)
    if ($LASTEXITCODE -ne 0) { throw ('执行失败：'+$script) }
}
