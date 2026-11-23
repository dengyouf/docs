# immortalwrt.md

```
wget https://downloads.immortalwrt.org/releases/23.05.1/targets/x86/64/immortalwrt-23.05.1-x86-64-generic-ext4-combined-efi.img.gz
gzip  -d immortalwrt-23.05.1-x86-64-generic-ext4-combined-efi.img.gz
sudo virt-install --name immortalwrt \
--osinfo=linux2022 --ram 1024 --vcpus 2 \
--disk path=immortalwrt-23.05.1-x86-64-generic-ext4-combined-efi.img,bus=virtio,cache=writeback \
--network bridge=virbr0,model=virtio  \
--graphics=vnc,password=123456,port=5967,listen=0.0.0.0 \
--noautoconsole --import --autostart
```

```
cat /etc/config/network 

config interface 'loopback'
	option device 'lo'
	option proto 'static'
	option ipaddr '127.0.0.1'
	option netmask '255.0.0.0'

config globals 'globals'
	option ula_prefix 'fd88:c706:cd36::/48'
	option packet_steering '1'

config device
	option name 'br-lan'
	option type 'bridge'
	list ports 'eth0'

config interface 'lan'
	option device 'br-lan'
	option proto 'static'
	option ipaddr '192.168.122.253'
	option netmask '255.255.255.0'
	option ip6assign '60'
	option gateway '192.168.122.1'
	list dns '223.5.5.5'
```

插件：

- luci-i18n-argon-config-zh-cn
- luci-app-openclash
- luci-i18n-passwall-zh-cn
- luci-i18n-homeproxy-zh-cn


wget https://github.com/moshaoli688/clash/releases/download/v1.18.0/clash-linux-amd64-v1.18.0.gz
gzip -d clash-linux-amd64-v1.18.0.gz clash.meta
chmod +x clash.meta