$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:PATH='D:/xuexi/canshuhua/anaconda/Anaconda/envs/geogis/Library/bin;'+$env:PATH
$py='D:/xuexi/canshuhua/anaconda/Anaconda/envs/geogis/python.exe'
foreach ($script in @('plot_Figure3a_county_supply.py','review_final_delivery.py','review_place_labels.py')) {
    & $py (Join-Path $PSScriptRoot $script)
    if ($LASTEXITCODE -ne 0) { throw ('执行失败：'+$script) }
}
