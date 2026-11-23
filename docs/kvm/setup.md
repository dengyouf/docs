# Linux KVM

KVM（基于内核的虚拟机器）是一种适用于 x86 硬件上的 Linux 系统的全虚拟化解决方案，它支持使用虚拟化扩展（如 Intel VT 或 AMD-V）。该解决方案由一个可加载的内核模块 kvm.ko 组成，该模块提供了核心虚拟化基础架构；此外，还有针对特定处理器的模块 kvm-intel.ko 或 kvm-amd.ko，这些模块则负责处理与处理器相关的虚拟化任务。

## 安装手册

=== "Ubuntu26.4"

1. 确认CPU 虚拟化扩展是否可用
```shell
sudo egrep -c '(vmx|svm)' /proc/cpuinfo
32
```
2. 加载KVM 内核模块
```shell
modprobe kvm_intel nested=1
echo  "options kvm_intel nested=1"|sudo tee -a /etc/modprobe.d/kvm.conf
lsmod | grep kvm
kvm_intel             487424  0
kvm                  1404928  1 kvm_intel
irqbypass              12288  1 kvm
```
3. 使用KVM加速
```shell
sudo apt install cpu-checker
sudo kvm-ok
INFO: /dev/kvm exists
KVM acceleration can be used
```
4. 安装kvm软件包
```shell
sudo apt install qemu-system-x86 libvirt-daemon-system libvirt-clients bridge-utils virt-manager libguestfs-tools
```
5. 授权用户
```shell
sudo adduser dengyouf libvirt
sudo adduser dengyouf kvm
```
6. 配置image路径
```
systemctl  stop libvirtd.socket libvirtd
mkdir -pv /data/apps/kvm/
mv /var/lib/libvirt/images /data/apps/kvm/
ln -sv /data/apps/kvm/images /var/lib/libvirt/images
systemctl  enable  libvirtd.socket libvirtd --now
```
6. 验证安装
```shell
sudo virsh  list --all
 Id   Name          State
------------------------------
```
8. 创建网桥
```shell
sudo cp /etc/netplan/00-installer-config.yaml{,.bak}
sudo cat >  /etc/netplan/00-installer-config.yaml << 'EOF'
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      # disable existing configuration for ethernet
      #addresses: [192.168.1.30/24]
      #routes:
      #  - to: default
      #    via: 192.168.1.1
      #    metric: 100
      #nameservers:
      #  addresses: [192.168.1.10]
      #  search: [linux.io]
      dhcp6: false
  # add configuration for bridge interface
  # [macaddress] ⇒ specify HW address of enp1s0
  bridges:
    br0:
      interfaces: [eth0]
      dhcp4: false
      addresses: [192.168.1.7/24]
      routes:
        - to: default
          via: 192.168.1.1
          metric: 100
      nameservers:
        addresses: [192.168.1.1, 8.8.8.8, 223.5.5.5]
        search: [linux.io]
      parameters:
        stp: false
      dhcp6: true
EOF
sudo netplan apply 
```

### 安装虚拟机

```shell
sudo virt-install \
--name ubuntu2204 \
--ram 4096 \
--disk path=/var/lib/libvirt/images/ubuntu2204.img,size=80 \
--vcpus 2 \
--os-variant ubuntu22.04 \
--network bridge=br0 \
--graphics none \
--console pty,target_type=serial \
--location /home/dengyouf/ubuntu-22.04.5-live-server-amd64.iso,kernel=casper/vmlinuz,initrd=casper/initrd \
--extra-args 'console=ttyS0,115200n8' 

...
================================================================================
  Serial                                                              [ Help ]
================================================================================

  As the installer is running on a serial console, it has started in basic
  mode, using only the ASCII character set and black and white colours.

  If you are connecting from a terminal emulator such as gnome-terminal that
  supports unicode and rich colours you can switch to "rich mode" which uses
  unicode, colours and supports many languages.

  You can also connect to the installer over the network via SSH, which will
  allow use of rich mode.


                          [ Continue in rich mode  > ]
                          [ Continue in basic mode > ]
                          [ View SSH instructions    ]
# 选择 [Continue in basic mode] 即开始安装，安装完成后，重启机器，开始登陆
...
Ubuntu 22.04.5 LTS mylab ttyS0

mylab login: dengyouf
Password:
~$ ip add l
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: enp1s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:15:25:e4 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.102/24 metric 100 brd 192.168.1.255 scope global dynamic enp1s0
       valid_lft 7026sec preferred_lft 7026sec
    inet6 2408:8207:78d0:690:5054:ff:fe15:25e4/64 scope global dynamic mngtmpaddr noprefixroute
       valid_lft 85066sec preferred_lft 2266sec
    inet6 fe80::5054:ff:fe15:25e4/64 scope link
       valid_lft forever preferred_lft forever
dengyouf@mylab:~$ lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
loop0    7:0    0 38.8M  1 loop /snap/snapd/21759
loop1    7:1    0   87M  1 loop /snap/lxd/29351
loop2    7:2    0 63.9M  1 loop /snap/core20/2318
sr0     11:0    1 1024M  0 rom
vda    252:0    0   80G  0 disk
├─vda1 252:1    0    1M  0 part
├─vda2 252:2    0    2G  0 part /boot
├─vda3 252:3    0    4G  0 part [SWAP]
└─vda4 252:4    0   74G  0 part /
dengyouf@mylab:~$ df -h
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           392M  1.1M  391M   1% /run
/dev/vda4        73G  3.0G   66G   5% /
tmpfs           2.0G     0  2.0G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/vda2       2.0G  125M  1.7G   7% /boot
tmpfs           392M  4.0K  392M   1% /run/user/1000
dengyouf@mylab:~$
# 切换终端 Ctrl +]
➜  ~ sudo virsh console ubuntu2404 # 连接虚拟机
Connected to domain 'ubuntu2404'
Escape character is ^] (Ctrl + ])

dengyouf@mylab:~$
```
### 克隆虚拟机

```shell
sudo virt-clone --auto-clone -o 00-ubuntu24.04-tmpl -n k8s-master01
sudo virt-clone --auto-clone -o 00-ubuntu24.04-tmpl -n k8s-worker01
sudo virt-clone --auto-clone -o 00-ubuntu24.04-tmpl -n k8s-worker02
sudo virt-clone --auto-clone -o 00-ubuntu24.04-tmpl -n k8s-worker03

sudo virt-ls -d k8s-master01 /etc/netplan/

sudo virt-sysprep  \
  --operations defaults,machine-id,-ssh-userdir,-lvm-uuids \
  --hostname k8s-master01 \
  --run-command \
  "sed -i 's@192.168.122.250@192.168.122.111@g' \
  /etc/netplan/50-cloud-init.yaml && \
   dpkg-reconfigure openssh-server" -d k8s-master01

sudo virt-sysprep  \
  --operations defaults,machine-id,-ssh-userdir,-lvm-uuids \
  --hostname k8s-worker01 \
  --run-command \
  "sed -i 's@192.168.122.250@192.168.122.121@g' \
  /etc/netplan/50-cloud-init.yaml && \
   dpkg-reconfigure openssh-server" -d k8s-worker01

sudo virt-sysprep  \
  --operations defaults,machine-id,-ssh-userdir,-lvm-uuids \
  --hostname k8s-worker02 \
  --run-command \
  "sed -i 's@192.168.122.250@192.168.122.122@g' \
  /etc/netplan/50-cloud-init.yaml && \
   dpkg-reconfigure openssh-server" -d k8s-worker02

sudo virt-sysprep  \
  --operations defaults,machine-id,-ssh-userdir,-lvm-uuids \
  --hostname k8s-worker03 \
  --run-command \
  "sed -i 's@192.168.122.250@192.168.122.123@g' \
  /etc/netplan/50-cloud-init.yaml && \
   dpkg-reconfigure openssh-server" -d k8s-worker03
```

### 虚拟机管理

```shell
sudo virsh start ubuntu2404
sudo virsh shutdown ubuntu2404
sudo virsh destroy  ubuntu22.04
sudo virsh start ubuntu2404 --console
```

### 虚拟化嵌套

1. 宿主机支持嵌套
```shell
cat /sys/module/kvm_intel/parameters/nested
Y
```
2. 修改 CPU 的模式
```shell
sudo  virsh edit ubuntu2404
...
<cpu mode='host-passthrough' check='none' migratable='on'/>
```
