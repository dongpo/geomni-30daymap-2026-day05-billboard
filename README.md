# Geomni｜廣告掛得越高，真的越多人看見？

2026 #30DayMapChallenge Day 05 — Senses: Sight。信義區假想看板可視性實驗，2026-11-04 製作，待本人審稿。取代先前 Day05 山區視域選題，保留舊成果不覆寫。

[開啟互動地圖](https://dongpo.github.io/geomni-30daymap-2026-day05-billboard/) · [Facebook 草稿](facebook-draft.txt) · [分享 PNG](day05-billboard.png) · [替代文字](alt-text.txt)

## 可以操作什麼

信義經貿大樓兩面外牆、看板中心高度 5/10/15/20/30 m、未知建物高度 6/15/30 m，及三區相對人流權重 0–500。可保存完整 A 情境，再調整 B 比較。看板為假想設定，不代表現場設置或地主同意。

人流完全是假設，沒有信令或現場觀測；「加權可視指數」不是不重複人數、觀看率、廣告收入或報價。所有權重為零時指數無定義。

## 真實資料與處理

- Overture Maps 2026-10-21.0 Buildings：範圍 121.557,25.027–121.573,25.043；2,070 棟建物與 799 個分部。原始欄位、來源與識別碼保留於 `building*.parquet`，另交付 GeoJSON 摘要。
- DuckDB Spatial/httpfs 以 bbox 對雲端 GeoParquet 篩選；查詢在 `evidence/building*.sql`。這不是完整下載全球建物。
- 以 EPSG:3826 公尺座標分析。可用 building_part 取代其母建物，排除地下圖徵，取宿主中心 550 m 內的幾何體作遮蔽模型。904 個柱體中，22 個使用 height，523 個使用 num_floors × 3 m，359 個由情境指定高度。
- 簡化柱體底部用 min_height（缺值為 0），頂部用底部加 height／推估高度。未建模屋頂形狀、樹木、車輛與地形；有分部的母建物整體移除，分部不完整時可能漏算遮蔽。
- 道路使用本系列 Day02 已擷取的同版 Overture Transportation，裁切至上述 bbox；原查詢存於 `evidence/day02-roads-original.sql`。重跑遮蔽直接使用交付的 `web/roads.geojson`，不需要舊專案。道路摘錄只有 id/name/class，未保留逐筆來源欄位，不能用來推論道路來源提供者。
- 道路每 20 m 採樣，以 5 m 網格去重，排除 motorway/trunk、建築內點及距宿主中心 10 m 內／300 m 外點，共 786 點。這些是道路中心線代理點，並未查證人行道或行人通行權。

## 可視運算與指標

看板 6 × 3 m，中心及四角共五個目標點；觀測眼高 1.6 m。每條射線和建築平面相交，求交段沿射線的高程，再與柱體底頂高度比較。STRtree 限縮候選建物。距看板中心限 300 m、偏離外牆正面 ≤60°、向上仰角 ≤45°，門檻均為實驗假設。

v_i 是第 i 個道路點看得到的目標數（0–5）。每區先計算 mean(v_i/5)，再用使用者設定的區域權重 w_z 加權：`score = 100 × Σ(w_z × mean_z) / Σw_z`。區域由宿主中心方位分成北、東南、西南，每區內人流假設均勻；不是行政界或觀測人流區。固定母體中位於看板 300 m 外的點記為不可視。

五點採樣不能保證整面看板皆可視。射線遇不連續交段時目前取首末交點的區間包絡，對凹形／多部件幾何可能保守高估遮蔽。幾何可視也不代表文字可讀或人真的會注意看板。

## 架構與執行

DuckDB 範圍查詢 → GeoParquet → GeoPandas/Shapely 遮蔽預算 → 30 組 JSON 結果 → MapLibre 3D 顯示。人流加權由瀏覽器即時計算；高度切換讀取預先計算情境，並非瀏覽器現場射線追蹤，也不支援任意點／連續高度。純靜態 GitHub Pages 可運作，無分析後端或 API 金鑰。

已完成：資料擷取、30 組分析、真實地圖 PNG、互動頁、A/B 比較、零權重處理、情境不變性檢核。尚未完成：現地驗證、真實人流接入、LOD2／地形模型、商業效益校準。

```sh
python3 -m pip install -r requirements.txt
python3 scripts/build.py
python3 scripts/validate.py
# 設定任一可用繁體中文字型的實際路徑
CJK_FONT=/path/to/chinese-font.otf python3 scripts/render.py
python3 -m http.server 8776 --directory web
```

分析重跑只需交付的 Parquet 與 roads.geojson；`scripts/acquire.py` 可重讀建物快取，移走快取後會向固定發布 S3 查詢（需網路與 DuckDB 擴充）。程式環境版本列於 requirements.txt；執行時間、參數、模型數量在 evidence/execution.json；資料 SHA256 在 evidence/manifest.json。

驗證涵蓋 30 組輸出長度與範圍，以及十組外牆／看板高度組合中，增加未知障礙物高度不會提高可視性。瀏覽器已實測滑桿、外牆、未知高度、保存 A、零權重及重設。這些檢查不等於模型實地精度驗證。

## 來源、年份、授權

- [官方 2026 主題](https://30daymapchallenge.com/)：11/5 Senses: Sight，2026-11-04 核對。
- [Overture 建物文件](https://docs.overturemaps.org/guides/buildings/)；[Transportation](https://docs.overturemaps.org/guides/transportation/)；發布 2026-10-21.0。發布日不代表每筆資料的觀測日，逐筆來源見 Parquet。
- 建物及道路資料、衍生地理資料：© Overture Maps Foundation / OpenStreetMap contributors，依 [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) 提供。原始資料來源標示保留，個別上游歸屬見 sources。
- [DuckDB Spatial](https://duckdb.org/docs/stable/core_extensions/spatial/overview)、[Shapely](https://shapely.readthedocs.io/)、[MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/)；MapLibre 本機隨附版本 5.24，授權見 web/vendor/MAPLIBRE-LICENSE.txt。
- 靈感：[PLATEAU 戶外廣告案例](https://www.mlit.go.jp/plateau/use-case/uc22-004/)（2022）。本作未使用該案的人流或 LOD2，沒有重現商業定價模型。

AI 協助程式、製圖與文稿。僅供本人審核；未自動發 Facebook。
