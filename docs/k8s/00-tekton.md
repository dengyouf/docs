# Tekton Operator 完整落地

架构：K8s 1.35.7 + Cilium + Metallb + Gitlab + Tekton Operator


## 1. 安装 Tekton Operator

```
wget https://infra.tekton.dev/tekton-releases/operator/previous/v0.79.3/release.yaml
kubectl apply -f release.yaml
kubectl get pod -n tekton-operator 
NAME                                      READY   STATUS    RESTARTS   AGE
tekton-operator-99c885676-wxgx7           2/2     Running   0          3m35s
tekton-operator-webhook-fd45dd8d7-gfljg   1/1     Running   0          3m35s
```

## TektonConfig CR 核心配置

```
cat > tekton-config.yaml << EOF
apiVersion: operator.tekton.dev/v1alpha1
kind: TektonConfig
metadata:
  name: config
spec:
  profile: basic
  pipeline:
    version: v1.15.0
  trigger:
    version: v0.35.0
  chain:
    version: v0.27.0
  dashboard:
    version: v0.65.0
  targetNamespace: tekton-pipelines
  # 资源限制，防止抢资源
  pipelineController:
    resourcelimits:
      requests:
        cpu: "100m"
        memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
  pipelineWebhook:
    resourcelimits:
      requests:
        cpu: "50m"
        memory: "128Mi"
      limits:
        cpu: "200m"
        memory: "256Mi"
  triggerController:
    resourcelimits:
      requests:
        cpu: "50m"
        memory: "128Mi"
      limits:
        cpu: "200m"
        memory: "256Mi"
EOF
kubectl apply -f tekton-config.yaml
```