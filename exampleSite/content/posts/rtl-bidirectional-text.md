---
title: "تثبيت Redis على Ubuntu — RTL fixture"
date: 2026-07-24
description: "Right-to-left prose wrapped around left-to-right commands: the bidirectional case a code-first theme has to get right."
tags: ["fixtures", "i18n"]
categories: ["Meta"]
params:
  direction: rtl
---

<!--
  RTL FIXTURE — specs/007 §2 Layer 1, row "RTL context".

  PARTIAL. A complete RTL test needs `dir="rtl"` on <html>, which per docs/contracts.md §3 is
  configured per language:

      [languages.ar]
        languageName = "العربية"
        weight = 2
        [languages.ar.params]
          direction = "rtl"

  `exampleSite/hugo.toml` is owned by the templates workstream (docs/contracts.md §1 C), so this
  page cannot add it. Requested in the PR that introduced this file.

  What this page DOES exercise without any config change, and what actually breaks in practice:

    * Bidi mixing inside prose — Arabic sentences containing LTR identifiers like `redis-server`
      and `/etc/redis/redis.conf`. The neutral characters around them resolve by surrounding
      direction, so a slash or a full stop lands on the wrong side and the path reads backwards.
    * Code blocks inside RTL prose. A `<pre>` MUST stay `direction: ltr` and MUST stay left-aligned
      regardless of the paragraph direction around it, or every command in the post is unreadable.
      This is the single most common RTL bug in themes that support RTL at all.
    * Punctuation and digits at a direction boundary.
    * Headings, lists and tables with mixed-direction cells.
-->

هذه صفحة اختبارية للنص ثنائي الاتجاه. النص العربي يُقرأ من اليمين إلى اليسار، بينما الأوامر
والمسارات مثل `/etc/redis/redis.conf` و `redis-server` تبقى من اليسار إلى اليمين. النقطة الحرجة هي
أن كتلة الشيفرة يجب أن تبقى محاذاة إلى اليسار دائمًا.

## التثبيت

كتلة الشيفرة التالية يجب أن تُعرض من اليسار إلى اليمين، ومحاذاة إلى اليسار، حتى داخل فقرة عربية.

```sh
sudo apt-get update
sudo apt-get install -y redis-server
```

## التحقق

بعد التثبيت، شغّل الأمر `systemctl status redis-server` للتحقق. الإخراج التالي يحتوي على رموز رسم
الصناديق `└ ├ ─ ●` التي يجب أن تحافظ على محاذاتها.

```text
● redis-server.service - Advanced key-value store
     Loaded: loaded (/lib/systemd/system/redis-server.service; enabled)
     Active: active (running) since Fri 2026-07-24 08:02:11 UTC; 2h 14min ago
   Main PID: 2041 (redis-server)
      Tasks: 5 (limit: 4915)
     CGroup: /system.slice/redis-server.service
             └─2041 /usr/bin/redis-server 127.0.0.1:6379
```

## الإعدادات

| الإعداد | القيمة | ملاحظة |
|---|---|---|
| `bind` | `127.0.0.1` | لا تعرضه على الشبكة العامة |
| `maxmemory` | `256mb` | يعتمد على حجم الخادم |
| `appendonly` | `yes` | مطلوب للاستمرارية |

## خطوات

1. حدّث فهرس الحزم بالأمر `apt-get update`
2. ثبّت الحزمة `redis-server`
3. عدّل الملف `/etc/redis/redis.conf`
4. أعد تشغيل الخدمة

## English paragraph inside an RTL document

An LTR paragraph sitting inside an otherwise RTL page, with `inline code` and a
[link](https://gohugo.io/). Both directions have to coexist on one page, because real
multilingual technical writing does exactly this.
