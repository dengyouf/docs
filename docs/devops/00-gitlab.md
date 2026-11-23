# GitLab代码管理

基于Ubuntu 24.04 安装 Gitlab Server

## 环境准备

### 1.主机名解析

```shell
hostnamectl  set-hostname gitlab.devops.io
echo "192.168.122.16 gitlab.devops.io gitlab" >> /etc/hosts
```

### 2.关闭防火墙和selinux
```shell
systemctl disable --now ufw
```

### 3.时间同步

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
```

## GitLab安装

使用[清华源](https://mirrors.tuna.tsinghua.edu.cn/help/gitlab-ce/) 安装gitlab

### 1. 安装gitlab
```shell
wget https://mirrors.tuna.tsinghua.edu.cn/gitlab-ce/ubuntu/noble/pool/main/g/gitlab-ce/gitlab-ce_17.11.7-ce.0_amd64.deb
apt install ./gitlab-ce_17.11.7-ce.0_amd64.deb
```
### 2.配置gitlab.rb
```shell
vim /etc/gitlab/gitlab.rb
external_url 'http://gitlab.devops.io'
```

### 3.启动gitlab

```shell
~# gitlab-ctl reconfigure
```

### 4.获取初始密码

```shell
~# cat /etc/gitlab/initial_root_password
```
