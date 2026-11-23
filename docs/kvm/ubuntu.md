# InitOs

## Ubuntu


- 允许root用户远程登陆

```
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
systemctl  restart ssh
echo "root:root"|chpasswd 
```

- 更新apt源为[阿里源](https://developer.aliyun.com/mirror/ubuntu?spm=a2c6h.13651102.0.0.3e221b1160qO5E)

- 关闭防火墙

```
systemctl disable --now ufw
```

- 关闭selinux

- 关闭swap分区

```
sed -ri 's/.*swap.*/#&/' /etc/fstab
swapoff -a && sysctl -w vm.swappiness=0

# blkid 查出来 /dev/sda2:... TYPE="swap"
sudo systemctl  mask dev-sda2.swap
```
- 调整时区

```
sudo cp /usr/share/zoneinfo/Asia/Shanghai  /etc/localtime
date -R
Wed, 31 Jul 2024 19:04:19 +0800
```

- 时间同步

```
sudo apt update
sudo apt install -y ntpdate
/usr/sbin/ntpdate ntp.aliyun.com 2&>1 /dev/null

crontab -e
/usr/sbin/ntpdate ntp.aliyun.com 2&>1 /dev/null
```
```
# chrony服务端
apt install chrony -y
cat > /etc/chrony/chrony.conf << EOF 
pool ntp.aliyun.com iburst
driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
allow 192.168.1.0/24
local stratum 10
keyfile /etc/chrony.keys
leapsectz right/UTC
logdir /var/log/chrony
EOF

systemctl restart chronyd
systemctl enable chronyd

# chrony客户端
apt install chrony -y
vim /etc/chrony/chrony.conf
cat /etc/chrony/chrony.conf | grep -v  "^#" | grep -v "^$"
pool 192.168.1.111 iburst
driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
keyfile /etc/chrony.keys
leapsectz right/UTC
logdir /var/log/chrony

systemctl restart chronyd ; systemctl enable chronyd

# 客户端安装一条命令
apt install chrony -y 
sed -i "s#2.centos.pool.ntp.org#192.168.1.111#g" /etc/chrony/chrony.conf ; systemctl restart chronyd ; systemctl enable chronyd


#使用客户端进行验证
chronyc sources -v


# 或者使用crontab -e
*/3 * * * * /usr/sbin/ntpdate ntp.aliyun.com &>/dev/null
```

- 安装常用软件包

```shell
apt install  wget jq psmisc vim net-tools nfs-kernel-server  telnet lvm2 git tar curl lrzsz -y
apt install ipvsadm ipset sysstat conntrack -y
```

- 配置ulimit

```
ulimit -SHn 65535
cat >> /etc/security/limits.conf <<EOF
* soft nofile 655360
* hard nofile 131072
* soft nproc 655350
* hard nproc 655350
* seft memlock unlimited
* hard memlock unlimitedd
EOF
```

- 免密登陆

```
# <在master01节点操作>
apt install -y sshpass
ssh-keygen -f /root/.ssh/id_rsa -P ''
export IP="192.168.1.111 192.168.1.112 192.168.1.113 192.168.1.121 192.168.1.122"
export SSHPASS=root
for HOST in $IP;do
     sshpass -e ssh-copy-id -o StrictHostKeyChecking=no $HOST
done
```

- 配置内核模块

```
cat >> /etc/modules-load.d/ipvs.conf <<EOF 
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack
ip_tables
ip_set
xt_set
ipt_set
ipt_rpfilter
ipt_REJECT
ipip
EOF

systemctl restart systemd-modules-load.service

lsmod | grep -e ip_vs -e nf_conntrack
ip_vs_sh               16384  0
ip_vs_wrr              16384  0
ip_vs_rr               16384  0
ip_vs                 155648  6 ip_vs_rr,ip_vs_sh,ip_vs_wrr
nf_conntrack          139264  1 ip_vs
nf_defrag_ipv6         24576  2 nf_conntrack,ip_vs
nf_defrag_ipv4         16384  1 nf_conntrack
libcrc32c              16384  4 nf_conntrack,btrfs,raid456,ip_vs
```

- 修改内核参数

```SHELL
cat <<EOF > /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
fs.may_detach_mounts = 1
vm.overcommit_memory=1
vm.panic_on_oom=0
fs.inotify.max_user_watches=89100
fs.file-max=52706963
fs.nr_open=52706963
net.netfilter.nf_conntrack_max=2310720


net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_intvl =15
net.ipv4.tcp_max_tw_buckets = 36000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_orphans = 327680
net.ipv4.tcp_orphan_retries = 3
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 16384
net.ipv4.ip_conntrack_max = 65536
net.ipv4.tcp_max_syn_backlog = 16384
net.ipv4.tcp_timestamps = 0
net.core.somaxconn = 16384

net.ipv6.conf.all.disable_ipv6 = 0
net.ipv6.conf.default.disable_ipv6 = 0
net.ipv6.conf.lo.disable_ipv6 = 0
net.ipv6.conf.all.forwarding = 0

EOF

sysctl --system
```