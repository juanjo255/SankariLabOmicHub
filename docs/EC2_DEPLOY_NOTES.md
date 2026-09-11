# EC2 Deployment Notes (Sankari Lab instance)

Practical notes from standing up this fork on AWS EC2, on top of
`docs/DEPLOYMENT_GUIDE.md`. Written down because several of these are
non-obvious and cost real time to track down the first time.

## Current setup

- Instance: `i-0475e60d82fddd3b5` (us-east-2), Amazon Linux, user `ec2-user`.
- Access: **SSH over AWS SSM** (`aws ssm start-session --document-name
  AWS-StartSSHSession ...` as a `ProxyCommand`), no port 22 open publicly.
- App code: `~/miniodp/src` (a `git clone` of this fork - **not** `/opt/miniodp`,
  see below).
- Built Hugo output: `~/miniodp/hugo/public/` (includes JBrowse - see below).
- Dash: conda env (`environment.yml`) + gunicorn, run under systemd
  (`miniodp-dash.service`), not Docker.
- SequenceServer: same pattern - conda env + systemd
  (`miniodp-sequenceserver.service`).
- nginx: **loopback only** (`listen 127.0.0.1:80;`). This app has no login and
  no TLS, so it is intentionally not exposed to the public internet. Reach it
  via an SSH tunnel:
  ```bash
  ssh -L 8080:localhost:80 <your-ssh-alias>
  # then open http://localhost:8080/miniodp/
  ```

## Why `~/miniodp`, not `/opt/miniodp`

The deployment guide and `common/nginx/miniodp.conf` both assume `/opt/miniodp`.
On this box `/opt/miniodp` already existed, owned by another account (a
colleague's earlier deployment of a *different* miniODP instance - see below).
Fighting over ownership of `/opt` wasn't worth it: everything now lives under
`~/miniodp` instead, which needs no `sudo`/`chown`.

**Consequence:** nginx (running as its own system user) cannot read into your
home directory by default. Fix, once:
```bash
chmod 711 ~
chmod -R o+rX ~/miniodp
```
`711` lets processes pass *through* the home directory without listing its
contents; `o+rX` gives "other" read on files and traverse on directories,
recursively, without making anything spuriously executable.

## The two-nginx-config trap

There were (and may still be) **two separate files** both trying to own
`/miniodp/`:

- `/etc/nginx/conf.d/*.conf` - a standalone `server {}` block, matched by
  `server_name`.
- `/etc/nginx/default.d/*.conf` - bare `location` blocks, meant to be
  `include`d *inside* the stock default server block in `/etc/nginx/nginx.conf`
  (that's what `default.d` is for on RPM-based nginx installs).

A colleague's earlier setup left a `default.d/miniodp.conf` pointing at their
own `/opt/miniodp/...` paths. Since the SSH-tunnel loopback block is the
*default* server (`server_name _;`), it's the one that actually answers a
`localhost` request - so `default.d/miniodp.conf` wins, not any separate file
in `conf.d/`. **Only one `/miniodp/` config should exist at a time** - edit the
one that's actually being matched (check with `sudo nginx -T | grep -B2 listen`
and look at which block a given `location` sits inside), don't add a
competing one.

## `alias` + `try_files ... /miniodp/index.html` -> infinite redirect (500)

This specific, common-looking pattern:
```nginx
location /miniodp/ {
    alias /home/ec2-user/miniodp/hugo/public/;
    try_files $uri $uri/ /miniodp/index.html;
}
```
causes nginx to loop internally re-matching the fallback URI against the same
`alias`d location, eventually erroring with `500` and logging *"rewrite or
internal redirection cycle while internally redirecting to
/miniodp/index.html"*. Known nginx footgun with `alias` + an absolute
`try_files` fallback. If Hugo starts 500ing after an nginx edit, check
`/var/log/nginx/error.log` first - it names this exact error.

## Docker containers from a prior deployment

A colleague had already deployed a different miniODP instance on this same
box using the guide's Docker path:
```
miniodp-dash              127.0.0.1:3939
miniodp-sequenceserver    127.0.0.1:4567
```
same ports our conda services need. Stopped (not removed) with:
```bash
docker stop miniodp-dash miniodp-sequenceserver
```
Their compose file sets `restart: unless-stopped`, so once manually stopped
they stay stopped across reboots - `docker start miniodp-dash
miniodp-sequenceserver` brings them back if ever needed. Check `docker ps -a`
before assuming ports 3939/4567 are free on this box.

## JBrowse: config vs. browser state

If JBrowse says *"Assembly ... not found"* or shows an assembly/genome that
was never configured (e.g. an unrelated species): this is very rarely the
server. Confirm server-side first:
```bash
curl -s http://localhost/miniodp/jbrowse2/config.json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print([a['name'] for a in d.get('assemblies',[])])"
```
If that prints the right assembly, the problem is **browser-side**: JBrowse 2
persists session state in `localStorage` **and** `IndexedDB`, which a normal
refresh does not clear. Fix: DevTools -> Application/Storage -> "Clear site
data" for that origin, then fully quit and reopen the browser (not just the
tab).

Also watch for stray `?session=share-...&password=...` URLs in the address
bar/history/autocomplete - that's JBrowse's "Share" feature, which loads a
session from JBrowse's own public sharing server (`share.jbrowse.org` by
default), bypassing local `config.json` entirely. If you see an unrelated
assembly, check the URL isn't one of these before assuming anything is
misconfigured.

## What still needs installing on EC2 vs. can be shipped pre-built

To minimize what has to be set up on the instance itself:
- **Hugo**: not installed on EC2 at all. Build locally/on the HPC with the
  right `--baseURL`, `rsync` just `hugo/public/` over. Because of the
  `[[module.mounts]]` entry in `hugo/config/hugo_default.toml` (pulls
  `../jbrowse2/app` into `static/jbrowse2/`), this one folder already contains
  JBrowse too - no separate JBrowse install step needed on EC2.
- **BLAST databases**: built locally (`makeblastdb`, bioconda `blast` env) and
  rsynced as finished `.n*`/`.p*` index files. EC2 only needs the
  `sequenceserver` package itself, not the BLAST+ toolchain.
- **What EC2 does need**: nginx, conda/mamba, the `miniodp` env
  (`dash/environment.yml`) for Dash, and a `sequenceserver` env
  (`bioconda -c conda-forge sequenceserver`) for BLAST search.

## Data that is never in git (by design - size and unpublished-data privacy)

Rsync these separately after `git clone`, they are not part of the repo:
- `dash/data/` (except `species_adapters.toml`, which is tracked)
- `jbrowse2/app/` (the whole JBrowse web app + reference/track bundle)
- `sequenceserver/data/` (BLAST FASTA + index files)
- `hugo/public/` (build output, regenerate/rsync from source, never commit)
