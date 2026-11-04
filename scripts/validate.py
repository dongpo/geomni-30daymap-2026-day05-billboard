from pathlib import Path
import json
import numpy as np
O=Path(__file__).resolve().parents[1]
d=json.loads((O/'web/analysis.json').read_text()); p=json.loads((O/'web/samples.geojson').read_text()); z=np.array([x['properties']['zone'] for x in p['features']]); r=d['results']; n=len(z)
assert n==d['meta']['sample_count']
assert len(r)==30 and all(len(v)==n and all(isinstance(x,int) and 0<=x<=5 for x in v) for v in r.values())
for f in [0,1]:
 for h in d['meta']['heights']:
  assert np.all(np.array(r[f'{f}-{h}-6'])>=r[f'{f}-{h}-15'])
  assert np.all(np.array(r[f'{f}-{h}-15'])>=r[f'{f}-{h}-30'])
comparison=[]
for h in d['meta']['heights']:
 v=np.array(r[f'0-{h}-15']);comparison.append({'height':h,'visible_points':int((v>0).sum()),'equal_weight_score':round(float(np.mean([(v[z==i]/5).mean() for i in range(3)]))*100,2)})
report={'tests':['30 scenarios: sample lengths and discrete visibility range valid','Raising unknown obstacles never increases visibility in all 10 face/height combinations'],'height_comparison':comparison}
(O/'evidence/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
