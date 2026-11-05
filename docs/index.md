---
hide:
  - navigation
  - toc
---

<div class="ops-hero" markdown>

# 运维手册



[//]: # ([内容导航]&#40;#nav&#41;{ .md-button .md-button--primary })

[//]: # ([常用速查]&#40;#quick&#41;{ .md-button })

</div>

[//]: # (## 内容导航 {#nav})

[//]: # ()
[//]: # (<div class="grid cards" markdown>)

[//]: # ()
[//]: # (-   :material-server-network:{ .lg .middle } **系统运维**)

[//]: # ()
[//]: # (    ---)

[//]: # ()
[//]: # (    主机基线、Nginx 与 Docker 的日常维护和排错。)

[//]: # ()
[//]: # (    [:octicons-arrow-right-24: 进入]&#40;ops/linux.md&#41;)

[//]: # ()
[//]: # (-   :material-database:{ .lg .middle } **数据库**)

[//]: # ()
[//]: # (    ---)

[//]: # ()
[//]: # (    MySQL / PostgreSQL 部署、日志、备份恢复，Redis 配置与运维。)

[//]: # ()
[//]: # (    [:octicons-arrow-right-24: 进入]&#40;db/mysql-installation.md&#41;)

[//]: # ()
[//]: # (-   :material-swap-horizontal:{ .lg .middle } **网络与传输**)

[//]: # ()
[//]: # (    ---)

[//]: # ()
[//]: # (    rsync 同步策略、限速与大文件增量传输。)

[//]: # ()
[//]: # (    [:octicons-arrow-right-24: 进入]&#40;network/rsync.md&#41;)

[//]: # ()
[//]: # (-   :material-package-variant:{ .lg .middle } **镜像源**)

[//]: # ()
[//]: # (    ---)

[//]: # ()
[//]: # (    内网 / 云上环境的软件源替换与加速配置。)

[//]: # ()
[//]: # (    [:octicons-arrow-right-24: 进入]&#40;huawei/rocky-linux.md&#41;)

[//]: # ()
[//]: # (</div>)

[//]: # ()
[//]: # (## 常用速查 {#quick})

[//]: # ()
[//]: # (| 场景 | 命令 | 说明 |)

[//]: # (| --- | --- | --- |)

[//]: # (| 磁盘写满 | `df -hT` / `du -sh /*` | 先用 `df -hT` 定位挂载点，再逐层 `du` 下钻 |)

[//]: # (| 端口占用 | `ss -lntp` | 替代 `netstat -lntp`，无需安装 net-tools |)

[//]: # (| 进程详情 | `ps -ef \| grep <key>` | 结合 `systemctl status <svc>` 看退出码 |)

[//]: # (| 实时日志 | `journalctl -u <svc> -f` | 服务由 systemd 托管时优先用它 |)

[//]: # (| 抓包 | `tcpdump -i any port 3306 -w a.pcap` | 抓完用 Wireshark 分析 |)

[//]: # ()
[//]: # (## 使用约定)

[//]: # ()
[//]: # (!!! note "命令格式说明")

[//]: # ()
[//]: # (    所有命令默认以 **root** 或具备 `sudo` 权限的账号执行。)

[//]: # ()
[//]: # (    - `$` 开头表示普通用户执行，`#` 开头表示 root 执行)

[//]: # (    - 尖括号 `<xxx>` 为需要替换的占位符)

[//]: # (    - 版本号以 Rocky Linux 9 / MySQL 8.0 / Redis 7 为基准，其他版本会单独标注)

[//]: # ()
[//]: # (!!! warning "生产环境操作提醒")

[//]: # ()
[//]: # (    涉及 `rm`、`dd`、`mkfs`、`DROP`、`FLUSHALL` 等破坏性命令时，务必先确认目标主机与实例，)

[//]: # (    并确保最近一次备份可用。手册中的危险命令均已加 ⚠️ 标注。)
