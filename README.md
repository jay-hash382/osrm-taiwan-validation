# Taiwan OSRM validation

這是「前路氣象」的一般道路導航獨立驗證環境。它不依賴、也不修改 App、既有後端或一般道路圖磚。

## 驗證目標

- 使用 Geofabrik 的完整臺灣 OpenStreetMap PBF。
- 使用 OSRM 官方 `car.lua` 建立 MLD 汽車路網。
- 驗證國道、一般道路、交流道、住宅道路與可通行 service 道路。
- 記錄路線結果、端點吸附距離、回應時間與資料版本。
- 對過遠吸附、無路線及不合理路線明確失敗，不把錯誤路線當成功。

目前階段只建立及驗證獨立 OSRM，不接入 App 或既有後端。

## 資料與版本

- OSM extract: `https://download.geofabrik.de/asia/taiwan-latest.osm.pbf`
- OSRM image: `ghcr.io/project-osrm/osrm-backend:latest`（每次報告會記錄實際 image digest）
- Algorithm: MLD
- Profile: OSRM 官方 `car.lua`

OSM 資料為 OpenStreetMap contributors 提供，Geofabrik 發布，依 ODbL 使用。

## 最簡單的執行方式

到 GitHub repository 的 **Actions → Validate Taiwan OSRM → Run workflow**。工作流程會：

1. 下載最新臺灣 PBF。
2. 建立 OSRM MLD graph。
3. 啟動獨立 OSRM server。
4. 執行 `tests/cases.json` 內的代表性路線。
5. 執行 `tests/quality-cases.json` 的路線品質稽核。
6. 上傳 JSON 報告及可視化用 GeoJSON artifact。

每次執行都使用暫時 runner；建圖檔不會提交到 Git，也不會影響任何正式服務。

## 本機執行

需求：Docker Desktop、PowerShell 7（Windows）或 Bash、約 5 GB 可用磁碟空間及至少 4 GB 記憶體；建圖時建議 8 GB 以上。

PowerShell：

```powershell
./scripts/build-and-run.ps1
python ./scripts/validate.py --base-url http://127.0.0.1:5000
```

Bash：

```bash
./scripts/build-and-run.sh
python3 ./scripts/validate.py --base-url http://127.0.0.1:5000
```

停止服務：

```powershell
docker stop osrm-taiwan-validation
```

## 判讀報告

每個案例會記錄：

- OSRM response code。
- 起終點吸附距離。
- 路線距離及時間。
- API 回應時間。
- 是否通過案例設定的距離與吸附門檻。

`nearest` 案例另外確認 service／住宅區等位置附近確實存在可供汽車吸附的路網。這只是第一層檢查；正式接入前仍需人工查看路線是否走入私人道路、停車場捷徑或錯誤方向。

品質稽核分成三種結果：

- `pass`：未超過目前的自動安全門檻。
- `review`：路線可用，但吸附距離、繞路比例或無名道路比例需要人工看 GeoJSON。
- `fail`：無路線、吸附超過 300 公尺、距離／幾何異常或速度資料不合理。

`review` 不會讓 Actions 失敗，因為它的目的就是標出需要人工判讀的案例；任何 `fail` 才會阻止流程通過。

端點規則詳見 [ENDPOINT_POLICY.md](ENDPOINT_POLICY.md)。Actions 亦會以 1、4、8、16 個並行請求測試初次規劃與偏離後重新規劃，記錄 p50、p95、p99、錯誤率、吞吐量與容器記憶體快照。
