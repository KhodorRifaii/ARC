import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from arc_solver import infer,apply,transforms,valid_grid,predict_task
from validate import validate_submission

class RegressionTests(unittest.TestCase):
    def test_all_programs_fit_every_demo(self):
        train=[{'input':[[1,2]],'output':[[3,4,3,4]]}]
        programs=infer(train)
        self.assertNotIn(('tile',1,2),programs)
        self.assertNotIn(('scale',1,2),programs)
        self.assertTrue(all(apply(train[0]['input'],p)==train[0]['output'] for p in programs))
    def test_color_map_combines_examples(self):
        train=[{'input':[[1,2]],'output':[[4,4]]},{'input':[[2,3]],'output':[[4,5]]}]
        self.assertTrue(any(apply([[1,3]],p)==[[4,5]] for p in infer(train)))
    def test_transform_indices_are_stable(self):
        self.assertEqual(len(transforms([[1]])),8)
        self.assertEqual(len(transforms([[1,2],[3,4]])),8)
    def test_crop_rejects_out_of_bounds(self):
        self.assertIsNone(apply([[1]],('crop',1,1,3,3)))
    def test_invalid_grids(self):
        for g in ([],[[]],[[True]],[[10]],[[1],[1,2]],[[1]*31]):
            self.assertFalse(valid_grid(g))
    def test_validator_rejects_missing_output(self):
        with self.assertRaises(ValueError): validate_submission({'a':{'test':[{'input':[[1]]}]}},{'a':[]})
    def test_relative_tile(self):
        self.assertEqual(apply([[1,2,3]],('tile',2,1)),[[1,2,3],[1,2,3]])
    def test_attempt_count_is_fixed(self):
        for attempts in (0,-1,1,3,True):
            with self.assertRaises(ValueError):predict_task({},attempts)
    def test_notebook_embeds_current_source(self):
        import ast,json
        root=Path(__file__).resolve().parents[1]
        nb=json.loads((root/'notebooks/arc_submission.ipynb').read_text())
        source=''.join(next(c for c in nb['cells'] if c['cell_type']=='code')['source'])
        assignments=[n for n in ast.parse(source).body if isinstance(n,ast.Assign)]
        files=next(ast.literal_eval(n.value) for n in assignments if any(isinstance(t,ast.Name) and t.id=='files' for t in n.targets))
        for name,text in files.items():self.assertEqual(text,(root/'src'/name).read_text())
if __name__=='__main__':unittest.main()
