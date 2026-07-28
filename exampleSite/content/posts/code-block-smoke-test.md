---
title: "Code block smoke test"
date: 2026-07-28
description: "The Layer-1 code-block torture page: every fence shape the reference corpus contains, on one URL."
tags: ["fixtures", "code"]
categories: ["Meta"]
---

The Layer-1 torture page from
[specs/007 §2](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/007-verification.md).
Every fence shape the 9,046-block reference corpus actually contains lives on this one URL, so a
regression in the render hook shows up on a single page rather than being spread across the fixture
set. Cases that need their own page — 158 blocks, a 767-line block, RTL, tables, prose — are
separate posts; `scripts/check_fixtures.py` asserts every property named here is still true.

Deliberately **not** here: a malformed fence. specs/007 §2 says not to preserve one as a fixture —
it is a content bug fixed upstream, and malformed source is only worth testing synthetically where
the renderer has a defined fallback.

## One line — 45.2% of the corpus

```sh
sudo dnf -y install redis
```

## Two lines — with one and two, 57.0% of the corpus

```sh
sudo systemctl enable --now redis
sudo systemctl status redis
```

## Three lines

```sh
sudo dnf -y install redis
sudo systemctl enable --now redis
redis-cli ping
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

## Unsupported language — lexer fallback

Chroma has no lexer for this. With `guessSyntax = false` it must fall back to plain text and still
render the full chrome, rather than erroring or dropping the block. Real posts do this constantly
with vendor DSLs and made-up tags.

```frobnicate-9000
frobnicate --with-vigour --target /dev/null
```

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

## The longest line in the corpus — exactly 854 characters

The single widest line across all 9,046 blocks is 854 characters. It is the worst case for REQ-CB-5
horizontal scrolling, for the copy button's position when the block is scrolled right, and for the
wrap toggle. `scripts/check_fixtures.py` asserts the line below is still exactly 854 characters, so
a well-meaning reflow cannot quietly weaken this fixture.

```sh
ansible all -i inventory/production.ini --become --become-method=sudo --become-user=root -m ansible.builtin.apt -a "upgrade=dist update_cache=yes cache_valid_time=3600 autoremove=yes autoclean=yes force_apt_get=yes dpkg_options=force-confdef,force-confold" --extra-vars '{"reboot_if_required": true, "reboot_timeout": 600, "serial_batch": "25%", "notify_channel": "#ops-alerts", "maintenance_owner": "platform-eng"}' --limit 'debian_hosts:&production:!maintenance_window' --forks 250 --timeout 600 --ssh-common-args='-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o ControlMaster=auto -o ControlPersist=60s -o ServerAliveInterval=15 -o ServerAliveCountMax=3' --private-key ~/.ssh/id_ed25519_ansible --vault-password-file ~/.ansible/vault-pass.txt --skip-tags 'reboot,kernel,grub' --tags 'apt,security' --diff --check --one-line -vvv
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

## Prompt-prefixed console block — Q2 copy semantics

79% of the corpus is shell, and a large share of it is pasted with a `$` prompt still attached.
Copying the prompt gives the reader a command that does not run. `{prompt="$"}` declares the prefix
so the copy button can strip it.

**Not implemented yet.** `prompt` is an unknown key to Chroma, so it lands in `.Attributes`
([contracts §3](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/contracts.md)) and the
current hook ignores it — this renders as an ordinary block. That is the correct intermediate state:
the fixture is here so the behaviour has somewhere to land, and so the day it lands the visual diff
shows it.

```console {prompt="$"}
$ redis-cli --version
redis-cli 7.2.4 (git:00000000)
$ redis-cli ping
PONG
```

## Output block — Q3 output treatment

`{output=true}` marks a block as program output rather than something to run: no copy button, no
prompt handling, and it should read as a result rather than an instruction. Also unimplemented, also
in `.Attributes`, also renders as an ordinary block today.

```text {output=true}
Non-existent process ID 1183
redis-server is not running
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

## Cases that are not on this page, and why

Three Layer-1 rows from specs/007 §2 cannot be expressed as content in this site:

- **Bare `<pre>` via unsafe HTML.** `exampleSite/hugo.toml` sets
  `markup.goldmark.renderer.unsafe = false`, which is deliberate — specs/007 §3.5 requires the
  build to pass with `unsafe: false`. Raw HTML is therefore replaced with a comment and the fixture
  would silently test nothing. The indented block above already exercises the same styling path
  (bare `pre > code`, no hook, REQ-CB-8). Turning it into a real fixture needs a second build
  configuration; see `docs/verification.md`.
- **Clipboard-unavailable context.** REQ-CB-4's fallback triggers on an insecure origin or a denied
  permission. That is a browser state, not page content, so it belongs to the Playwright suite.
- **Tabs shortcode.** `layouts/shortcodes/` is owned by the templates workstream and is still empty.
  A `{{</* tabs */>}}` call in content is a hard build failure, not a graceful degradation, so the
  fixture waits for the shortcode.
