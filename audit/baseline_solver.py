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
    out += [[r[::-1] for r in x] for x in out]
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
    if op=='geom':
      return transforms(inp)[program[1]]
    if op=='color':
      m=program[1]; return [[m.get(v,v) for v in r] for r in inp]
    if op=='tile':
      oh,ow=program[1:]; return [[inp[r%h][c%w] for c in range(ow)] for r in range(oh)]
    if op=='scale':
      sy,sx=program[1:]; return [[v for x in r for v in [x]*sx] for r in inp for _ in range(sy)]
    if op=='crop':
      y,x,hh,ww=program[1:]; return [r[x:x+ww] for r in inp[y:y+hh]]
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
    if op=='gravity':
      color,axis,side=program[1:]; out=copy(inp)
      if axis=='down':
        for c in range(w):
          vals=[inp[r][c] for r in range(h) if inp[r][c]==color]
          for r in range(h): out[r][c]=0
          for i in range(len(vals)): out[h-len(vals)+i][c]=color
      elif axis=='up':
        for c in range(w):
          n=sum(inp[r][c]==color for r in range(h))
          for r in range(h): out[r][c]=color if r<n else (0 if inp[r][c]==color else inp[r][c])
      elif axis=='left':
        for r in range(h):
          n=sum(v==color for v in inp[r])
          row=[color]*n+[0]*(w-n)
          out[r]=[row[c] if inp[r][c] in (0,color) else inp[r][c] for c in range(w)]
      elif axis=='right':
        for r in range(h):
          n=sum(v==color for v in inp[r]); row=[0]*(w-n)+[color]*n
          out[r]=[row[c] if inp[r][c] in (0,color) else inp[r][c] for c in range(w)]
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
      if oh//ih==ow//iw: ps.append(('scale',oh//ih,ow//iw))
      ps.append(('tile',oh,ow))
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
    return ps


def infer(train):
    if not train: return []
    programs=candidates(train[0]['input'],train[0]['output'])
    for ex in train[1:]:
      programs=[p for p in programs if apply(ex['input'],p)==ex['output']]
      if not programs: break
    return programs


def predict_task(task, attempts=2):
    programs=infer(task.get('train',[])); result=[]
    for test in task.get('test',[]):
      preds=[]
      for p in programs:
        y=apply(test['input'],p)
        if y is not None and y not in preds: preds.append(y)
      if not preds:
        # Explicitly low-information fallback, with distinct shapes if available.
        for ex in task.get('train',[]):
          if ex['output'] not in preds: preds.append(copy(ex['output']))
      if not preds: preds=[copy(test['input'])]
      while len(preds)<attempts: preds.append(copy(preds[-1]))
      result.append({f'attempt_{i+1}':preds[i] for i in range(attempts)})
    return result


def generate(challenges_path=DATA/'arc-agi_test_challenges.json',out_path=OUT):
    challenges=json.loads(Path(challenges_path).read_text())
    result={tid:predict_task(task) for tid,task in challenges.items()}
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    Path(out_path).write_text(json.dumps(result,separators=(',',':')))
    return result

if __name__=='__main__':
    generate(); print(f'Wrote {OUT}')
