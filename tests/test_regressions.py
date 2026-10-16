import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from arc_solver import infer,apply,transforms,valid_grid
from validate import validate_submission

class RegressionTests(unittest.TestCase):
    def test_all_programs_fit_every_demo(self):
        train=[{'input':[[1,2]],'output':[[3,4,3,4]]}]
        self.assertTrue(all(apply(train[0]['input'],p)==train[0]['output'] for p in infer(train)))
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
if __name__=='__main__':unittest.main()
