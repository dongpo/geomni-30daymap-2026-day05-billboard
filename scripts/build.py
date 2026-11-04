from pathlib import Path
import json,time,math
import numpy as np,geopandas as gpd
from shapely.geometry import Point,LineString,Polygon,mapping
from shapely.strtree import STRtree
from pyproj import Transformer
O=Path(__file__).resolve().parents[1];W=O/'web';start=time.time()
b=gpd.read_parquet(O/'building.parquet').to_crs(3826);parts=gpd.read_parquet(O/'building_part.parquet').to_crs(3826)
host=b[b.id=='308fed10-f070-4a4c-a911-8e89eef8b7ed'].iloc[0];poly=host.geometry
if poly.geom_type=='MultiPolygon':poly=max(poly.geoms,key=lambda x:x.area)
center=poly.centroid;parentset=set(parts.building_id)
# Parts replace their parent solid, preventing duplicate obstructions.
model=[]
for df,ispart in [(b,False),(parts,True)]:
 for _,r in df.iterrows():
  if (not ispart and r.id in parentset) or r.get('is_underground',False)==True:continue
  if r.geometry.distance(center)>550:continue
  if not r.geometry.is_valid:raise ValueError('invalid geometry')
  height=float(r.height) if r.height is not None and np.isfinite(r.height) and r.height>0 else None
  floors=float(r.num_floors) if r.num_floors is not None and np.isfinite(r.num_floors) and r.num_floors>0 else None
  base=float(r.min_height) if r.min_height is not None and np.isfinite(r.min_height) else 0
  mode='height' if height else ('floors' if floors else 'unknown')
  # Model extrusion convention explicitly recorded; not a surveyed 3D facade.
  model.append({'id':r.id,'geom':r.geometry,'base':base,'top':base+height if height else (base+floors*3 if floors else None),'method':mode})
geoms=[m['geom'] for m in model];tree=STRtree(geoms)
road=gpd.read_file(W/'roads.geojson').to_crs(3826);samples={}
for _,r in road.iterrows():
 if r['class'] in ['motorway','trunk']:continue
 for line in ([r.geometry] if r.geometry.geom_type=='LineString' else getattr(r.geometry,'geoms',[])):
  if line.geom_type!='LineString':continue
  for d in np.arange(0,line.length,20):
   p=line.interpolate(d)
   if not 10<center.distance(p)<=300:continue
   if any(geoms[j].covers(p) for j in tree.query(p)):continue
   key=(round(p.x/5),round(p.y/5));samples[key]=p
pts=list(samples.values());assert len(pts)>30
coords=list(poly.exterior.coords);edges=[]
for a,c in zip(coords,coords[1:]):
 v=np.array(c)-a;length=np.linalg.norm(v)
 if length<10:continue
 u=v/length;n=np.array([u[1],-u[0]]);mid=(np.array(a)+c)/2
 if poly.contains(Point(mid+n)):n=-n
 edges.append((length,mid,u,n))
edges.sort(key=lambda e:-e[0]);chosen=[edges[0]]
chosen.append(next(e for e in edges[1:] if np.dot(e[3],chosen[0][3])<.3))
toLL=Transformer.from_crs(3826,4326,always_xy=True)
features=[]
for m in model:
 ll=gpd.GeoSeries([m['geom']],crs=3826).to_crs(4326).iloc[0]
 features.append({'type':'Feature','geometry':mapping(ll),'properties':{k:m[k] for k in ['id','base','top','method']}})
(W/'buildings.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features}))
pointfeatures=[]
for i,p in enumerate(pts):
 angle=math.atan2(p.y-center.y,p.x-center.x);zone=0 if angle>math.pi/6 and angle<5*math.pi/6 else (1 if p.x>=center.x else 2)
 pointfeatures.append({'type':'Feature','geometry':mapping(Point(*toLL.transform(p.x,p.y))),'properties':{'i':i,'zone':zone}})
(W/'samples.geojson').write_text(json.dumps({'type':'FeatureCollection','features':pointfeatures}))
res={};faces=[];heights=[5,10,15,20,30];unknowns=[6,15,30]
for fi,(_,mid,u,n) in enumerate(chosen):
 mid=mid+n*.3 # Mount just outside the exterior face.
 facepts=[mid-u*3,mid+u*3,mid+u*3+n*.25,mid-u*3+n*.25,mid-u*3]
 ll=[toLL.transform(*p) for p in facepts];bearing=(math.degrees(math.atan2(n[0],n[1]))+360)%360
 faces.append({'id':fi,'label':f'外牆 {chr(65+fi)} · 朝向 {round(bearing)}°','normal_bearing':bearing,'polygon':{'type':'Polygon','coordinates':[ll]},'center':toLL.transform(*mid)})
 # 5 target samples across a 6m x 3m hypothetical board.
 targets=[(mid,0),(mid-u*3,-1.5),(mid+u*3,-1.5),(mid-u*3,1.5),(mid+u*3,1.5)]
 caches=[]
 for p in pts:
  delta=np.array([p.x,p.y])-mid;dist=np.linalg.norm(delta);front=np.dot(delta,n)/dist
  paths=[]
  for target,zoff in targets:
   ray=LineString([(p.x,p.y),target]);hits=[]
   for j in tree.query(ray,predicate='intersects'):
    intersection=ray.intersection(geoms[j]);coords2=[]
    def collect(g):
     if hasattr(g,'geoms'):
      for part in g.geoms:collect(part)
     elif not g.is_empty:coords2.extend(list(g.coords))
    collect(intersection)
    if coords2:
     ts=[ray.project(Point(c))/ray.length for c in coords2];hits.append((int(j),min(ts),max(ts)))
   paths.append((zoff,hits))
  caches.append((dist,front,paths))
 for h in heights:
  for unknown in unknowns:
   values=[]
   for dist,front,paths in caches:
    visible=0
    if dist<=300 and front>=.5 and math.degrees(math.atan2(h-1.6,dist))<=45:
     for zoff,hits in paths:
      end=h+zoff;blocked=False
      for j,lo,hi in hits:
       m=model[j];top=m['top'] if m['top'] is not None else m['base']+unknown
       z1=1.6+(end-1.6)*lo;z2=1.6+(end-1.6)*hi
       if min(z1,z2)<=top and max(z1,z2)>=m['base']:blocked=True;break
      if not blocked:visible+=1
    values.append(visible)
   res[f'{fi}-{h}-{unknown}']=values
 print('face complete',fi,flush=True)
meta={'release':'2026-10-21.0','host_id':str(host.id),'host_name':'信義經貿大樓','host_height':float(host.height),'center':toLL.transform(center.x,center.y),'sample_count':len(pts),'model_counts':{k:sum(m['method']==k for m in model) for k in ['height','floors','unknown']},'faces':faces,'heights':heights,'unknowns':unknowns,'zone_names':['北側街段','東南側街段','西南側街段'],'zone_counts':[sum(f['properties']['zone']==z for f in pointfeatures) for z in range(3)],'board_size_m':[6,3],'observer_height_m':1.6,'max_range_m':300,'max_off_normal_deg':60,'max_elevation_deg':45,'seconds':round(time.time()-start,2),'sources_bbox':[121.557,25.027,121.573,25.043]}
assert all(len(v)==len(pts) and all(0<=x<=5 for x in v) for v in res.values())
assert len({tuple(v) for v in res.values()})>1
(W/'analysis.json').write_text(json.dumps({'meta':meta,'results':res}));(O/'evidence/execution.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False))
