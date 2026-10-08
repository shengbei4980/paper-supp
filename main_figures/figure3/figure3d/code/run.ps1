$ErrorActionPreference = 'Stop'
$pythonFigure3d = 'D:\xuexi\canshuhua\anaconda\Anaconda\envs\py311\python.exe'
if (-not (Test-Path -LiteralPath $pythonFigure3d)) { throw '请将 pythonFigure3d 设置为安装了 numpy、pandas、matplotlib、Pillow 的 Python 路径。' }
& $pythonFigure3d (Join-Path $PSScriptRoot 'redraw_Figure3d.py')
if ($LASTEXITCODE -ne 0) { throw '重绘失败。' }
& $pythonFigure3d (Join-Path $PSScriptRoot 'review_Figure3d.py')
if ($LASTEXITCODE -ne 0) { throw '复核失败。' }
