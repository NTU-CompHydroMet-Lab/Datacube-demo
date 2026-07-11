#!/usr/bin/env bash
# 容器啟動：起 postgres → 起 rasdaman + Petascope，並保持前景
set -uo pipefail
export RMANHOME=/opt/rasdaman
export PATH="$RMANHOME/bin:$PATH"

PGVER="$(ls /etc/postgresql)"
echo "[entrypoint] 啟動 PostgreSQL $PGVER ..."
pg_ctlcluster "$PGVER" main start
for i in $(seq 1 30); do pg_isready -q && break; sleep 1; done
pg_isready && echo "[entrypoint] postgres ready ✓"

echo "[entrypoint] 啟動 rasdaman + Petascope (port 8080) ..."
start_rasdaman.sh || /etc/init.d/rasdaman start || true

echo "[entrypoint] 服務已拉起；Petascope: http://127.0.0.1:8080/rasdaman/ows (需帳密 rasadmin:rasadmin)"
echo "[entrypoint] tail 日誌中 (Ctrl-C 停止容器)"
# 優雅關閉：收到 SIGTERM 時停服務
term() { echo "[entrypoint] 停止中..."; stop_rasdaman.sh 2>/dev/null || true; pg_ctlcluster "$PGVER" main stop || true; exit 0; }
trap term SIGTERM SIGINT

# 保持前景並輸出日誌
tail -F "$RMANHOME"/log/*.log 2>/dev/null &
wait $!
