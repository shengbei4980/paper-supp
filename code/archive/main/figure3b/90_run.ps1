param([string]$Python = 'D:\xuexi\canshuhua\anaconda\Anaconda\envs\py311\python.exe')
& $Python (Join-Path $PSScriptRoot '重绘Figure3b_NSF_NSFC.py')
if ($LASTEXITCODE -ne 0) { throw 'Figure3b 绘制或核查失败。' }
