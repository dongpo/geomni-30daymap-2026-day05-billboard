from pathlib import Path
import json,math
from shapely.geometry import shape,Point,LineString
from shapely.ops import transform
from pyproj import Transformer
O=Path(__file__).resolve().parents[1];d=json.loads((O/'web/analysis.json').read_text());m=d['meta'];b=json.loads((O/'web/buildings.geojson').read_text());project=Transformer.from_crs(4326,3826,always_xy=True).transform
host=transform(project,shape(next(f for f in b['features'] if f['properties']['id']==m['host_id'])['geometry']));checks=[]
for f in m['faces']:
 board=transform(project,shape(f['polygon']));center=Point(*project(*f['center']));a=math.radians(f['normal_bearing']);nx,ny=math.sin(a),math.cos(a)
 assert board.intersection(host).area<1e-7
 assert .29<board.distance(host)<.31
 assert not host.contains(Point(center.x+nx,center.y+ny))
 assert host.contains(Point(center.x-nx,center.y-ny))
 # Eye directly behind the wall crosses the host below its roof at every selectable height.
 for h in m['heights']:
  back=Point(center.x-nx*10,center.y-ny*10);ray=LineString([back,center]);assert ray.intersection(host).length>1 and h+1.5<m['host_height']
 checks.append({'face':f['id'],'bearing':f['normal_bearing'],'host_overlap_m2':board.intersection(host).area,'wall_clearance_m':board.distance(host),'outward_normal_and_back_occlusion':'pass'})
(O/'evidence/placement-validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
