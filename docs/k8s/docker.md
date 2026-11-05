# Docker

Docker 是一个开源的容器化引擎。 可以帮助开发者将应用程序以及它运行所需的所有依赖（环境、库、配置文件），打包成一个轻量级、可移植的“集装箱”（Container），从而实现“一次构建，处处运行”。其通过容器化的应用环境，解决了环境管理的复杂问题，让应用的部署和运维变得更加简单和高效。。

- [x] 一次构建到处运行
- [x] 更强的一致性
- [x] 可移植性强
- [x] 提升资源利用率
- [x] 创建和启动速度快
- [x] 更细粒度的隔离性

## 安装手册

> [官网](https://docs.docker.com/engine/install/): `https://docs.docker.com/engine/install/`

=== "在线安装"

    1. 在安装 Docker Engine 之前，需要卸载任何冲突的软件包,然后安装依赖
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
    apt list --all-versions docker-ce
    VERSION_STRING=5:29.8.2-1~ubuntu.24.04~noble
    sudo apt install docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin
    ```
    5. 配置docker
    ```
    mkdir /etc/docker
    tee /etc/docker/daemon.json << EOF
    {
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "10m",
        "max-file": "3"
      },
      "data-root": "/data/docker"
    }
    EOF
    mkdir -p /etc/containerd
    containerd config default | sudo tee /etc/containerd/config.toml
    sed -i "s@root = '/var/lib/containerd'@root = '/data/containerd'@g" /etc/containerd/config.toml
    ```
    6. 启动并设置服务开机自启动
    ```
    sudo systemctl stop docker docker.socket containerd
    sudo systemctl enable docker --now
    ```
    7. 迁移已有数据
    ```
    sudo systemctl stop docker docker.socket containerd
    sudo rsync -aP /var/lib/containerd/ /data/containerd/
    sudo systemctl start docker 
    ```



=== "离线安装"
    
    1. 下载二进制文件
    ```
    wget https://download.docker.com/linux/static/stable/aarch64/docker-29.8.0.tgz
    ```
    2. 解压并移动到可执行文件路径上
    ```shell
    tar -xf docker-29.8.0.tgz
    cp docker/* /usr/bin/
    ```
    3. 配置docker
    ```shell
    mkdir /etc/docker
    cat > /etc/docker/daemon.json << EOF
    {
        "exec-opts": ["native.cgroupdriver=systemd"],
        "max-concurrent-downloads": 10,
        "max-concurrent-uploads": 10,
        "log-driver": "json-file",
        "storage-driver": "overlay2",
        "data-root": "/data/docker",
        "log-opts":{
            "max-size": "300m",
            "max-file": "2" 
        },
        "registry-mirrors": ["https://docker.m.daocloud.io"],
        "live-restore": true
    }
    EOF
    ```
    
    4. 提供启动脚本并启动
    ```shell
    cat > /usr/lib/systemd/system/docker.service << EOF
    [Unit]
    Description=Docker Application Container Engine
    Documentation=https://docs.docker.com
    After=network-online.target firewalld.service
    Wants=network-online.target
    [Service]
    Type=notify
    ExecStart=/usr/bin/dockerd
    ExecReload=/bin/kill -s HUP $MAINPID
    LimitNOFILE=infinity
    LimitNPROC=infinity
    LimitCORE=infinity
    TimeoutStartSec=0
    Delegate=yes
    KillMode=process
    Restart=on-failure
    StartLimitBurst=3
    StartLimitInterval=60s
    [Install]
    WantedBy=multi-user.target
    EOF
    
    systemctl enable docker --now
    ```

=== "卸载"

    1. 卸载 Docker Engine、CLI、containerd 和 Docker Compose 软件包
    ```shell
    sudo apt purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras
    ```
    2. 主机上的镜像、容器、卷或自定义配置文件不会自动删除。要删除所有镜像、容器和卷
    ```
    sudo rm -rf /data/docker
    sudo rm -rf /data/containerd
    ```
    3. 删除源列表和密钥环
    ```
    sudo rm /etc/apt/sources.list.d/docker.sources
    sudo rm /etc/apt/keyrings/docker.asc
    ```
