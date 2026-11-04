CREATE OR REPLACE TABLE roads AS
SELECT id,names.primary AS name,class,subclass,version,geometry,bbox, sources
FROM read_parquet('s3://overturemaps-us-west-2/release/2026-10-21.0/theme=transportation/type=segment/*',hive_partitioning=true)
WHERE subtype='road' AND bbox.xmin <= 121.95 AND bbox.xmax >= 120.80
 AND bbox.ymin <= 25.35 AND bbox.ymax >= 24.55
 AND ST_Intersects(geometry,ST_MakeEnvelope(120.80,24.55,121.95,25.35));
COPY roads TO 'outputs/v2/data/north-taiwan-roads.parquet' (FORMAT PARQUET);
CREATE OR REPLACE TABLE roads_clipped AS SELECT id,name,class,
 ST_Intersection(geometry,ST_MakeEnvelope(120.80,24.55,121.95,25.35)) AS geometry FROM roads;
COPY roads_clipped TO 'outputs/v2/data/north-taiwan-roads.geojson' (FORMAT GDAL,DRIVER 'GeoJSON');
COPY (SELECT class,COUNT(*) AS segments,
 SUM(ST_Length(ST_Transform(geometry,'EPSG:4326','EPSG:3826',always_xy:=true)))/1000 AS clipped_geometry_km
 FROM roads_clipped GROUP BY class ORDER BY segments DESC) TO 'outputs/v2/evidence/road-summary.csv' (HEADER);