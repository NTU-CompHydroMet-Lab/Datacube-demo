# rasdaman Community（all-in-one）：rasdaman + Petascope + SECORE + PostgreSQL
# 從本地快取的 .deb 安裝（build 時用 --volume 掛 NAS 快取到 /debs）：
#   podman build --volume <NAS>/rasdaman/cache:/debs:ro -t localhost/rasdaman:latest .
FROM docker.io/library/ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
ENV RMANHOME=/opt/rasdaman
ENV PATH=/opt/rasdaman/bin:$PATH

# 執行期/安裝器需要的工具：wget（安裝器健康檢查必需）、postgresql（rasdaman 後端）等
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates wget curl sudo python3 netcat-openbsd postgresql \
    && rm -rf /var/lib/apt/lists/*

# 安裝 rasdaman（postgres 先起、建 petascopedb、再從本地 .deb 安裝）
COPY scripts/build-install.sh /tmp/build-install.sh
RUN bash /tmp/build-install.sh && rm -f /tmp/build-install.sh

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Petascope OGC 服務（WCS/WCPS/WMS）；rasmgr 7001 僅容器內部
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
