# Helm 包管理器

Helm 是 Kubernetes 的包管理器。

## 安装

```
tar -xf helm-v4.3.2-linux-amd64.tar.gz 
cp linux-amd64/helm /usr/local/bin/
chmod  +x /usr/local/bin/helm 
helm version
version.BuildInfo{Version:"v4.3.2", GitCommit:"8346aaa55e7161f7c547212d0a87f01367976727", GitTreeState:"clean", GoVersion:"go1.27.4", KubeClientVersion:"v1.37"}

```