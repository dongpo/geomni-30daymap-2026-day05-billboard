from pathlib import Path
import sys,json,time
import duckdb
O=Path(__file__).resolve().parents[1];c=duckdb.connect();c.execute('INSTALL spatial; INSTALL httpfs');c.execute("LOAD spatial; LOAD httpfs; SET geometry_always_xy=true; SET s3_region='us-west-2'; SET threads=4; SET memory_limit='2GB'")
base='s3://overturemaps-us-west-2/release/2026-10-21.0/theme=buildings/type='
for typ in ['building','building_part']:
 sql=f"SELECT * FROM read_parquet('{base}{typ}/*',hive_partitioning=true) WHERE bbox.xmin<121.573 AND bbox.xmax>121.557 AND bbox.ymin<25.043 AND bbox.ymax>25.027"
 (O/'evidence'/f'{typ}.sql').write_text(sql);t=time.time();print('START',typ,flush=True)
 c.execute('CREATE OR REPLACE TABLE b AS '+(f"SELECT * FROM read_parquet('{O}/{typ}.parquet')" if (O/f'{typ}.parquet').exists() else sql))
 c.execute(f"COPY b TO '{O}/{typ}.parquet' (FORMAT PARQUET)")
 c.execute(f"COPY (SELECT id, height, num_floors, min_height, geometry, CAST(sources AS JSON) AS sources FROM b) TO '{O}/{typ}.geojson' (FORMAT GDAL, DRIVER 'GeoJSON')")
 print(typ,c.execute('SELECT count(*),count(height),count(num_floors) FROM b').fetchall(),time.time()-t,flush=True)
