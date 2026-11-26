# Envoy Gateway

## Setup

```
wget https://github.com/envoyproxy/gateway/releases/download/v1.10.0/install.yaml
kubectl  create -f install.yaml
kubectl  get pod -n envoy-gateway-system
NAME                            READY   STATUS      RESTARTS      AGE
eg-gateway-helm-certgen-vbn6t   0/1     Completed   0             26s
envoy-gateway-f9486b44b-tnshl   1/1     Running     2 (21s ago)   26s
kubectl apply -f - << EOF
---
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: eg
  namespace: envoy-gateway-system
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller
EOF
kubectl  get gatewayclass
NAME   CONTROLLER                                      ACCEPTED   AGE
eg     gateway.envoyproxy.io/gatewayclass-controller   True       21s
kubectl apply -f - << EOF
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: eg
  namespace: envoy-gateway-system
spec:
  gatewayClassName: eg
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
EOF
kubectl  get gatewayclass
NAME   CONTROLLER                                      ACCEPTED   AGE
eg     gateway.envoyproxy.io/gatewayclass-controller   True       21s
kubectl  get pod -n envoy-gateway-system
NAME                                                      READY   STATUS    RESTARTS        AGE
envoy-envoy-gateway-system-eg-5391c79d-5c5bdd476c-zmb2q   2/2     Running   0               12s
envoy-gateway-f9486b44b-tnshl                             1/1     Running   2 (2m37s ago)   2m42s
root@k8s-master01:~/gateway# kubectl  get svc -n envoy-gateway-system
NAME                                     TYPE           CLUSTER-IP       EXTERNAL-IP       PORT(S)                                            AGE
envoy-envoy-gateway-system-eg-5391c79d   LoadBalancer   10.102.163.96    192.168.122.140   80:30698/TCP                                       19s
envoy-gateway                            ClusterIP      10.100.112.173   <none>            18000/TCP,18001/TCP,18002/TCP,19001/TCP,9443/TCP   2m49s
```

## Example

### Http

??? example "案例"

    === "Deployment&Service"


        ```
        kubectl apply -f - <<EOF
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: whoami
          namespace: default
        spec:
          progressDeadlineSeconds: 600
          replicas: 2
          revisionHistoryLimit: 10
          selector:
            matchLabels:
              app: whoami
          strategy:
            rollingUpdate:
              maxSurge: 25%
              maxUnavailable: 25%
            type: RollingUpdate
          template:
            metadata:
              labels:
                app: whoami
            spec:
              containers:
              - image: traefik/whoami
                imagePullPolicy: Always
                name: whoami
                ports:
                - containerPort: 80
                  protocol: TCP
                terminationMessagePath: /dev/termination-log
                terminationMessagePolicy: File
              dnsPolicy: ClusterFirst
              restartPolicy: Always
              schedulerName: default-scheduler
              securityContext: {}
              terminationGracePeriodSeconds: 30
        ---
        apiVersion: v1
        kind: Service
        metadata:
          name: whoami
          namespace: default
        spec:
          ports:
          - port: 80
            protocol: TCP
            targetPort: 80
          selector:
            app: whoami
          sessionAffinity: None
          type: ClusterIP
        EOF
        ```
    === "HttpRoute"

        ```
        kubectl apply -f - <<EOF
        apiVersion: gateway.networking.k8s.io/v1
        kind: HTTPRoute
        metadata:
          name: whoami
          namespace: default
        spec:
          parentRefs:
          - name: eg
            namespace: envoy-gateway-system
          hostnames:
          - "whoami.devops.io"
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /
            backendRefs:
            - name: whoami
              port: 80
        EOF
        ```
    === "Verify"

        ```
        curl -I  -H "host: whoami.devops.io" http://192.168.122.140
        HTTP/1.1 200 OK
        date: Thu, 26 Nov 2026 11:59:03 GMT
        content-length: 365
        content-type: text/plain; charset=utf-8
        ```

### Https

??? example "**一张 SAN 证书，同时包含 whoami.devops.io 和 www.devops.io**"

    - 生成 SAN 证书（同时带两个域名）

    ```
    cat > openssl.cnf <<EOF
    [req]
    distinguished_name = dn
    x509_extensions = v3_ext
    prompt = no

    [dn]
    CN = devops.io

    [v3_ext]
    subjectAltName = @alt_names
    basicConstraints = CA:FALSE
    keyUsage = digitalSignature,keyEncipherment

    [alt_names]
    DNS.1 = whoami.devops.io
    DNS.2 = www.devops.io
    EOF
    openssl req -x509 -newkey rsa:4096 -keyout tls.key -out tls.crt -days 3650 -nodes -config openssl.cnf
    ```

    - 创建 secret（envoy-gateway-system）

    ```
    kubectl create secret tls devops-tls-secret --cert=tls.crt --key=tls.key -n envoy-gateway-system
    ```

    === "Gateway"

        ```
        # 1. 增加https listener
        kubectl apply -f - << EOF
        apiVersion: gateway.networking.k8s.io/v1
        kind: Gateway
        metadata:
          name: eg
          namespace: envoy-gateway-system
        spec:
          gatewayClassName: eg
          listeners:
          - name: http
            protocol: HTTP
            port: 80
            allowedRoutes:
              namespaces:
                from: All
          - name: https
            protocol: HTTPS
            port: 443
            tls:
              mode: Terminate
              certificateRefs:
              - kind: Secret
                name: devops-tls-secret
                namespace: envoy-gateway-system
            allowedRoutes:
              namespaces:
                from: All
        EOF
        ```

    === "HttpRoute(www)"

        ```
        kubectl apply -f - <<EOF
        apiVersion: gateway.networking.k8s.io/v1
        kind: HTTPRoute
        metadata:
          name: www
          namespace: default
        spec:
          parentRefs:
          - name: eg
            namespace: envoy-gateway-system
          hostnames:
          - "www.devops.io"
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /
            backendRefs:
            - name: whoami
              port: 80
        EOF
        ```

    === "HttpRoute(whoami)"


        ```
        kubectl apply -f - <<EOF
        apiVersion: gateway.networking.k8s.io/v1
        kind: HTTPRoute
        metadata:
          name: whoami
          namespace: default
        spec:
          parentRefs:
          - name: eg
            namespace: envoy-gateway-system
          hostnames:
          - "whoami.devops.io"
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /
            backendRefs:
            - name: whoami
              port: 80
        EOF
        ```

    === "Verify"

        ```
        curl -vk --resolve whoami.devops.io:443:192.168.122.140 https://whoami.devops.io
        curl -vk --resolve www.devops.io:443:192.168.122.140 https://www.devops.io
        ```
??? example "**两个独立证书，两个 HTTPS listener（各自域名独立证书）**"

    - 生成证书和secret

    ```
    # 证书1：whoami.devops.io
    openssl req -x509 -newkey rsa:4096 -keyout whoami.key -out whoami.crt -days 3650 -nodes -subj "/CN=whoami.devops.io"
    # 证书2：www.devops.io
    openssl req -x509 -newkey rsa:4096 -keyout www.key -out www.crt -days 3650 -nodes -subj "/CN=www.devops.io"
    kubectl create secret tls whoami-tls-secret --cert=whoami.crt --key=whoami.key -n envoy-gateway-system
    kubectl create secret tls www-tls-secret --cert=www.crt --key=www.key -n envoy-gateway-system
    ```
    === "Gateway"

        ```
        # 两个 HTTPS listener，都在 443 端口，靠 `hostname` 区分域名（SNI）
        kubectl apply -f - << EOF
        apiVersion: gateway.networking.k8s.io/v1
        kind: Gateway
        metadata:
          name: eg
          namespace: envoy-gateway-system
        spec:
          gatewayClassName: eg
          listeners:
          - name: http
            protocol: HTTP
            port: 80
            allowedRoutes:
              namespaces:
                from: All

          - name: https-whoami
            protocol: HTTPS
            port: 443
            hostname: whoami.devops.io
            tls:
              mode: Terminate
              certificateRefs:
              - kind: Secret
                name: whoami-tls-secret
                namespace: envoy-gateway-system
            allowedRoutes:
              namespaces:
                from: All

          - name: https-www
            protocol: HTTPS
            port: 443
            hostname: www.devops.io
            tls:
              mode: Terminate
              certificateRefs:
              - kind: Secret
                name: www-tls-secret
                namespace: envoy-gateway-system
            allowedRoutes:
              namespaces:
                from: All
        EOF
        ```
    === "HttpRoute(www)"

        ```
        kubectl apply -f - <<EOF
        apiVersion: gateway.networking.k8s.io/v1
        kind: HTTPRoute
        metadata:
          name: www
          namespace: default
        spec:
          parentRefs:
          - name: eg
            namespace: envoy-gateway-system
            sectionName: https-www
          hostnames:
          - "www.devops.io"
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /
            backendRefs:
            - name: whoami
              port: 80
        EOF
        ```

    === "HttpRoute(whoami)"


        ```
        kubectl apply -f - <<EOF
        apiVersion: gateway.networking.k8s.io/v1
        kind: HTTPRoute
        metadata:
          name: whoami
          namespace: default
        spec:
          parentRefs:
          - name: eg
            namespace: envoy-gateway-system
            sectionName: https-whoami
          hostnames:
          - "whoami.devops.io"
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /
            backendRefs:
            - name: whoami
              port: 80
        EOF
        ```

    === "Verify"

        ```
        curl -vk --resolve whoami.devops.io:443:192.168.122.140 https://whoami.devops.io
        curl -vk --resolve www.devops.io:443:192.168.122.140 https://www.devops.io
        ```

=== "HTTP 80 强制跳转 HTTPS"

    ```YAML
    kubectl apply -f - << EOF
    apiVersion: gateway.networking.k8s.io/v1
    kind: HTTPRoute
    metadata:
      name: redirect-https
      namespace: default
    spec:
      parentRefs:
      - name: eg
        namespace: envoy-gateway-system
        sectionName: http
      hostnames:
      - whoami.devops.io
      - www.devops.io
      rules:
      - matches:
        - path:
            type: PathPrefix
            value: /
        filters:
        - type: RequestRedirect
          requestRedirect:
            scheme: https
            statusCode: 302
    EOF
    curl -I -k  -H "host: www.devops.io" http://192.168.122.140
    HTTP/1.1 302 Found
    location: https://www.devops.io/
    date: Thu, 26 Nov 2026 12:56:52 GMT
    transfer-encoding: chunked
    ```