---
title: "Building the whole stack: 158 code blocks on one page"
date: 2026-07-25
description: "The maximum-block fixture — the reference corpus tops out at 158 blocks in a single post."
tags: ["fixtures", "code"]
categories: ["Meta"]
---

**Generated fixture — do not hand-edit.** Regenerate with
`python3 scripts/check_fixtures.py --regenerate`.

The reference corpus tops out at **158 fenced blocks in a single post**, against an average
of 18.2. This page reproduces that maximum, because the tail is where per-block cost stops
being theoretical: 158 individual copy-button listeners, 158 clipboard closures and 158
`ResizeObserver`s behave nothing like one delegated listener on the article element, and the
difference does not show up on a page with four blocks.

It is also the page-weight worst case for markup that scales with block count, and the
fixture the visual-regression suite should screenshot at 360 px to check that block chrome
does not accumulate vertical drift.

## Step 1 — redis

Install, enable and verify `redis`.

```sh
sudo dnf -y install redis
```

```sh
sudo systemctl enable --now redis
sudo systemctl status redis
```

```sh
sudo firewall-cmd --permanent --add-port=6003/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: redis
  port: 6004
  enabled: true
```

```text
● redis.service - Redis daemon
     Loaded: loaded (/usr/lib/systemd/system/redis.service; enabled)
     Active: active (running)
     CGroup: /system.slice/redis.service
             └─1035 /usr/sbin/redis
```

```sh
curl -fsSL http://127.0.0.1:6006/healthz
```

```ini
[redis]
bind = 127.0.0.1
port = 6007
```

```json
{"service": "redis", "port": 6008, "healthy": true}
```

## Step 2 — nginx

Install, enable and verify `nginx`.

```sh
sudo dnf -y install nginx
```

```sh
sudo systemctl enable --now nginx
sudo systemctl status nginx
```

```sh
sudo firewall-cmd --permanent --add-port=6011/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: nginx
  port: 6012
  enabled: true
```

```text
● nginx.service - Nginx daemon
     Loaded: loaded (/usr/lib/systemd/system/nginx.service; enabled)
     Active: active (running)
     CGroup: /system.slice/nginx.service
             └─1091 /usr/sbin/nginx
```

```sh
curl -fsSL http://127.0.0.1:6014/healthz
```

```ini
[nginx]
bind = 127.0.0.1
port = 6015
```

```json
{"service": "nginx", "port": 6016, "healthy": true}
```

## Step 3 — postgresql

Install, enable and verify `postgresql`.

```sh
sudo dnf -y install postgresql
```

```sh
sudo systemctl enable --now postgresql
sudo systemctl status postgresql
```

```sh
sudo firewall-cmd --permanent --add-port=6019/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: postgresql
  port: 6020
  enabled: true
```

```text
● postgresql.service - Postgresql daemon
     Loaded: loaded (/usr/lib/systemd/system/postgresql.service; enabled)
     Active: active (running)
     CGroup: /system.slice/postgresql.service
             └─1147 /usr/sbin/postgresql
```

```sh
curl -fsSL http://127.0.0.1:6022/healthz
```

```ini
[postgresql]
bind = 127.0.0.1
port = 6023
```

```json
{"service": "postgresql", "port": 6024, "healthy": true}
```

## Step 4 — haproxy

Install, enable and verify `haproxy`.

```sh
sudo dnf -y install haproxy
```

```sh
sudo systemctl enable --now haproxy
sudo systemctl status haproxy
```

```sh
sudo firewall-cmd --permanent --add-port=6027/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: haproxy
  port: 6028
  enabled: true
```

```text
● haproxy.service - Haproxy daemon
     Loaded: loaded (/usr/lib/systemd/system/haproxy.service; enabled)
     Active: active (running)
     CGroup: /system.slice/haproxy.service
             └─1203 /usr/sbin/haproxy
```

```sh
curl -fsSL http://127.0.0.1:6030/healthz
```

```ini
[haproxy]
bind = 127.0.0.1
port = 6031
```

```json
{"service": "haproxy", "port": 6032, "healthy": true}
```

## Step 5 — prometheus

Install, enable and verify `prometheus`.

```sh
sudo dnf -y install prometheus
```

```sh
sudo systemctl enable --now prometheus
sudo systemctl status prometheus
```

```sh
sudo firewall-cmd --permanent --add-port=6035/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: prometheus
  port: 6036
  enabled: true
```

```text
● prometheus.service - Prometheus daemon
     Loaded: loaded (/usr/lib/systemd/system/prometheus.service; enabled)
     Active: active (running)
     CGroup: /system.slice/prometheus.service
             └─1259 /usr/sbin/prometheus
```

```sh
curl -fsSL http://127.0.0.1:6038/healthz
```

```ini
[prometheus]
bind = 127.0.0.1
port = 6039
```

```json
{"service": "prometheus", "port": 6040, "healthy": true}
```

## Step 6 — grafana

Install, enable and verify `grafana`.

```sh
sudo dnf -y install grafana
```

```sh
sudo systemctl enable --now grafana
sudo systemctl status grafana
```

```sh
sudo firewall-cmd --permanent --add-port=6043/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: grafana
  port: 6044
  enabled: true
```

```text
● grafana.service - Grafana daemon
     Loaded: loaded (/usr/lib/systemd/system/grafana.service; enabled)
     Active: active (running)
     CGroup: /system.slice/grafana.service
             └─1315 /usr/sbin/grafana
```

```sh
curl -fsSL http://127.0.0.1:6046/healthz
```

```ini
[grafana]
bind = 127.0.0.1
port = 6047
```

```json
{"service": "grafana", "port": 6048, "healthy": true}
```

## Step 7 — vault

Install, enable and verify `vault`.

```sh
sudo dnf -y install vault
```

```sh
sudo systemctl enable --now vault
sudo systemctl status vault
```

```sh
sudo firewall-cmd --permanent --add-port=6051/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: vault
  port: 6052
  enabled: true
```

```text
● vault.service - Vault daemon
     Loaded: loaded (/usr/lib/systemd/system/vault.service; enabled)
     Active: active (running)
     CGroup: /system.slice/vault.service
             └─1371 /usr/sbin/vault
```

```sh
curl -fsSL http://127.0.0.1:6054/healthz
```

```ini
[vault]
bind = 127.0.0.1
port = 6055
```

```json
{"service": "vault", "port": 6056, "healthy": true}
```

## Step 8 — consul

Install, enable and verify `consul`.

```sh
sudo dnf -y install consul
```

```sh
sudo systemctl enable --now consul
sudo systemctl status consul
```

```sh
sudo firewall-cmd --permanent --add-port=6059/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: consul
  port: 6060
  enabled: true
```

```text
● consul.service - Consul daemon
     Loaded: loaded (/usr/lib/systemd/system/consul.service; enabled)
     Active: active (running)
     CGroup: /system.slice/consul.service
             └─1427 /usr/sbin/consul
```

```sh
curl -fsSL http://127.0.0.1:6062/healthz
```

```ini
[consul]
bind = 127.0.0.1
port = 6063
```

```json
{"service": "consul", "port": 6064, "healthy": true}
```

## Step 9 — etcd

Install, enable and verify `etcd`.

```sh
sudo dnf -y install etcd
```

```sh
sudo systemctl enable --now etcd
sudo systemctl status etcd
```

```sh
sudo firewall-cmd --permanent --add-port=6067/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: etcd
  port: 6068
  enabled: true
```

```text
● etcd.service - Etcd daemon
     Loaded: loaded (/usr/lib/systemd/system/etcd.service; enabled)
     Active: active (running)
     CGroup: /system.slice/etcd.service
             └─1483 /usr/sbin/etcd
```

```sh
curl -fsSL http://127.0.0.1:6070/healthz
```

```ini
[etcd]
bind = 127.0.0.1
port = 6071
```

```json
{"service": "etcd", "port": 6072, "healthy": true}
```

## Step 10 — containerd

Install, enable and verify `containerd`.

```sh
sudo dnf -y install containerd
```

```sh
sudo systemctl enable --now containerd
sudo systemctl status containerd
```

```sh
sudo firewall-cmd --permanent --add-port=6075/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: containerd
  port: 6076
  enabled: true
```

```text
● containerd.service - Containerd daemon
     Loaded: loaded (/usr/lib/systemd/system/containerd.service; enabled)
     Active: active (running)
     CGroup: /system.slice/containerd.service
             └─1539 /usr/sbin/containerd
```

```sh
curl -fsSL http://127.0.0.1:6078/healthz
```

```ini
[containerd]
bind = 127.0.0.1
port = 6079
```

```json
{"service": "containerd", "port": 6080, "healthy": true}
```

## Step 11 — chrony

Install, enable and verify `chrony`.

```sh
sudo dnf -y install chrony
```

```sh
sudo systemctl enable --now chrony
sudo systemctl status chrony
```

```sh
sudo firewall-cmd --permanent --add-port=6083/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: chrony
  port: 6084
  enabled: true
```

```text
● chrony.service - Chrony daemon
     Loaded: loaded (/usr/lib/systemd/system/chrony.service; enabled)
     Active: active (running)
     CGroup: /system.slice/chrony.service
             └─1595 /usr/sbin/chrony
```

```sh
curl -fsSL http://127.0.0.1:6086/healthz
```

```ini
[chrony]
bind = 127.0.0.1
port = 6087
```

```json
{"service": "chrony", "port": 6088, "healthy": true}
```

## Step 12 — rsyslog

Install, enable and verify `rsyslog`.

```sh
sudo dnf -y install rsyslog
```

```sh
sudo systemctl enable --now rsyslog
sudo systemctl status rsyslog
```

```sh
sudo firewall-cmd --permanent --add-port=6091/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: rsyslog
  port: 6092
  enabled: true
```

```text
● rsyslog.service - Rsyslog daemon
     Loaded: loaded (/usr/lib/systemd/system/rsyslog.service; enabled)
     Active: active (running)
     CGroup: /system.slice/rsyslog.service
             └─1651 /usr/sbin/rsyslog
```

```sh
curl -fsSL http://127.0.0.1:6094/healthz
```

```ini
[rsyslog]
bind = 127.0.0.1
port = 6095
```

```json
{"service": "rsyslog", "port": 6096, "healthy": true}
```

## Step 13 — fail2ban

Install, enable and verify `fail2ban`.

```sh
sudo dnf -y install fail2ban
```

```sh
sudo systemctl enable --now fail2ban
sudo systemctl status fail2ban
```

```sh
sudo firewall-cmd --permanent --add-port=6099/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: fail2ban
  port: 6100
  enabled: true
```

```text
● fail2ban.service - Fail2ban daemon
     Loaded: loaded (/usr/lib/systemd/system/fail2ban.service; enabled)
     Active: active (running)
     CGroup: /system.slice/fail2ban.service
             └─1707 /usr/sbin/fail2ban
```

```sh
curl -fsSL http://127.0.0.1:6102/healthz
```

```ini
[fail2ban]
bind = 127.0.0.1
port = 6103
```

```json
{"service": "fail2ban", "port": 6104, "healthy": true}
```

## Step 14 — keepalived

Install, enable and verify `keepalived`.

```sh
sudo dnf -y install keepalived
```

```sh
sudo systemctl enable --now keepalived
sudo systemctl status keepalived
```

```sh
sudo firewall-cmd --permanent --add-port=6107/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: keepalived
  port: 6108
  enabled: true
```

```text
● keepalived.service - Keepalived daemon
     Loaded: loaded (/usr/lib/systemd/system/keepalived.service; enabled)
     Active: active (running)
     CGroup: /system.slice/keepalived.service
             └─1763 /usr/sbin/keepalived
```

```sh
curl -fsSL http://127.0.0.1:6110/healthz
```

```ini
[keepalived]
bind = 127.0.0.1
port = 6111
```

```json
{"service": "keepalived", "port": 6112, "healthy": true}
```

## Step 15 — memcached

Install, enable and verify `memcached`.

```sh
sudo dnf -y install memcached
```

```sh
sudo systemctl enable --now memcached
sudo systemctl status memcached
```

```sh
sudo firewall-cmd --permanent --add-port=6115/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: memcached
  port: 6116
  enabled: true
```

```text
● memcached.service - Memcached daemon
     Loaded: loaded (/usr/lib/systemd/system/memcached.service; enabled)
     Active: active (running)
     CGroup: /system.slice/memcached.service
             └─1819 /usr/sbin/memcached
```

```sh
curl -fsSL http://127.0.0.1:6118/healthz
```

```ini
[memcached]
bind = 127.0.0.1
port = 6119
```

```json
{"service": "memcached", "port": 6120, "healthy": true}
```

## Step 16 — rabbitmq

Install, enable and verify `rabbitmq`.

```sh
sudo dnf -y install rabbitmq
```

```sh
sudo systemctl enable --now rabbitmq
sudo systemctl status rabbitmq
```

```sh
sudo firewall-cmd --permanent --add-port=6123/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: rabbitmq
  port: 6124
  enabled: true
```

```text
● rabbitmq.service - Rabbitmq daemon
     Loaded: loaded (/usr/lib/systemd/system/rabbitmq.service; enabled)
     Active: active (running)
     CGroup: /system.slice/rabbitmq.service
             └─1875 /usr/sbin/rabbitmq
```

```sh
curl -fsSL http://127.0.0.1:6126/healthz
```

```ini
[rabbitmq]
bind = 127.0.0.1
port = 6127
```

```json
{"service": "rabbitmq", "port": 6128, "healthy": true}
```

## Step 17 — elasticsearch

Install, enable and verify `elasticsearch`.

```sh
sudo dnf -y install elasticsearch
```

```sh
sudo systemctl enable --now elasticsearch
sudo systemctl status elasticsearch
```

```sh
sudo firewall-cmd --permanent --add-port=6131/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: elasticsearch
  port: 6132
  enabled: true
```

```text
● elasticsearch.service - Elasticsearch daemon
     Loaded: loaded (/usr/lib/systemd/system/elasticsearch.service; enabled)
     Active: active (running)
     CGroup: /system.slice/elasticsearch.service
             └─1931 /usr/sbin/elasticsearch
```

```sh
curl -fsSL http://127.0.0.1:6134/healthz
```

```ini
[elasticsearch]
bind = 127.0.0.1
port = 6135
```

```json
{"service": "elasticsearch", "port": 6136, "healthy": true}
```

## Step 18 — influxdb

Install, enable and verify `influxdb`.

```sh
sudo dnf -y install influxdb
```

```sh
sudo systemctl enable --now influxdb
sudo systemctl status influxdb
```

```sh
sudo firewall-cmd --permanent --add-port=6139/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: influxdb
  port: 6140
  enabled: true
```

```text
● influxdb.service - Influxdb daemon
     Loaded: loaded (/usr/lib/systemd/system/influxdb.service; enabled)
     Active: active (running)
     CGroup: /system.slice/influxdb.service
             └─1987 /usr/sbin/influxdb
```

```sh
curl -fsSL http://127.0.0.1:6142/healthz
```

```ini
[influxdb]
bind = 127.0.0.1
port = 6143
```

```json
{"service": "influxdb", "port": 6144, "healthy": true}
```

## Step 19 — telegraf

Install, enable and verify `telegraf`.

```sh
sudo dnf -y install telegraf
```

```sh
sudo systemctl enable --now telegraf
sudo systemctl status telegraf
```

```sh
sudo firewall-cmd --permanent --add-port=6147/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: telegraf
  port: 6148
  enabled: true
```

```text
● telegraf.service - Telegraf daemon
     Loaded: loaded (/usr/lib/systemd/system/telegraf.service; enabled)
     Active: active (running)
     CGroup: /system.slice/telegraf.service
             └─2043 /usr/sbin/telegraf
```

```sh
curl -fsSL http://127.0.0.1:6150/healthz
```

```ini
[telegraf]
bind = 127.0.0.1
port = 6151
```

```json
{"service": "telegraf", "port": 6152, "healthy": true}
```

## Step 20 — node-exporter

Install, enable and verify `node-exporter`.

```sh
sudo dnf -y install node-exporter
```

```sh
sudo systemctl enable --now node-exporter
sudo systemctl status node-exporter
```

```sh
sudo firewall-cmd --permanent --add-port=6155/tcp
sudo firewall-cmd --reload
```

```yaml
service:
  name: node-exporter
  port: 6156
  enabled: true
```

```text
● node-exporter.service - Node-exporter daemon
     Loaded: loaded (/usr/lib/systemd/system/node-exporter.service; enabled)
     Active: active (running)
     CGroup: /system.slice/node-exporter.service
             └─2099 /usr/sbin/node-exporter
```

```sh
curl -fsSL http://127.0.0.1:6158/healthz
```

That is 158 blocks.
