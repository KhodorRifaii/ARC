"""Reproducible exact-grid scoring; labels are loaded after predictions."""
import json
import hashlib
import time
from pathlib import Path
from arc_solver import predict_task
from validate import validate_submission
ROOT=Path(__file__).resolve().parents[1]

def measure(challenges,predictions,solutions):
    validate_submission(challenges,predictions)
    if set(challenges)!=set(solutions): raise ValueError('Solution IDs mismatch')
    correct=total=tasks_correct=0
    for tid,task in challenges.items():
        targets=solutions[tid]
        if len(targets)!=len(task['test']): raise ValueError('Solution count mismatch')
        hits=[any(p[k]==t for k in ('attempt_1','attempt_2')) for p,t in zip(predictions[tid],targets)]
        correct+=sum(hits);total+=len(hits);tasks_correct+=all(hits)
    return {'correct_outputs':correct,'total_outputs':total,'accuracy':correct/total,'fully_correct_tasks':tasks_correct,'total_tasks':len(challenges)}

def run():
    start=time.monotonic(); data=ROOT/'data'; report={}
    train=json.loads((data/'arc-agi_training_challenges.json').read_text())
    correct=total=0
    for task in train.values():
        for i,ex in enumerate(task['train']):
            reduced={'train':[x for j,x in enumerate(task['train']) if j!=i],'test':[{'input':ex['input']}]}
            p=predict_task(reduced)[0]
            correct+=any(p[k]==ex['output'] for k in ('attempt_1','attempt_2'));total+=1
    report['training_loo']={'correct_outputs':correct,'total_outputs':total,'accuracy':correct/total}
    for split in ('training','evaluation'):
        challenges=json.loads((data/f'arc-agi_{split}_challenges.json').read_text())
        predictions={tid:predict_task(task) for tid,task in challenges.items()}
        # Predictions completed before opening target labels. No labels reach solver.
        solutions=json.loads((data/f'arc-agi_{split}_solutions.json').read_text())
        report[split+'_test_outputs']=measure(challenges,predictions,solutions)
    report['solver_sha256']=hashlib.sha256((ROOT/'src/arc_solver.py').read_bytes()).hexdigest()
    report['seconds']=time.monotonic()-start
    (ROOT/'outputs/metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':run()
