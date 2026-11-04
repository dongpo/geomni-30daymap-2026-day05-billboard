from pathlib import Path
import os,json
O=Path(__file__).resolve().parents[1];os.environ['MPLCONFIGDIR']=str(O/'evidence/mpl-cache')
import geopandas as gpd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from pyproj import Transformer
D=json.load(open(O/'web/analysis.json'));m=D['meta'];b=gpd.read_file(O/'web/buildings.geojson').to_crs(3826);pts=gpd.read_file(O/'web/samples.geojson').to_crs(3826);roads=gpd.read_file(O/'web/roads.geojson').to_crs(3826);x,y=Transformer.from_crs(4326,3826,always_xy=True).transform(*m['center']);font=FontProperties(fname=os.environ.get('CJK_FONT', '/System/Library/Fonts/PingFang.ttc'));bg='#0b1926';ink='#edf6f2';mut='#b0c5ce'
f=plt.figure(figsize=(8,10),dpi=200,facecolor=bg)
def text(x,y,s,size=12,c=ink,**kw):f.text(x,y,s,fontproperties=font,fontsize=size,color=c,**kw)
text(.06,.95,'Geomni / GIS FIELD NOTES                                      05 / 30',12,'#67d8c2');text(.06,.895,'廣告掛得越高，真的越多人看見？',22);text(.06,.852,'2026.11.05 · SENSES: SIGHT · OVERTURE × 3D',12,'#efbf72');text(.06,.81,'信義區假想看板｜同一外牆與人流假設｜比較 20 m 與 30 m',11)
for i,h in enumerate([20,30]):
 ax=f.add_axes([.05+i*.48,.37,.42,.40],facecolor=bg);b.plot(ax=ax,color='#2a4053',edgecolor='#6a7b86',linewidth=.25);roads.plot(ax=ax,color='#425d6e',linewidth=.5)
 v=np.array(D['results'][f'0-{h}-15']);colors=np.where(v==5,'#61d6be',np.where(v>0,'#efc479','#778997'));ax.scatter(pts.geometry.x,pts.geometry.y,c=colors,s=6,linewidth=0)
 bx,by=Transformer.from_crs(4326,3826,always_xy=True).transform(*m['faces'][0]['center']);ax.scatter([bx],[by],marker='*',s=110,c='#ffbf52',edgecolor=bg,zorder=8);ax.set_xlim(x-320,x+320);ax.set_ylim(y-320,y+320);ax.set_aspect('equal');ax.axis('off');ax.set_title(f'{h} m',color=ink,fontsize=18);ax.text(.93,.95,'N ↑',transform=ax.transAxes,color=ink,ha='right',fontsize=10);ax.plot([x-270,x-170],[y-270]*2,c=ink,lw=2);ax.text(x-220,y-245,'100 m',color=ink,ha='center',fontsize=8)
 score=np.mean([(v[pts.zone==z]/5).mean() for z in range(3)])*100;text(.07+i*.48,.35,f'加權可視指數 {score:.2f} / 100',12);text(.07+i*.48,.32,f'至少部分可視：{int((v>0).sum())} / {len(v)} 點',10,mut)
text(.06,.266,'青綠：5 點皆可視　暖金：部分可視　灰：遮蔽／角度不符',10,'#67d8c2');text(.06,.22,'兩圖人流權重均為 100 : 100 : 100，非實測人流。\n看板 6 × 3 m；行人眼高 1.6 m；未知建物假設 15 m。',10,mut,linespacing=1.8);text(.06,.15,'看得更高，不必然提高此模型指數：仰角與街道分布也有影響。\n30 m 情境的細微差異受採樣與假設影響，並非價格或效益驗證。',10,mut,linespacing=1.8);text(.06,.075,'© Overture Maps / OpenStreetMap contributors · ODbL · 2026-10-21.0\n簡化建築柱體、平坦地面；高度缺值與樓層推估詳見互動頁。',8,mut,linespacing=1.6);text(.06,.025,'#30DayMapChallenge · Geomni · AI-assisted · 待審稿',9,mut);f.savefig(O/'day05-billboard.png')
