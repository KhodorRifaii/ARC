"""Exact-grid offline scoring. Prediction functions never receive solution files."""
import json, random
from pathlib import Path
from arc_solver import predict_task
ROOT=Path(__file__).resolve().parents[1]

def score_loo(challenges):
    correct=total=0
    for tid,task in challenges.items():
        for i,ex in enumerate(task['train']):
            reduced={'train':[x for j,x in enumerate(task['train']) if j!=i], 'test':[{'input':ex['input']}]}
            g=predict_task(reduced)[0]
            correct += any(g[k]==ex['output'] for k in ('attempt_1','attempt_2')); total+=1
    return correct,total

def score_eval(challenges, solutions):
    correct=total=0
    for tid,task in challenges.items():
        preds=predict_task(task); targets=solutions[tid]
        if len(preds)!=len(targets): raise ValueError(f'{tid}: output count mismatch')
        for p,t in zip(preds,targets):
            correct+=any(p[k]==t for k in ('attempt_1','attempt_2')); total+=1
    return correct,total

def score_task_holdout(challenges, seed=17, fraction=.2):
    """Split task IDs before evaluation to estimate transfer to unseen tasks."""
    ids=sorted(challenges); random.Random(seed).shuffle(ids); held=set(ids[:round(len(ids)*fraction)])
    correct=total=0
    for tid in held:
        task=challenges[tid]
        for i,ex in enumerate(task['train']):
            reduced={'train':[x for j,x in enumerate(task['train']) if j!=i], 'test':[{'input':ex['input']}]}
            p=predict_task(reduced)[0]
            correct+=any(p[k]==ex['output'] for k in ('attempt_1','attempt_2'));total+=1
    return correct,total,len(held)

if __name__=='__main__':
    d=ROOT/'data'
    train=json.loads((d/'arc-agi_training_challenges.json').read_text())
    eva=json.loads((d/'arc-agi_evaluation_challenges.json').read_text())
    # Read labels only in this scoring process, after predictions are generated.
    solutions=json.loads((d/'arc-agi_evaluation_solutions.json').read_text())
    a,b=score_loo(train); print(f'train leave-one-demo-out exact: {a}/{b} ({a/b:.3%})')
    a,b,n=score_task_holdout(train); print(f'train held-out tasks ({n} tasks) LOO exact: {a}/{b} ({a/b:.3%})')
    a,b=score_eval(eva,solutions); print(f'evaluation exact: {a}/{b} ({a/b:.3%})')
