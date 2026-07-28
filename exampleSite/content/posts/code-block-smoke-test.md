---
title: "Code block smoke test"
date: 2026-07-28
description: "A minimal subset of the code-block fixture set, enough to keep the foundation honest."
tags: ["fixtures", "code"]
categories: ["Meta"]
---

Seed fixtures only. The full torture page from
[specs/007 §2 Layer 1](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/007-verification.md)
is owned by the fixtures workstream — this page exists so the foundation build is verifiable, not to
replace it.

## One line — 45.2% of the corpus

```sh
sudo dnf -y install redis
```

## Two lines — with one and two, 57.0% of the corpus

```sh
sudo systemctl enable --now redis
sudo systemctl status redis
```

## Untagged fence

`.Type` is an empty string here, not nil. 93 blocks in the reference corpus look like this.

```
PING
PONG
```

## Tilde fence

~~~
Also reaches the render hook.
~~~

## Line-number opt-in

Line numbers appear here because this block asked for them, and nowhere else — REQ-CB-1.

```python {linenos=true}
def deploy(host):
    run(host, "systemctl restart redis")
    return check(host)
```

## Highlighted lines and a filename

```yaml {file="docker-compose.yml" hl_lines="3-4"}
services:
  redis:
    image: redis:7
    restart: unless-stopped
    ports:
      - "6379:6379"
```

## Horizontal overflow — REQ-CB-5

1,586 blocks in the reference corpus carry a line over 80 characters. This must scroll, never wrap.

```sh
kubeadm join 10.0.0.1:6443 --token abcdef.0123456789abcdef --discovery-token-ca-cert-hash sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef --control-plane --certificate-key 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

## Box-drawing glyphs — REQ-FONT-1

221 posts (44% of the reference archive) contain `└ ├ ─ ●` across 1,177 lines. A Latin-only subset
renders these from the fallback font mid-block, breaking the alignment readers scan most carefully.

```text
● redis.service - Redis persistent key-value database
     Loaded: loaded (/usr/lib/systemd/system/redis.service; enabled)
     Active: active (running) since Tue 2026-07-28 09:14:22 UTC; 3h ago
   Main PID: 1183 (redis-server)
      Tasks: 5 (limit: 23404)
     CGroup: /system.slice/redis.service
             └─1183 /usr/bin/redis-server 127.0.0.1:6379
```

## Indented code — bypasses the render hook in every Hugo version

No copy button, no language tag and no wrap toggle is possible here. CSS is the only tool that
reaches it, which is why `pre > code` is the styled base case (REQ-CB-8).

    $ redis-cli ping
    PONG

## Inline code

Restart with `systemctl restart redis`, then check `redis-cli ping` returns `PONG`. Inline spans run
at 16.2 per post across the reference corpus, so they carry real weight and must never disturb the
prose baseline.
