# nfs-subdir-external-provisioner

NFS subdir external provisioner是一个存储自动配置器，它使用您现有的、已配置的NFS 服务器，通过持久卷声明 (Persistent Volume Claim) 支持 Kubernetes 持久卷的动态配置。持久卷的配置方式如下${namespace}-${pvcName}-${pvName}。

## 1.准备NFS Server

```shell
# ubuntu
apt install nfs-server
# centos
yum -y install nfs-utils

mkdir -pv /data/nfs-k8s
echo  "/data/nfs-k8s  *(rw,sync,no_root_squash,no_subtree_check)" >> /etc/exports
exportfs  -av
exporting *:/data/nfs-k8s

showmount -e 192.168.1.111
Export list for 192.168.1.111:
/data/nfs-k8s *
```

## 2.部署 nfs-subdir-external-provisioner

```shell
# 获取资源清单到本地
wget https://gh-proxy.org/https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner/blob/master/deploy/class.yaml
wget https://gh-proxy.org/https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner/blob/master/deploy/deployment.yaml
wget https://gh-proxy.org/https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner/blob/master/deploy/rbac.yaml
# 配置Deployment
vim deployment.yaml
              value: k8s-sigs.io/nfs-subdir-external-provisioner
            - name: NFS_SERVER
              value: 192.168.1.111
            - name: NFS_PATH
              value: /data/nfs-k8s
      volumes:
        - name: nfs-client-root
          nfs:
            server: 192.168.1.111
            path: /data/nfs-k8s

# 
kubectl  apply -f .
# 设置程默认存储类
kubectl patch storageclass nfs-client -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

## 3. 验证存储可用性

```
tee test-claim.yaml << EOF | kubectl apply -f -
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: test-claim
spec:
  storageClassName: nfs-client
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Mi
EOF
kubectl  get pvc
NAME         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
test-claim   Bound    pvc-a84fbcab-7f31-4909-aeec-0399529a6ceb   1Mi        RWX            nfs-client     <unset>                 4m47s
kubectl  get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
pvc-a84fbcab-7f31-4909-aeec-0399529a6ceb   1Mi        RWX            Delete           Bound    default/test-claim   nfs-client     <unset> 
```
```
kubectl apply -f - << EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test-pod
    image: busybox:stable
    command:
      - "/bin/sh"
    args:
      - "-c"
      - "touch /mnt/SUCCESS && exit 0 || exit 1"
    volumeMounts:
      - name: nfs-pvc
        mountPath: "/mnt"
  restartPolicy: "Never"
  volumes:
    - name: nfs-pvc
      persistentVolumeClaim:
        claimName: test-claim
EOF
```