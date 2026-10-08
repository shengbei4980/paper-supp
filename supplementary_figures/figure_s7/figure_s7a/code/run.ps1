$ErrorActionPreference = 'Stop'
$figurePython = 'D:/xuexi/canshuhua/anaconda/Anaconda/envs/py311/python.exe'
foreach ($script in @('build_data.py', 'plot_lorenz.py', 'verify_data.py')) {
    & $figurePython (Join-Path $PSScriptRoot $script)
    if ($LASTEXITCODE -ne 0) { throw "$script failed" }
}
$pdfPython = 'C:/Users/19392/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $pdfPython (Join-Path $PSScriptRoot 'verify_pdf.py')
if ($LASTEXITCODE -ne 0) { throw 'PDF verification failed' }
