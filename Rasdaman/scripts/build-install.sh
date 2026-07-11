#!/usr/bin/env bash
# build 階段執行：啟動 postgres → 建 petascopedb → 從本地 .deb 安裝 rasdaman
# （rasdaman 的安裝器會在安裝當下完成 RASBASE/Petascope 準備，需要 postgres 在跑 + wget）
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

PGVER="$(ls /etc/postgresql)"
echo "### [build] 啟動 PostgreSQL $PGVER"
pg_ctlcluster "$PGVER" main start
for i in $(seq 1 30); do pg_isready -q && break; sleep 1; done
pg_isready

echo "### [build] 建立 petascope 角色與資料庫（若不存在）"
su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='petauser'\"" | grep -q 1 \
  || su postgres -c "psql -c \"CREATE USER petauser WITH PASSWORD 'petapass';\""
su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='petascopedb'\"" | grep -q 1 \
  || su postgres -c "psql -c \"CREATE DATABASE petascopedb OWNER petauser;\""

echo "### [build] 從本地 .deb 安裝 rasdaman（相依走 Ubuntu 鏡像）"
apt-get update
apt-get install -y /debs/rasdaman_*.deb
rm -rf /var/lib/apt/lists/*

echo "### [build] 停掉安裝器啟動的服務（runtime 由 entrypoint 重新拉起）"
stop_rasdaman.sh 2>/dev/null || /etc/init.d/rasdaman stop 2>/dev/null || true
pg_ctlcluster "$PGVER" main stop || true
echo "### [build] 完成"
