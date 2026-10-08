$ErrorActionPreference = 'Stop'
$figurePython = 'D:/xuexi/canshuhua/anaconda/Anaconda/envs/py311/python.exe'
$figurePdfPython = 'C:/Users/19392/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
foreach ($figureScript in @('build_data.py','plot_figure3c.py','verify_data.py')) {
    & $figurePython -X utf8 (Join-Path $PSScriptRoot $figureScript)
    if ($LASTEXITCODE -ne 0) { throw "$figureScript failed with exit $LASTEXITCODE" }
}
& $figurePdfPython -X utf8 (Join-Path $PSScriptRoot 'verify_pdf.py')
if ($LASTEXITCODE -ne 0) { throw "PDF verification failed with exit $LASTEXITCODE" }
