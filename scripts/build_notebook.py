"""Rebuild the offline notebook from current source files."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def build():
    path=ROOT/'notebooks/arc_submission.ipynb'
    notebook=json.loads(path.read_text())
    cell=next(c for c in notebook['cells'] if c['cell_type']=='code')
    source=''.join(cell['source'])
    start=source.index('files = ')
    end=source.index('\ncode_dir=',start)
    files={name:(ROOT/'src'/name).read_text() for name in ('arc_solver.py','validate.py')}
    source=source[:start]+'files = '+repr(files)+source[end:]
    compile(source,str(path),'exec')
    cell.update(source=source.splitlines(keepends=True),outputs=[],execution_count=None)
    path.write_text(json.dumps(notebook,indent=2)+'\n')
    return path
if __name__=='__main__':print(build())
