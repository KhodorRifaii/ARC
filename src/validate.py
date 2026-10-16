"""Strict submission validation against challenge inputs, without answer access."""
import json
import argparse

def validate_submission(challenges, submission):
    from arc_solver import valid_grid
    if not isinstance(submission,dict) or set(submission)!=set(challenges):
        raise ValueError('Submission task IDs must exactly match challenges')
    total=0
    for tid,task in challenges.items():
        records=submission[tid]
        if not isinstance(records,list) or len(records)!=len(task['test']):
            raise ValueError(f'{tid}: incorrect number of test outputs')
        for i,record in enumerate(records):
            if not isinstance(record,dict) or set(record)!={'attempt_1','attempt_2'}:
                raise ValueError(f'{tid}/{i}: exactly two attempts required')
            for name,grid in record.items():
                if not valid_grid(grid): raise ValueError(f'{tid}/{i}/{name}: invalid grid')
            total+=1
    return {'tasks':len(challenges),'test_outputs':total,'attempts':2*total}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('challenges');p.add_argument('submission');a=p.parse_args()
    print(validate_submission(json.load(open(a.challenges)),json.load(open(a.submission))))
