# Kubeadm 安装 Kubernetes v1.35.7(Containerd)
## 主机环境准备
使用Kubeadm快速部署Kubernetes集群，操作系统为Ubuntu 24.04.2 LTS(noble)，用到的各相关程序版本如下:

- Kubernetes: v1.35.7
- Contianerd: v2.2.1
- Cilium: v1.20.3

| 主机名          | IP            | 角色     |
|--------------|---------------|--------|
| k8s-master01 | 192.168.122.11 | k8s-master01 |
| k8s-worker01 | 192.168.122.21 | k8s-worker01 |
| k8s-worker02 | 192.168.122.22 | k8s-worker02 |
| k8s-worker03 | 192.168.122.23 | k8s-worker03 |

### 1.配置国内源

- [Apt源码](https://developer.aliyun.com/mirror/ubuntu?spm=a2c6h.13651102.0.0.3e221b11e0gYK2)

```shell
cat > /etc/apt/sources.list.d/ubuntu.list << 'EOF'
deb https://mirrors.aliyun.com/ubuntu/ noble main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ noble main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ noble-security main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ noble-security main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ noble-updates main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ noble-updates main restricted universe multiverse

# deb https://mirrors.aliyun.com/ubuntu/ noble-proposed main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ noble-proposed main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ noble-backports main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ noble-backports main restricted universe multiverse
EOF
```

- [Docker源](https://developer.aliyun.com/mirror/docker-ce?spm=a2c6h.13651102.0.0.3e221b11e0gYK2)

```shell
# step 1: 安装必要的一些系统工具
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

# step 2: 信任 Docker 的 GPG 公钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Step 3: 写入软件源信息
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Step 4: 安装Docker
sudo apt-get update
# 安装指定版本的Docker-CE:
# Step 1: 查找Docker-CE的版本:
# apt-cache madison docker-ce
#   docker-ce | 17.03.1~ce-0~ubuntu-xenial | https://mirrors.aliyun.com/docker-ce/linux/ubuntu xenial/stable amd64 Packages
#   docker-ce | 17.03.0~ce-0~ubuntu-xenial | https://mirrors.aliyun.com/docker-ce/linux/ubuntu xenial/stable amd64 Packages
# Step 2: 安装指定版本的Docker-CE: (VERSION例如上面的17.03.1~ce-0~ubuntu-xenial)
# sudo apt-get -y install docker-ce=[VERSION]
```

- [Kubernetes源](https://developer.aliyun.com/mirror/kubernetes?spm=a2c6h.13651102.0.0.3e221b11e0gYK2)

```shell
apt-get update && apt-get install -y apt-transport-https
curl -fsSL https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.35/deb/Release.key |
    gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.35/deb/ /" |
    tee /etc/apt/sources.list.d/kubernetes.list
apt-get update
```

### 2.主机名解析

```shell
cat >> /etc/hosts << 'EOF'
192.168.122.11 k8s-master01
192.168.122.21 k8s-worker01
192.168.122.22 k8s-worker02
192.168.122.23 k8s-worker03
# k8s-vip 预留后期扩展高可用集群
192.168.122.11 k8s-vip
EOF
```

### 3.关闭防火墙和selinux(Ubuntu不用管SELinux)

```shell
ufw disable
```

### 4.关闭swap分区
```shell
sed -i 's/.*swap.*/#&/' /etc/fstab
swapoff -a && sysctl -w vm.swappiness=0
systemctl  mask swap.target
```

### 5.时区跟时间同步

```shell
timedatectl  set-timezone Asia/Shanghai
apt install -y chrony
cat  > /etc/chrony/chrony.conf << 'EOF'
pool ntp.aliyun.com       iburst maxsources 4
keyfile /etc/chrony/chrony.keys
driftfile /var/lib/chrony/chrony.drift
logdir /var/log/chrony
maxupdateskew 100.0
rtcsync
makestep 1 3
EOF
systemctl restart chrony.service && systemctl  enable chrony.service
chronyc sources
MS Name/IP address         Stratum Poll Reach LastRx Last sample
===============================================================================
^* 203.107.6.88                  2   6     7     1  -4176us[ +806us] +/-   29ms
```

### 6.加载IPVS模块

```shell
apt install ipset ipvsadm -y
cat >> /etc/modules-load.d/k8s.conf << 'EOF'
br_netfilter
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack
nf_nat
overlay
vxlan
iptable_nat
xt_MASQUERADE
EOF
systemctl restart systemd-modules-load
lsmod | grep -E 'br_netfilter|ip_vs|nf_conntrack|overlay|vxlan'
```

### 7.内核参数优化

```shell
cat > /etc/sysctl.d/k8s.conf << 'EOF'
# 开启IPv4转发
net.ipv4.ip_forward = 1
# 允许桥接的流量进入iptables/netfilter
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
# 优化连接跟踪表大小，防止大规模连接爆掉
net.netfilter.nf_conntrack_max = 2310720
# TCP优化（缩短 TIME_WAIT，快速回收连接）
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 5
# 内存相关优化（防止OOM）
vm.swappiness = 0
vm.overcommit_memory = 1
vm.panic_on_oom = 0
# 文件句柄限制
fs.file-max = 52706963
# 网络层面优化
net.core.somaxconn = 32768
net.core.netdev_max_backlog = 16384
net.ipv4.tcp_max_syn_backlog = 16384
EOF
sysctl --system
cat >> /etc/security/limits.conf << 'EOF'
* soft nofile 1048576
* hard nofile 1048576
* soft nproc 1048576
* hard nproc 1048576
* soft memlock unlimited
* hard memlock unlimited
EOF
ulimit  -n 64435
ulimit  -s 10240
```

## 安装容器运行时

### 1.安装指定版本的容器运行时

```shell
apt-cache madison containerd
apt install -y containerd=2.2.1-0ubuntu1~24.04.4
```
### 2.配置contianerd

```shell
mkdir -pv /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
containerd config default | sudo tee /etc/containerd/config.toml
# 修改cgroup Driver为systemd
grep -E "SystemdCgroup|pause:|root = '(.*)'|config_path"  /etc/containerd/config.toml
sed -ri 's@SystemdCgroup = false@SystemdCgroup = true@' /etc/containerd/config.toml
# 更改sandbox_image
sed -ri 's@registry.k8s.io\/pause:3.10.1@registry.cn-hangzhou.aliyuncs.com\/google_containers\/pause:3.10.1@' /etc/containerd/config.toml
# 配置containerd 的镜像存储目录
sed -i "s@root = '/var/lib/containerd'@root = '/data/containerd'@g" /etc/containerd/config.toml
#
sed -i "s@config_path = '/etc/containerd/certs.d:/etc/docker/certs.d'@config_path = '\/etc\/containerd\/certs.d\/'@g" /etc/containerd/config.toml
```
```
# 配置修改的最终结果
grep -E "SystemdCgroup|pause:|root = '(.*)'|config_path"  /etc/containerd/config.toml
root = '/data/containerd'
      sandbox = 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.10.1'
      config_path = '/etc/containerd/certs.d/'
            SystemdCgroup = true
    plugin_config_path = '/etc/nri/conf.d'
    config_path = ''
```

### 3.配置加速器

!!! warning "如果镜像拉不下来，请检查代理的可用性"

```shell
# docker.io 镜像加速
mkdir -p /etc/containerd/certs.d/docker.io
cat > /etc/containerd/certs.d/docker.io/hosts.toml << 'EOF'
server = "https://registry-1.docker.io" # 源镜像地址
[host."https://***.xuanyuan.run"]
  capabilities = ["pull", "resolve"]
  skip_verify = false

[host."https://docker.1ms.run"]
  capabilities = ["pull","resolve"]

[host."https://docker.m.daocloud.io"] # 道客-镜像加速地址
  capabilities = ["pull","resolve"]

[host."https://dockerproxy.com"] # 镜像加速地址
  capabilities = ["pull", "resolve"]

[host."https://docker.mirrors.sjtug.sjtu.edu.cn"] # 上海交大-镜像加速地址
  capabilities = ["pull","resolve"]

[host."https://docker.mirrors.ustc.edu.cn"] # 中科大-镜像加速地址
  capabilities = ["pull","resolve"]

[host."https://docker.nju.edu.cn"] # 南京大学-镜像加速地址
  capabilities = ["pull","resolve"]

[host."https://registry-1.docker.io"]
  capabilities = ["pull","resolve","push"]
EOF

# registry.k8s.io 镜像加速
mkdir -p /etc/containerd/certs.d/registry.k8s.io
cat > /etc/containerd/certs.d/registry.k8s.io/hosts.toml << 'EOF'
server = "https://registry.k8s.io"

[host."https://k8s.m.daocloud.io"]
  capabilities = ["pull", "resolve", "push"]
EOF

# quay.io 镜像加速
mkdir -p /etc/containerd/certs.d/quay.io
cat > /etc/containerd/certs.d/quay.io/hosts.toml << 'EOF'
server = "https://quay.io"

[host."https://quay.m.daocloud.io"]
  capabilities = ["pull", "resolve", "push"]
EOF

# docker.elastic.co镜像加速
mkdir -p /etc/containerd/certs.d/docker.elastic.co
tee /etc/containerd/certs.d/docker.elastic.co/hosts.toml << 'EOF'
server = "https://docker.elastic.co"

[host."https://elastic.m.daocloud.io"]
  capabilities = ["pull", "resolve", "push"]
EOF
systemctl daemon-reload &&  systemctl restart containerd && systemctl enable containerd
```
### 4.安装crictl客户端

```shell
wget https://gh-proxy.org/https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.24.0/crictl-v1.24.0-linux-amd64.tar.gz
tar -zxvf crictl-v1.24.0-linux-amd64.tar.gz -C /usr/local/bin
cat > /etc/crictl.yaml <<EOF
runtime-endpoint: unix:///var/run/containerd/containerd.sock
image-endpoint: unix:///var/run/containerd/containerd.sock
timeout: 10
debug: false
pull-image-on-create: false
EOF
```

## 安装集群

### 1.安装kubeadm软件包

```shell
apt-cache madison kubeadm
VERSION="1.35.7-1.1"
apt install -y kubeadm=${VERSION} kubelet=${VERSION} kubectl=${VERSION} 
```

### 2.配置kubelet开机自启

```shell
systemctl enable --now kubelet
```

### 3.集群安装

#### 3.1.Master 节点初始化
```shell
# 提前拉取镜像
kubeadm config images pull --image-repository=registry.cn-hangzhou.aliyuncs.com/google_containers --kubernetes-version=1.30.7

kubeadm init --control-plane-endpoint k8s-vip \
        --kubernetes-version=v1.35.7 \
        --pod-network-cidr=10.244.0.0/16 \
        --service-cidr=10.96.0.0/12 \
        --token-ttl=0 \
        --upload-certs \
        --image-repository=registry.aliyuncs.com/google_containers \
        --skip-phases=addon/kube-proxy |tee kubeadm.log
[init] Using Kubernetes version: v1.35.7
[preflight] Running pre-flight checks
[preflight] Pulling images required for setting up a Kubernetes cluster
[preflight] This might take a minute or two, depending on the speed of your internet connection
[preflight] You can also perform this action beforehand using 'kubeadm config images pull'
[certs] Using certificateDir folder "/etc/kubernetes/pki"
[certs] Generating "ca" certificate and key
[certs] Generating "apiserver" certificate and key
[certs] apiserver serving cert is signed for DNS names [k8s-master01 k8s-vip kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local] and IPs [10.96.0.1 192.168.122.11]
[certs] Generating "apiserver-kubelet-client" certificate and key
[certs] Generating "front-proxy-ca" certificate and key
[certs] Generating "front-proxy-client" certificate and key
[certs] Generating "etcd/ca" certificate and key
[certs] Generating "etcd/server" certificate and key
[certs] etcd/server serving cert is signed for DNS names [k8s-master01 localhost] and IPs [192.168.122.11 127.0.0.1 ::1]
[certs] Generating "etcd/peer" certificate and key
[certs] etcd/peer serving cert is signed for DNS names [k8s-master01 localhost] and IPs [192.168.122.11 127.0.0.1 ::1]
[certs] Generating "etcd/healthcheck-client" certificate and key
[certs] Generating "apiserver-etcd-client" certificate and key
[certs] Generating "sa" key and public key
[kubeconfig] Using kubeconfig folder "/etc/kubernetes"
[kubeconfig] Writing "admin.conf" kubeconfig file
[kubeconfig] Writing "super-admin.conf" kubeconfig file
[kubeconfig] Writing "kubelet.conf" kubeconfig file
[kubeconfig] Writing "controller-manager.conf" kubeconfig file
[kubeconfig] Writing "scheduler.conf" kubeconfig file
[etcd] Creating static Pod manifest for local etcd in "/etc/kubernetes/manifests"
[control-plane] Using manifest folder "/etc/kubernetes/manifests"
[control-plane] Creating static Pod manifest for "kube-apiserver"
[control-plane] Creating static Pod manifest for "kube-controller-manager"
[control-plane] Creating static Pod manifest for "kube-scheduler"
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/instance-config.yaml"
[patches] Applied patch of type "application/strategic-merge-patch+json" to target "kubeletconfiguration"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Starting the kubelet
[wait-control-plane] Waiting for the kubelet to boot up the control plane as static Pods from directory "/etc/kubernetes/manifests"
[kubelet-check] Waiting for a healthy kubelet at http://127.0.0.1:10248/healthz. This can take up to 4m0s
[kubelet-check] The kubelet is healthy after 474.068µs
[control-plane-check] Waiting for healthy control plane components. This can take up to 4m0s
[control-plane-check] Checking kube-apiserver at https://192.168.122.11:6443/livez
[control-plane-check] Checking kube-controller-manager at https://127.0.0.1:10257/healthz
[control-plane-check] Checking kube-scheduler at https://127.0.0.1:10259/livez
[control-plane-check] kube-controller-manager is healthy after 5.794079ms
[control-plane-check] kube-scheduler is healthy after 8.432961ms
[control-plane-check] kube-apiserver is healthy after 1.501635925s
[upload-config] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[kubelet] Creating a ConfigMap "kubelet-config" in namespace kube-system with the configuration for the kubelets in the cluster
[upload-certs] Storing the certificates in Secret "kubeadm-certs" in the "kube-system" Namespace
[upload-certs] Using certificate key:
c3cef690ff255e9b07a80d5b7bf1141b0f3ae9e9bbf0ee1e2a678ba35012cf09
[mark-control-plane] Marking the node k8s-master01 as control-plane by adding the labels: [node-role.kubernetes.io/control-plane node.kubernetes.io/exclude-from-external-load-balancers]
[mark-control-plane] Marking the node k8s-master01 as control-plane by adding the taints [node-role.kubernetes.io/control-plane:NoSchedule]
[bootstrap-token] Using token: pm3xzg.1yp0895ym0ly683h
[bootstrap-token] Configuring bootstrap tokens, cluster-info ConfigMap, RBAC Roles
[bootstrap-token] Configured RBAC rules to allow Node Bootstrap tokens to get nodes
[bootstrap-token] Configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstrap-token] Configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstrap-token] Configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstrap-token] Configured RBAC rules to allow the API server kubelet client certificate to access the kubelet API
[bootstrap-token] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
[kubelet-finalize] Updating "/etc/kubernetes/kubelet.conf" to point to a rotatable kubelet client certificate and key
[addons] Applied essential addon: CoreDNS

Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

You can now join any number of control-plane nodes running the following command on each as root:

  kubeadm join k8s-vip:6443 --token pm3xzg.1yp0895ym0ly683h \
	--discovery-token-ca-cert-hash sha256:b903bfab90496f87bd77d73bdf75c727d61af2700e5d69d220ad8256d9a485f0 \
	--control-plane --certificate-key c3cef690ff255e9b07a80d5b7bf1141b0f3ae9e9bbf0ee1e2a678ba35012cf09

Please note that the certificate-key gives access to cluster sensitive data, keep it secret!
As a safeguard, uploaded-certs will be deleted in two hours; If necessary, you can use
"kubeadm init phase upload-certs --upload-certs" to reload certs afterward.

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join k8s-vip:6443 --token pm3xzg.1yp0895ym0ly683h \
	--discovery-token-ca-cert-hash sha256:b903bfab90496f87bd77d73bdf75c727d61af2700e5d69d220ad8256d9a485f0 
```

#### 3.2.配置kubectl命令

```shell
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl  get nodes
NAME           STATUS     ROLES           AGE    VERSION
k8s-master01   NotReady   control-plane   3m1s   v1.35.7
root@k8s-master01:~# kubectl  get pods -A
NAMESPACE     NAME                                   READY   STATUS    RESTARTS   AGE
kube-system   coredns-bbdc5fdf6-kb5qc                0/1     Pending   0          2m55s
kube-system   coredns-bbdc5fdf6-np7xp                0/1     Pending   0          2m55s
kube-system   etcd-k8s-master01                      1/1     Running   0          3m
kube-system   kube-apiserver-k8s-master01            1/1     Running   0          3m
kube-system   kube-controller-manager-k8s-master01   1/1     Running   0          3m
kube-system   kube-scheduler-k8s-master01            1/1     Running   0          3m2s
```
#### 3.3.部署网络插件Cilium

!!! info "[Kubernetes 兼容性](https://docs.cilium.io/en/stable/network/kubernetes/compatibility/)"

```shell
CILIUM_CLI_VERSION=v0.20.3
CLI_ARCH=amd64
curl -L --fail --remote-name-all https://gh-proxy.org/https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
cilium version
cilium-cli: v0.20.3 compiled with go1.27.3 on linux/amd64
cilium image (default): v1.20.3
cilium image (stable): unknown
cilium image (running): unknown. Unable to obtain cilium version. Reason: release: not found
```

???+ NOTE "网络模式"

    === "VXLAN 隧道模式 (Tunnel Mode)"

        它会在节点之间建立虚拟隧道。当 Pod 发送数据包到其他节点时，Cilium 会把原始数据包整个“封装”进一个 UDP 包里（就像装进信封），通过节点的物理网络发送过去，到达后再拆开。只要节点之间 IP 能通就行，不需要底层网络认识 Pod 的 IP。但封装/解封装会带来轻微的性能开销，并且因为加了包头，链路的有效 MTU 会变小（VXLAN 通常少 50 字节）

        ```
        cilium install --version 1.20.3\
            --set kubeProxyReplacement=true  \
            --set ipam.mode=kubernetes \
            --set routingMode=tunnel \
            --set tunnelProtocol=vxlan \
            --set ipam.operator.clusterPoolIPv4PodCIDRList=10.244.0.0/16 \
            --set ipam.Operator.ClusterPoolIPv4MaskSize=24   
        ```
    === "Native Routing 模式 (原生路由)"
        
        Cilium 直接把跨节点的 Pod 数据包交给 Linux 内核的路由子系统，由底层网络像转发普通主机流量一样去转发它，这种模式追求更高的性能，但对网络环境有明确要求。

        ```shell
        cilium install --version 1.20.3\
                --set kubeProxyReplacement=true \
                --set ipam.mode=kubernetes \
                --set routingMode=native \
                --set ipam.operator.clusterPoolIPv4PodCIDRList=10.244.0.0/16 \
                --set ipam.Operator.ClusterPoolIPv4MaskSize=24 \
                --set ipv4NativeRoutingCIDR=10.244.0.0/16 \
                --set autoDirectNodeRoutes=true
        ℹ️  Using Cilium version 1.20.3
        🔮 Auto-detected cluster name: kubernetes
        🔮 Auto-detected kube-proxy has not been installed
        ℹ️  Cilium will fully replace all functionalities of kube-proxy
        kubectl  get pod -A -w
        NAMESPACE     NAME                                   READY   STATUS    RESTARTS   AGE
        kube-system   cilium-envoy-8mxqh                     1/1     Running   0          2m38s
        kube-system   cilium-operator-6f5485bc7-2pvqw        1/1     Running   0          2m38s
        kube-system   cilium-rn8ct                           1/1     Running   0          2m38s
        kube-system   coredns-bbdc5fdf6-kb5qc                1/1     Running   0          42m
        kube-system   coredns-bbdc5fdf6-np7xp                1/1     Running   0          42m
        kube-system   etcd-k8s-master01                      1/1     Running   0          43m
        kube-system   kube-apiserver-k8s-master01            1/1     Running   0          43m
        kube-system   kube-controller-manager-k8s-master01   1/1     Running   0          43m
        kube-system   kube-scheduler-k8s-master01            1/1     Running   0          43m
        cilium status
            /¯¯\
        /¯¯\__/¯¯\    Cilium:             OK
        \__/¯¯\__/    Operator:           OK
        /¯¯\__/¯¯\    Envoy DaemonSet:    OK
        \__/¯¯\__/    Hubble Relay:       disabled
            \__/       ClusterMesh:        disabled

        DaemonSet              cilium                   Desired: 1, Ready: 1/1, Available: 1/1
        DaemonSet              cilium-envoy             Desired: 1, Ready: 1/1, Available: 1/1
        Deployment             cilium-operator          Desired: 1, Ready: 1/1, Available: 1/1
        Containers:            cilium                   Running: 1
                            cilium-envoy             Running: 1
                            cilium-operator          Running: 1
                            clustermesh-apiserver    
                            hubble-relay             
        Cluster Pods:          2/2 managed by Cilium
        Helm chart version:    1.20.3
        Image versions         cilium             quay.io/cilium/cilium:v1.20.3@sha256:95cfa5c2427cc6b452c00908778d0566311f572589284af949d06a013db1a849: 1
                            cilium-envoy       quay.io/cilium/cilium-envoy:v1.38.6-1791537840-00e749f11f69334c625e53fc1ce2fc6c7f34a51f@sha256:d6c8c0c91954d1885026d82a31b341f37dcd34a4b127fdaf1587e43ddd224cef: 1
                            cilium-operator    quay.io/cilium/operator-generic:v1.20.3@sha256:efdd8d89d6d8f63d21a065fa2f9e17614a2b3ac9371b221af9355f63829e2dbc: 1

        ```

#### 3.4.加入worker节点

```shell
kubeadm join k8s-vip:6443 --token 2zzmat.b1omkhqhuns4s30x \
	--discovery-token-ca-cert-hash sha256:66d67a3c65fb6a32e5e67b1194ec9a49fc826f1ae1d9ab92b3a2932e49a82d5e
kubectl  get nodes -o wide
NAME           STATUS   ROLES           AGE     VERSION   INTERNAL-IP      EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
k8s-master01   Ready    control-plane   60m     v1.35.7   192.168.122.11   <none>        Ubuntu 24.04.3 LTS   6.8.0-149-generic   containerd://2.2.1
k8s-worker01   Ready    <none>          9m      v1.35.7   192.168.122.21   <none>        Ubuntu 24.04.3 LTS   6.8.0-149-generic   containerd://2.2.1
k8s-worker02   Ready    <none>          8m56s   v1.35.7   192.168.122.22   <none>        Ubuntu 24.04.3 LTS   6.8.0-149-generic   containerd://2.2.1
k8s-worker03   Ready    <none>          8m53s   v1.35.7   192.168.122.23   <none>        Ubuntu 24.04.3 LTS   6.8.0-149-generic   containerd://2.2.1
cilium status
    /¯¯\
 /¯¯\__/¯¯\    Cilium:             OK
 \__/¯¯\__/    Operator:           OK
 /¯¯\__/¯¯\    Envoy DaemonSet:    OK
 \__/¯¯\__/    Hubble Relay:       disabled
    \__/       ClusterMesh:        disabled

DaemonSet              cilium                   Desired: 4, Ready: 4/4, Available: 4/4
DaemonSet              cilium-envoy             Desired: 4, Ready: 4/4, Available: 4/4
Deployment             cilium-operator          Desired: 1, Ready: 1/1, Available: 1/1
Containers:            cilium                   Running: 4
                       cilium-envoy             Running: 4
                       cilium-operator          Running: 1
                       clustermesh-apiserver    
                       hubble-relay             
Cluster Pods:          2/2 managed by Cilium
Helm chart version:    1.20.3
Image versions         cilium             quay.io/cilium/cilium:v1.20.3@sha256:95cfa5c2427cc6b452c00908778d0566311f572589284af949d06a013db1a849: 4
                       cilium-envoy       quay.io/cilium/cilium-envoy:v1.38.6-1791537840-00e749f11f69334c625e53fc1ce2fc6c7f34a51f@sha256:d6c8c0c91954d1885026d82a31b341f37dcd34a4b127fdaf1587e43ddd224cef: 4
                       cilium-operator    quay.io/cilium/operator-generic:v1.20.3@sha256:efdd8d89d6d8f63d21a065fa2f9e17614a2b3ac9371b221af9355f63829e2dbc: 1
```
## 验证集群

### 1.创建deploy和svc
```shell
kubectl  create deployment myapp --image=swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/ikubernetes/myapp:v1 --replicas=5
kubectl expose deployment myapp --port=80 --target-port=80 --type="NodePort"
```
### 2.查看pod跟svc
```shell
kubectl  get pod -A -o wide -l app=myapp
NAME                     READY   STATUS    RESTARTS   AGE   IP             NODE           NOMINATED NODE   READINESS GATES
myapp-7df864fdcb-4gz5m   1/1     Running   0          17s   10.244.4.104   k8s-worker01   <none>           <none>
myapp-7df864fdcb-9qbm2   1/1     Running   0          17s   10.244.4.240   k8s-worker01   <none>           <none>
myapp-7df864fdcb-hhhdp   1/1     Running   0          17s   10.244.6.225   k8s-worker03   <none>           <none>
myapp-7df864fdcb-qq4lp   1/1     Running   0          17s   10.244.6.140   k8s-worker03   <none>           <none>
myapp-7df864fdcb-zmf5g   1/1     Running   0          17s   10.244.5.82    k8s-worker02   <none>           <none>
root@k8s-master01:~# kubectl  get svc
NAME         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
kubernetes   ClusterIP   10.96.0.1      <none>        443/TCP        73m
myapp        NodePort    10.99.57.136   <none>        80:30468/TCP   4m59s
```
### 3.通过svc访问pod

```shell
for i in `seq 5`;do curl 10.99.57.136/hostname.html;done
myapp-7df864fdcb-9qbm2
myapp-7df864fdcb-9qbm2
myapp-7df864fdcb-hhhdp
myapp-7df864fdcb-4gz5m
myapp-7df864fdcb-hhhdp
```
### 4. 验证dns

```shell
apt install -y dnsutils
kubectl get svc -n kube-system
NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
kube-dns   ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   3h7m

dig -t A myapp.default.svc.cluster.local @10.96.0.10

; <<>> DiG 9.18.39-0ubuntu0.24.04.9-Ubuntu <<>> -t A myapp.default.svc.cluster.local @10.96.0.10
;; global options: +cmd
;; Got answer:
;; WARNING: .local is reserved for Multicast DNS
;; You are currently testing what happens when an mDNS query is leaked to DNS
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 27081
;; flags: qr aa rd; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
;; WARNING: recursion requested but not available

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
; COOKIE: 5a53481bf084a4dd (echoed)
;; QUESTION SECTION:
;myapp.default.svc.cluster.local. IN	A

;; ANSWER SECTION:
myapp.default.svc.cluster.local. 30 IN	A	10.99.57.136

;; Query time: 0 msec
;; SERVER: 10.96.0.10#53(10.96.0.10) (UDP)
;; WHEN: Sat Nov 21 14:58:40 CST 2026
;; MSG SIZE  rcvd: 119
```
```shell
kubectl  exec -it myapp-7df864fdcb-hhhdp-- sh
/ # wget -O - -q myapp
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
```

## 启用Cilium Ingress控制器

!!! note "[官方文档](https://docs.cilium.io/en/stable/network/servicemesh/ingress/): `https://docs.cilium.io/en/stable/network/servicemesh/ingress/`"


```
# shared（共享模式）：集群内所有的 Ingress 共用同一个负载均衡器实例
# dedicated（专用模式）：每个 Ingress 都有自己独立的负载均衡器
cilium upgrade --version 1.20.3 \
  --set kubeProxyReplacement=true \
  --set ipam.mode=kubernetes \
  --set routingMode=native \
  --set ipam.operator.clusterPoolIPv4PodCIDRList=10.244.0.0/16 \
  --set ipam.operator.clusterPoolIPv4MaskSize=24 \
  --set ipv4NativeRoutingCIDR=10.244.0.0/16 \
  --set autoDirectNodeRoutes=true \
  --set ingressController.enabled=true \
  --set ingressController.loadbalancerMode=shared 
ℹ️  Using Cilium version 1.20.3
🔮 Auto-detected cluster name: kubernetes
🔮 Auto-detected kube-proxy has not been installed
ℹ️  Cilium will fully replace all functionalities of kube-proxy
⚠️  You maybe need to restart Cilium pods for configmap changes to take effect


kubectl -n kube-system rollout restart daemonset cilium
kubectl  get ingressclass  
NAME     CONTROLLER                     PARAMETERS   AGE
cilium   cilium.io/ingress-controller   <none>       69s
# 这里 EXTERNAL-IP 有IP 是由于已经部署好了MetalLB
kubectl -n kube-system get svc cilium-ingress
NAME             TYPE           CLUSTER-IP     EXTERNAL-IP       PORT(S)                      AGE
cilium-ingress   LoadBalancer   10.97.138.85   192.168.122.140   80:31533/TCP,443:32563/TCP   93s
```

### 验证Ingress控制器

```
kubectl  create deployment myapp --replicas=3 --image=ikubernetes/myapp:v1 
kubectl expose deployment myapp --port=80 --target-port=80 --type="ClusterIP"
kubectl  create ingress ingress-myapp --rule="myapp.devops.io/*=myapp:80" --class='cilium' 
curl -H "Host: myapp.devops.io" http://192.168.122.140
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
```