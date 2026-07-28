---
title: "A 767-line redis.conf"
date: 2026-07-26
description: "The long-block fixture — one fenced block of exactly 767 lines, the corpus maximum."
tags: ["fixtures", "code"]
categories: ["Meta"]
---

**Generated fixture — do not hand-edit.** Regenerate with
`python3 scripts/check_fixtures.py --regenerate`.

One fenced block, **exactly 767 lines** — the longest single block in the reference corpus.
Three things only go wrong at this length: the copy button scrolls out of reach when the
block is taller than the viewport (REQ-CB-3), a line-number gutter changes width at line 100
and again at line 1000 and pushes the code sideways mid-block, and syntax highlighting of
this many lines starts to show up in build time and page weight.

Nothing else is on this page, so anything measured here is attributable to the block.

The language tag is `ini`, which Chroma has a lexer for, deliberately. An unknown tag makes
Hugo emit a bare `<pre><code>` with no `div.highlight`, no `pre.chroma` and no
`span.line` wrappers at all — see the unsupported-language case on the smoke-test page — so a
767-line block tagged with one would measure the cost of *not* highlighting.

```ini
# redis.conf — generated fixture, 767 lines exactly.
# Regenerate with: python3 scripts/check_fixtures.py --regenerate
#
# The reference corpus maximum for a single fenced block is 767 lines. A block this
# long is where the copy button scrolls out of reach, where a forced line-number
# gutter changes width at line 100, and where highlighting cost becomes visible.

################################## NETWORK #####################################

bind 127.0.0.1 -::1
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

################################### GENERAL ###################################

# Run as a foreground process; systemd supervises it.
daemonize no

# Signal readiness to the service manager.
supervised systemd

# Written before privileges drop.
pidfile /run/redis/redis-server.pid

# debug | verbose | notice | warning
loglevel notice

# Empty string logs to stdout.
logfile /var/log/redis/redis-server.log

# Logical databases, selected with SELECT.
databases 16

################################# SNAPSHOTTING #################################

# One change in fifteen minutes.
save 900 1

# Ten changes in five minutes.
save 300 10

# Ten thousand changes in one minute.
save 60 10000

# Fail loudly rather than losing data quietly.
stop-writes-on-bgsave-error yes

# LZF on string values inside the dump.
rdbcompression yes

# CRC64 at the end of the file.
rdbchecksum yes

# Relative to dir below.
dbfilename dump.rdb

# Working directory for the dump and the AOF.
dir /var/lib/redis

################################# REPLICATION #################################

# Serve reads during a link outage.
replica-serve-stale-data yes

# Writes to a replica are refused.
replica-read-only yes

# Stream the RDB rather than staging it on disk.
repl-diskless-sync yes

# Wait to batch arriving replicas.
repl-diskless-sync-delay 5

# Latency over bandwidth.
repl-disable-tcp-nodelay no

# Lower wins a failover election.
replica-priority 100

################################### SECURITY ###################################

# Retained ACL security events.
acllog-max-len 128

# Placeholder; never a real credential.
requirepass CHANGE_ME_IN_PRODUCTION

################################### CLIENTS ###################################

# Bounded by the file-descriptor limit.
maxclients 10000

############################## MEMORY MANAGEMENT ##############################

# Size to the box, not to the default.
maxmemory 256mb

# Cache workload; use noeviction for a store.
maxmemory-policy allkeys-lru

# Approximation quality for LRU and LFU.
maxmemory-samples 5

# Eviction is driven by the primary.
replica-ignore-maxmemory yes

################################# LAZY FREEING #################################

lazyfree-lazy-eviction no

lazyfree-lazy-expire no

lazyfree-lazy-server-del no

replica-lazy-flush no

lazyfree-lazy-user-del no

lazyfree-lazy-user-flush no

############################### APPEND ONLY MODE ###############################

# Durability beyond the RDB snapshot interval.
appendonly yes

appendfilename "appendonly.aof"

appenddirname "appendonlydir"

# always | everysec | no
appendfsync everysec

no-appendfsync-on-rewrite no

auto-aof-rewrite-percentage 100

auto-aof-rewrite-min-size 64mb

aof-load-truncated yes

aof-use-rdb-preamble yes

aof-timestamp-enabled no

################################### SLOW LOG ###################################

# Microseconds.
slowlog-log-slower-than 10000

slowlog-max-len 128

############################### LATENCY MONITOR ###############################

# Zero disables the monitor.
latency-monitor-threshold 0

latency-tracking yes

latency-tracking-info-percentiles 50 99 99.9

############################## EVENT NOTIFICATION ##############################

# Costs CPU; enable only what is consumed.
notify-keyspace-events ""

############################### ADVANCED CONFIG ###############################

hash-max-listpack-entries 128

hash-max-listpack-value 64

list-max-listpack-size -2

list-compress-depth 0

set-max-intset-entries 512

set-max-listpack-entries 128

set-max-listpack-value 64

zset-max-listpack-entries 128

zset-max-listpack-value 64

hll-sparse-max-bytes 3000

stream-node-max-bytes 4096

stream-node-max-entries 100

activerehashing yes

client-output-buffer-limit normal 0 0 0

client-output-buffer-limit replica 256mb 64mb 60

client-output-buffer-limit pubsub 32mb 8mb 60

hz 10

dynamic-hz yes

aof-rewrite-incremental-fsync yes

rdb-save-incremental-fsync yes

jemalloc-bg-thread yes

############################# GENERAL (instance 2) #############################

# Run as a foreground process; systemd supervises it.
instance2-daemonize no

# Signal readiness to the service manager.
instance2-supervised systemd

# Written before privileges drop.
instance2-pidfile /run/redis/redis-server.pid

# debug | verbose | notice | warning
instance2-loglevel notice

# Empty string logs to stdout.
instance2-logfile /var/log/redis/redis-server.log

# Logical databases, selected with SELECT.
instance2-databases 16

########################## SNAPSHOTTING (instance 2) ##########################

# One change in fifteen minutes.
instance2-save 900 1

# Ten changes in five minutes.
instance2-save 300 10

# Ten thousand changes in one minute.
instance2-save 60 10000

# Fail loudly rather than losing data quietly.
instance2-stop-writes-on-bgsave-error yes

# LZF on string values inside the dump.
instance2-rdbcompression yes

# CRC64 at the end of the file.
instance2-rdbchecksum yes

# Relative to dir below.
instance2-dbfilename dump.rdb

# Working directory for the dump and the AOF.
instance2-dir /var/lib/redis

########################### REPLICATION (instance 2) ###########################

# Serve reads during a link outage.
instance2-replica-serve-stale-data yes

# Writes to a replica are refused.
instance2-replica-read-only yes

# Stream the RDB rather than staging it on disk.
instance2-repl-diskless-sync yes

# Wait to batch arriving replicas.
instance2-repl-diskless-sync-delay 5

# Latency over bandwidth.
instance2-repl-disable-tcp-nodelay no

# Lower wins a failover election.
instance2-replica-priority 100

############################ SECURITY (instance 2) ############################

# Retained ACL security events.
instance2-acllog-max-len 128

# Placeholder; never a real credential.
instance2-requirepass CHANGE_ME_IN_PRODUCTION

############################# CLIENTS (instance 2) #############################

# Bounded by the file-descriptor limit.
instance2-maxclients 10000

######################## MEMORY MANAGEMENT (instance 2) ########################

# Size to the box, not to the default.
instance2-maxmemory 256mb

# Cache workload; use noeviction for a store.
instance2-maxmemory-policy allkeys-lru

# Approximation quality for LRU and LFU.
instance2-maxmemory-samples 5

# Eviction is driven by the primary.
instance2-replica-ignore-maxmemory yes

########################## LAZY FREEING (instance 2) ##########################

instance2-lazyfree-lazy-eviction no

instance2-lazyfree-lazy-expire no

instance2-lazyfree-lazy-server-del no

instance2-replica-lazy-flush no

instance2-lazyfree-lazy-user-del no

instance2-lazyfree-lazy-user-flush no

######################## APPEND ONLY MODE (instance 2) ########################

# Durability beyond the RDB snapshot interval.
instance2-appendonly yes

instance2-appendfilename "appendonly.aof"

instance2-appenddirname "appendonlydir"

# always | everysec | no
instance2-appendfsync everysec

instance2-no-appendfsync-on-rewrite no

instance2-auto-aof-rewrite-percentage 100

instance2-auto-aof-rewrite-min-size 64mb

instance2-aof-load-truncated yes

instance2-aof-use-rdb-preamble yes

instance2-aof-timestamp-enabled no

############################ SLOW LOG (instance 2) ############################

# Microseconds.
instance2-slowlog-log-slower-than 10000

instance2-slowlog-max-len 128

######################### LATENCY MONITOR (instance 2) #########################

# Zero disables the monitor.
instance2-latency-monitor-threshold 0

instance2-latency-tracking yes

instance2-latency-tracking-info-percentiles 50 99 99.9

####################### EVENT NOTIFICATION (instance 2) #######################

# Costs CPU; enable only what is consumed.
instance2-notify-keyspace-events ""

######################### ADVANCED CONFIG (instance 2) #########################

instance2-hash-max-listpack-entries 128

instance2-hash-max-listpack-value 64

instance2-list-max-listpack-size -2

instance2-list-compress-depth 0

instance2-set-max-intset-entries 512

instance2-set-max-listpack-entries 128

instance2-set-max-listpack-value 64

instance2-zset-max-listpack-entries 128

instance2-zset-max-listpack-value 64

instance2-hll-sparse-max-bytes 3000

instance2-stream-node-max-bytes 4096

instance2-stream-node-max-entries 100

instance2-activerehashing yes

instance2-client-output-buffer-limit normal 0 0 0

instance2-client-output-buffer-limit replica 256mb 64mb 60

instance2-client-output-buffer-limit pubsub 32mb 8mb 60

instance2-hz 10

instance2-dynamic-hz yes

instance2-aof-rewrite-incremental-fsync yes

instance2-rdb-save-incremental-fsync yes

instance2-jemalloc-bg-thread yes

############################# GENERAL (instance 3) #############################

# Run as a foreground process; systemd supervises it.
instance3-daemonize no

# Signal readiness to the service manager.
instance3-supervised systemd

# Written before privileges drop.
instance3-pidfile /run/redis/redis-server.pid

# debug | verbose | notice | warning
instance3-loglevel notice

# Empty string logs to stdout.
instance3-logfile /var/log/redis/redis-server.log

# Logical databases, selected with SELECT.
instance3-databases 16

########################## SNAPSHOTTING (instance 3) ##########################

# One change in fifteen minutes.
instance3-save 900 1

# Ten changes in five minutes.
instance3-save 300 10

# Ten thousand changes in one minute.
instance3-save 60 10000

# Fail loudly rather than losing data quietly.
instance3-stop-writes-on-bgsave-error yes

# LZF on string values inside the dump.
instance3-rdbcompression yes

# CRC64 at the end of the file.
instance3-rdbchecksum yes

# Relative to dir below.
instance3-dbfilename dump.rdb

# Working directory for the dump and the AOF.
instance3-dir /var/lib/redis

########################### REPLICATION (instance 3) ###########################

# Serve reads during a link outage.
instance3-replica-serve-stale-data yes

# Writes to a replica are refused.
instance3-replica-read-only yes

# Stream the RDB rather than staging it on disk.
instance3-repl-diskless-sync yes

# Wait to batch arriving replicas.
instance3-repl-diskless-sync-delay 5

# Latency over bandwidth.
instance3-repl-disable-tcp-nodelay no

# Lower wins a failover election.
instance3-replica-priority 100

############################ SECURITY (instance 3) ############################

# Retained ACL security events.
instance3-acllog-max-len 128

# Placeholder; never a real credential.
instance3-requirepass CHANGE_ME_IN_PRODUCTION

############################# CLIENTS (instance 3) #############################

# Bounded by the file-descriptor limit.
instance3-maxclients 10000

######################## MEMORY MANAGEMENT (instance 3) ########################

# Size to the box, not to the default.
instance3-maxmemory 256mb

# Cache workload; use noeviction for a store.
instance3-maxmemory-policy allkeys-lru

# Approximation quality for LRU and LFU.
instance3-maxmemory-samples 5

# Eviction is driven by the primary.
instance3-replica-ignore-maxmemory yes

########################## LAZY FREEING (instance 3) ##########################

instance3-lazyfree-lazy-eviction no

instance3-lazyfree-lazy-expire no

instance3-lazyfree-lazy-server-del no

instance3-replica-lazy-flush no

instance3-lazyfree-lazy-user-del no

instance3-lazyfree-lazy-user-flush no

######################## APPEND ONLY MODE (instance 3) ########################

# Durability beyond the RDB snapshot interval.
instance3-appendonly yes

instance3-appendfilename "appendonly.aof"

instance3-appenddirname "appendonlydir"

# always | everysec | no
instance3-appendfsync everysec

instance3-no-appendfsync-on-rewrite no

instance3-auto-aof-rewrite-percentage 100

instance3-auto-aof-rewrite-min-size 64mb

instance3-aof-load-truncated yes

instance3-aof-use-rdb-preamble yes

instance3-aof-timestamp-enabled no

############################ SLOW LOG (instance 3) ############################

# Microseconds.
instance3-slowlog-log-slower-than 10000

instance3-slowlog-max-len 128

######################### LATENCY MONITOR (instance 3) #########################

# Zero disables the monitor.
instance3-latency-monitor-threshold 0

instance3-latency-tracking yes

instance3-latency-tracking-info-percentiles 50 99 99.9

####################### EVENT NOTIFICATION (instance 3) #######################

# Costs CPU; enable only what is consumed.
instance3-notify-keyspace-events ""

######################### ADVANCED CONFIG (instance 3) #########################

instance3-hash-max-listpack-entries 128

instance3-hash-max-listpack-value 64

instance3-list-max-listpack-size -2

instance3-list-compress-depth 0

instance3-set-max-intset-entries 512

instance3-set-max-listpack-entries 128

instance3-set-max-listpack-value 64

instance3-zset-max-listpack-entries 128

instance3-zset-max-listpack-value 64

instance3-hll-sparse-max-bytes 3000

instance3-stream-node-max-bytes 4096

instance3-stream-node-max-entries 100

instance3-activerehashing yes

instance3-client-output-buffer-limit normal 0 0 0

instance3-client-output-buffer-limit replica 256mb 64mb 60

instance3-client-output-buffer-limit pubsub 32mb 8mb 60

instance3-hz 10

instance3-dynamic-hz yes

instance3-aof-rewrite-incremental-fsync yes

instance3-rdb-save-incremental-fsync yes

instance3-jemalloc-bg-thread yes

############################# GENERAL (instance 4) #############################

# Run as a foreground process; systemd supervises it.
instance4-daemonize no

# Signal readiness to the service manager.
instance4-supervised systemd

# Written before privileges drop.
instance4-pidfile /run/redis/redis-server.pid

# debug | verbose | notice | warning
instance4-loglevel notice

# Empty string logs to stdout.
instance4-logfile /var/log/redis/redis-server.log

# Logical databases, selected with SELECT.
instance4-databases 16

########################## SNAPSHOTTING (instance 4) ##########################

# One change in fifteen minutes.
instance4-save 900 1

# Ten changes in five minutes.
instance4-save 300 10

# Ten thousand changes in one minute.
instance4-save 60 10000

# Fail loudly rather than losing data quietly.
instance4-stop-writes-on-bgsave-error yes

# LZF on string values inside the dump.
instance4-rdbcompression yes

# CRC64 at the end of the file.
instance4-rdbchecksum yes

# Relative to dir below.
instance4-dbfilename dump.rdb

# Working directory for the dump and the AOF.
instance4-dir /var/lib/redis

########################### REPLICATION (instance 4) ###########################

# Serve reads during a link outage.
instance4-replica-serve-stale-data yes

# Writes to a replica are refused.
instance4-replica-read-only yes

# Stream the RDB rather than staging it on disk.
instance4-repl-diskless-sync yes

# Wait to batch arriving replicas.
instance4-repl-diskless-sync-delay 5

# Latency over bandwidth.
instance4-repl-disable-tcp-nodelay no

# Lower wins a failover election.
instance4-replica-priority 100

############################ SECURITY (instance 4) ############################

# Retained ACL security events.
instance4-acllog-max-len 128

# Placeholder; never a real credential.
instance4-requirepass CHANGE_ME_IN_PRODUCTION

############################# CLIENTS (instance 4) #############################

# Bounded by the file-descriptor limit.
instance4-maxclients 10000

######################## MEMORY MANAGEMENT (instance 4) ########################

# Size to the box, not to the default.
instance4-maxmemory 256mb

# Cache workload; use noeviction for a store.
instance4-maxmemory-policy allkeys-lru

# Approximation quality for LRU and LFU.
instance4-maxmemory-samples 5

# Eviction is driven by the primary.
instance4-replica-ignore-maxmemory yes

########################## LAZY FREEING (instance 4) ##########################

instance4-lazyfree-lazy-eviction no

instance4-lazyfree-lazy-expire no

instance4-lazyfree-lazy-server-del no

instance4-replica-lazy-flush no

instance4-lazyfree-lazy-user-del no

instance4-lazyfree-lazy-user-flush no

######################## APPEND ONLY MODE (instance 4) ########################

# Durability beyond the RDB snapshot interval.
instance4-appendonly yes

instance4-appendfilename "appendonly.aof"

instance4-appenddirname "appendonlydir"

# always | everysec | no
instance4-appendfsync everysec

instance4-no-appendfsync-on-rewrite no

instance4-auto-aof-rewrite-percentage 100

instance4-auto-aof-rewrite-min-size 64mb

instance4-aof-load-truncated yes

instance4-aof-use-rdb-preamble yes

instance4-aof-timestamp-enabled no

############################ SLOW LOG (instance 4) ############################

# Microseconds.
instance4-slowlog-log-slower-than 10000

instance4-slowlog-max-len 128

######################### LATENCY MONITOR (instance 4) #########################

# Zero disables the monitor.
instance4-latency-monitor-threshold 0

instance4-latency-tracking yes

instance4-latency-tracking-info-percentiles 50 99 99.9

####################### EVENT NOTIFICATION (instance 4) #######################

# Costs CPU; enable only what is consumed.
instance4-notify-keyspace-events ""

######################### ADVANCED CONFIG (instance 4) #########################

instance4-hash-max-listpack-entries 128

instance4-hash-max-listpack-value 64

instance4-list-max-listpack-size -2

instance4-list-compress-depth 0

instance4-set-max-intset-entries 512
```
