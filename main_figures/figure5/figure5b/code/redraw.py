from pathlib import Path
import importlib.util
root = Path(__file__).resolve().parents[1]
engine = root.parent / '重绘全部.py'
spec = importlib.util.spec_from_file_location('replot_engine', engine)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.render('5e')
