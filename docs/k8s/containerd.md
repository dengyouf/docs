# Containerd

Containerd 是一个行业标准的容器运行时环境，注重简洁性、健壮性和可移植性。它以守护进程的形式支持 Linux 和 Windows 系统，能够管理宿主系统容器的完整生命周期：镜像传输和存储、容器执行和监控、底层存储和网络连接等。

## 安装手册

> [官网](https://containerd.io/docs/2.4/getting-started/): `https://containerd.io/docs/2.4/getting-started/`

=== "在线安装"


    1. 卸载任何冲突的软件包,然后安装依赖
    ```
    sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc | cut -f1)
    sudo apt install -y apt-transport-https ca-certificates curl gnupg software-properties-common
    ```
    2. 下载并保存密钥
    ```
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://mirrors.huaweicloud.com/docker-ce/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    ```
    3. 配置DEB822格式的源文件，添加软件仓库
    ```
    tee /etc/apt/sources.list.d/docker.sources << EOF
    Types: deb
    URIs: https://mirrors.huaweicloud.com/docker-ce/linux/ubuntu
    Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
    Components: stable
    Signed-By: /etc/apt/keyrings/docker.asc
    EOF
    ```
    4. 更新索引文件并安装指定版本
    ```
    apt update
    apt list --all-versions containerd
    VERSION_STRING=2.2.1-0ubuntu1~24.04.4
    sudo apt install -y containerd=$VERSION_STRING
    ```

## 配置代理

```
mkdir -p /etc/systemd/system/containerd.service.d
cat > /etc/systemd/system/containerd.service.d/http-proxy.conf << 'EOF'
[Service]
Environment="HTTP_PROXY=http://192.168.122.1:7897"
Environment="HTTP_PROXY=http://192.168.122.1:7897"
Environment="NO_PROXY=localhost,127.0.0.1,10.244.0.0/16,10.96.0.0/12,.svc,.cluster.local,k8s-vip,*.devops.io"
EOF
systemctl daemon-reload
systemctl restart containerd

systemctl show containerd --property=Environment
Environment=HTTP_PROXY=http://192.168.122.1:7897 "NO_PROXY=localhost,127.0.0.1,10.244.0.0/16,10.96.0.0/12,.svc,.cluster.local,k8s-vip,*.devops.io"
curl -x http://192.168.122.1:7897 -I https://registry-1.docker.io/v2/ --connect-timeout 5
HTTP/1.1 200 Connection established

HTTP/2 401 
date: Sat, 21 Nov 2026 07:16:31 GMT
content-type: application/json
content-length: 87
docker-distribution-api-version: registry/2.0
www-authenticate: Bearer realm="https://auth.docker.io/token",service="registry.docker.io"
x-ratelimit-limit: 1500;w=60
ratelimit-limit: 1500;w=60
x-ratelimit-remaining: 1490;w=60
ratelimit-remaining: 1490;w=60
strict-transport-security: max-age=31536000
```

