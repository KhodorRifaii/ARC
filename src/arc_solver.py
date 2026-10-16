"""Symbolic ARC program search and competition submission generation.

The solver only sees task demonstrations and test inputs. It does not read labels.
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs" / "submission.json"


def key(g): return tuple(tuple(r) for r in g)
def copy(g): return [r[:] for r in g]
def dims(g): return len(g), len(g[0]) if g else 0


def transforms(g):
    a=copy(g); out=[]
    for _ in range(4):
        out.append(a); a=[list(r) for r in zip(*a[::-1])]
    out += [x[::-1] for x in out]
    return out


def object_components(g, diagonal=False, background=None):
    h,w=dims(g); seen=set(); objs=[]
    for r in range(h):
      for c in range(w):
        color=g[r][c]
        if (r,c) in seen or (background is not None and color==background): continue
        stack=[(r,c)]; seen.add((r,c)); cells=[]
        while stack:
          y,x=stack.pop(); cells.append((y,x))
          steps=[(1,0),(-1,0),(0,1),(0,-1)]
          if diagonal: steps += [(1,1),(1,-1),(-1,1),(-1,-1)]
          for dy,dx in steps:
            yy,xx=y+dy,x+dx
            if 0<=yy<h and 0<=xx<w and (yy,xx) not in seen and g[yy][xx]==color:
              seen.add((yy,xx)); stack.append((yy,xx))
        ys=[p[0] for p in cells]; xs=[p[1] for p in cells]
        objs.append({'color':color,'cells':cells,'box':(min(ys),min(xs),max(ys)+1,max(xs)+1)})
    return objs


def apply(inp, program):
    h,w=dims(inp); op=program[0]
    if op=='compose':
      x=apply(inp,program[1])
      return apply(x,program[2]) if x else None
    if op=='bbox':
      bg=program[1]
      if bg=='mode': bg=Counter(v for row in inp for v in row).most_common(1)[0][0]
      cells=[(r,c) for r in range(h) for c in range(w) if inp[r][c]!=bg]
      if not cells: return None
      y,x=min(r for r,c in cells),min(c for r,c in cells)
      yy,xx=max(r for r,c in cells)+1,max(c for r,c in cells)+1
      return [row[x:xx] for row in inp[y:yy]]
    if op=='object':
      bg,selection=program[1:]
      if bg=='mode': bg=Counter(v for row in inp for v in row).most_common(1)[0][0]
      objects=object_components(inp,background=bg)
      if not objects: return None
      ob=sorted(objects,key=lambda o:len(o['cells']),reverse=selection=='largest')[0]
      y,x,yy,xx=ob['box']
      return [row[x:xx] for row in inp[y:yy]]
    if op=='geom':
      return transforms(inp)[program[1]]
    if op=='color':
      m=program[1]; return [[m.get(v,v) for v in r] for r in inp]
    if op=='tile':
      sy,sx=program[1:]; oh,ow=h*sy,w*sx; return [[inp[r%h][c%w] for c in range(ow)] for r in range(oh)]
    if op=='scale':
      sy,sx=program[1:]; return [[v for x in r for v in [x]*sx] for r in inp for _ in range(sy)]
    if op=='crop':
      y,x,hh,ww=program[1:]
      if y+hh>h or x+ww>w: return None
      return [r[x:x+ww] for r in inp[y:y+hh]]
    if op=='majority':
      bg=program[1]; counts=Counter(v for r in inp for v in r if v!=bg)
      fg=counts.most_common(1)[0][0] if counts else bg
      return [[fg if v==bg else bg for v in r] for r in inp]
    if op=='fill_boxes':
      bg,fill=program[1:]; out=copy(inp)
      for ob in object_components(inp,background=bg):
        y1,x1,y2,x2=ob['box']
        if y2-y1>2 and x2-x1>2:
          border={(y1,x) for x in range(x1,x2)}|{(y2-1,x) for x in range(x1,x2)}|{(y,x1) for y in range(y1,y2)}|{(y,x2-1) for y in range(y1,y2)}
          if all(inp[y][x]==ob['color'] for y,x in border):
            for y in range(y1+1,y2-1):
              for x in range(x1+1,x2-1): out[y][x]=fill
      return out
    if op=='complete_lines':
      bg,fg=program[1:]; out=copy(inp)
      for r in range(h):
        if all(v in (bg,fg) for v in inp[r]) and fg in inp[r]: out[r]=[fg]*w
      for c in range(w):
        col=[inp[r][c] for r in range(h)]
        if all(v in (bg,fg) for v in col) and fg in col:
          for r in range(h): out[r][c]=fg
      return out
    return None


def candidates(inp, out):
    ih,iw=dims(inp); oh,ow=dims(out); ps=[]
    # Eight dihedral symmetries.
    for i,x in enumerate(transforms(inp)):
      if x==out: ps.append(('geom',i))
    # Per-color map, constrained by all pixels.
    if (ih,iw)==(oh,ow):
      m={}; rev={}; ok=True
      for arow,brow in zip(inp,out):
        for a,b in zip(arow,brow):
          if (a in m and m[a]!=b) or (b in rev and rev[b]!=a): ok=False; break
          m[a]=b; rev[b]=a
        if not ok: break
      if ok and m!={c:c for c in m}: ps.append(('color',m))
    if ih and iw and oh%ih==0 and ow%iw==0:
      ps.append(('scale',oh//ih,ow//iw))
      ps.append(('tile',oh//ih,ow//iw))
    if oh<=ih and ow<=iw:
      for y in range(ih-oh+1):
       for x in range(iw-ow+1):
        if inp[y:y+oh] and [r[x:x+ow] for r in inp[y:y+oh]]==out: ps.append(('crop',y,x,oh,ow))
    colors=set(v for r in inp for v in r)
    if colors:
      bg=min(colors,key=lambda c:sum(v==c for r in inp for v in r))
      if ('majority',bg) not in ps and apply(inp,('majority',bg))==out: ps.append(('majority',bg))
    for bg in colors:
      for fill in range(10):
        p=('fill_boxes',bg,fill)
        try:
          if apply(inp,p)==out: ps.append(p)
        except Exception: pass
      for fg in colors-{bg}:
        p=('complete_lines',bg,fg)
        if apply(inp,p)==out: ps.append(p)
    return [p for p in ps if apply(inp,p)==out]


def infer(train):
    if not train: return []
    programs=candidates(train[0]['input'],train[0]['output'])
    programs=[p for p in programs if p[0]!='color']
    bases=[('geom',i) for i in range(8)]
    for bg in ['mode']+list(range(10)):
        bases.append(('bbox',bg))
        bases.extend(('object',bg,which) for which in ('largest','smallest'))
    # Infer mapping jointly from all demonstrations, including many-to-one maps.
    for base in bases:
        transformed=[apply(ex['input'],base) for ex in train]
        if any(x is None or dims(x)!=dims(ex['output']) for x,ex in zip(transformed,train)):
            continue
        if all(x==ex['output'] for x,ex in zip(transformed,train)):
            programs.append(base)
            continue
        mapping={}; valid=True
        for x,ex in zip(transformed,train):
            for row,target in zip(x,ex['output']):
                for a,b in zip(row,target):
                    if a in mapping and mapping[a]!=b: valid=False
                    mapping[a]=b
        if valid: programs.append(('compose',base,('color',mapping)))
    return [p for p in programs if all(apply(ex['input'],p)==ex['output'] for ex in train)]


def predict_task(task, attempts=2):
    programs=infer(task.get('train',[])); result=[]
    for test in task.get('test',[]):
      preds=[]
      for p in programs:
        y=apply(test['input'],p)
        if valid_grid(y) and y not in preds: preds.append(y)
      if not preds:
        # Explicitly low-information fallback, with distinct shapes if available.
        for ex in task.get('train',[]):
          if ex['output'] not in preds: preds.append(copy(ex['output']))
      if not preds: preds=[copy(test['input'])]
      while len(preds)<attempts: preds.append(copy(preds[-1]))
      result.append({f'attempt_{i+1}':preds[i] for i in range(attempts)})
    return result


def valid_grid(g):
    return isinstance(g,list) and 1<=len(g)<=30 and isinstance(g[0],list) and 1<=len(g[0])<=30 and all(isinstance(row,list) and len(row)==len(g[0]) and all(type(v) is int and 0<=v<=9 for v in row) for row in g)


def generate(challenges_path=DATA/'arc-agi_test_challenges.json',out_path=OUT):
    challenges=json.loads(Path(challenges_path).read_text())
    result={tid:predict_task(task) for tid,task in challenges.items()}
    from validate import validate_submission
    validate_submission(challenges,result)
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    Path(out_path).write_text(json.dumps(result,separators=(',',':')))
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--challenges',type=Path,default=DATA/'arc-agi_test_challenges.json')
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args()
    generate(args.challenges,args.output); print(f'Wrote {args.output}')
