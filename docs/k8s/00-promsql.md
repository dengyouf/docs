# 节点相关

```
# cpu负载
node_load1
node_load5
node_load15
# cpu使用率
rate(node_cpu_seconds_total[5m])
# 内存使用率
100- (node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes* 100)
# 磁盘使用率
(1- node_filesystem_avail_bytes{mountpoint="/"}/node_filesystem_size_bytes{mountpoint="/"})*100
# Inode使用率
 (1- node_filesystem_files_free{instance="k8s-master01", mountpoint="/"}/node_filesystem_files{instance="k8s-master01", mountpoint="/"} )*100
# 系统启动天数
(node_time_seconds - node_boot_time_seconds)/86499                                                                              
```