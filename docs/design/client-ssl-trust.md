# Client SSL Trust

**Description:** Why bring-our-own-Python builds trust the bundled certifi store ONLY (cafile= skips the OS store), the Windows expired-legacy-root failure it prevents, and the BA_USE_SYSTEM_CERTS escape hatch.

In builds that bring their own Python distribution, client TLS trust
comes from the bundled certifi store and nothing else — the OS
certificate store is deliberately never loaded. This page records the
mechanism, the concrete Windows failure that motivated it, and the
escape hatch for environments that genuinely need OS-store roots.

## Policy and mechanism

- **`baenv._setup_certs`**
  (`src/assets/ba_data/python/baenv.py`) — in bring-our-own-Python
  builds (`contains_python_dist`, or forced via
  `BA_USE_BUNDLED_ROOT_CERTS=1`) it sets
  `SSL_CERT_FILE = REQUESTS_CA_BUNDLE = certifi.where()`.
- **The single shared SSL context** is built in
  `babase/_env.py` `_bootstrap_networking`
  (`_g_net_warm_start_ssl_context`, exposed as `app.net.sslcontext` +
  `app.net.urllib3pool`; all client HTTPS funnels through that pool).
  When `SSL_CERT_FILE` is set (and the escape hatch below isn't), it
  builds the context via
  `ssl.create_default_context(cafile=SSL_CERT_FILE)`.
- **The load-bearing detail: passing `cafile=` makes CPython skip
  `load_default_certs()`**, so the OS cert store is fully out of the
  loop — trust is the bundled certifi set only, on every platform.
- `v2transport` reuses `app.net.sslcontext` rather than minting its own
  context (commit `ed79b46600`) — its old inline
  `create_default_context()` was a leftover from the private-CA `cadata`
  days, obsolete since basn nodes moved to public Let's Encrypt certs.

## Why: the Windows expired-legacy-root failure

Only win32 ever loaded the OS cert store — CPython's
`load_default_certs()` enumerates the system store on Windows only, so
mac/Linux/Android/iOS were already effectively certifi-only. The change
brings Windows in line rather than taking anything away elsewhere.

The failure it prevents: expired legacy roots lingering in a user's
Windows store (DST Root CA X3, the expired ISRG Root X2 cross-sign,
stale R3/E1 intermediates) **poison OpenSSL chain-building**. OpenSSL
anchors on the expired duplicate and rejects a currently-valid Let's
Encrypt basn-node cert with `CERT_HAS_EXPIRED`, even though a valid
ISRG X2 exists in certifi. Browsers (Chrome/Edge via CryptoAPI,
Firefox via mozilla::pkix) do robust alternate-path chain building and
don't trip on this; OpenSSL does not — so we feed it a clean store.

## Escape hatch

`BA_USE_SYSTEM_CERTS=1` reverts to a bare `create_default_context()`
(OS store trust). This exists for corporate/AV TLS-inspection proxy
environments whose MITM root lives only in the system store.

## Diagnostic signature and rule-outs

The characteristic symptom: WSS to `*.basn.ballistica.net` (Let's
Encrypt cert) fails with `CERT_HAS_EXPIRED` while HTTPS to
`regional.ballistica.net` (Amazon cert) succeeds — e.g. the game stuck
in construct-mode. Rule-outs before blaming the OS store:

- **Not the clock** — the browser uses the same clock and works; a
  wrong clock also yields "not yet valid", not "expired".
- **Not the server** — `curl -sv https://prod-<id>.basn.ballistica.net/`
  shows `verify ok` with valid dates.
- **Not stale bundled certifi** — verify it carries current ISRG
  X1/X2 and zero expired anchors.

Confirm the OS store on Windows with PowerShell:

```powershell
Get-ChildItem Cert:\LocalMachine\Root,Cert:\CurrentUser\Root,Cert:\LocalMachine\CA,Cert:\CurrentUser\CA | ? {$_.NotAfter -lt (Get-Date)}
```

Gotcha: **Firefox uses its own Mozilla/NSS store** and ignores the
Windows store by default (enterprise-roots auto-import aside), so it's
the wrong browser for testing an OS-store issue — use Edge or Chrome
(CryptoAPI).

## Deferred alternative

A curated cross-platform trust set — certifi plus only the
*non-expired* OS roots — was considered and deferred in favor of
certifi-only simplicity/consistency. We don't bundle `cryptography`,
so date-filtering OS roots would need `ssl.enum_certificates`
(win-only) plus `_test_decode_cert` or a hand-rolled ASN.1 read.
Revisit only if the corporate/AV MITM population ever proves to
matter beyond what `BA_USE_SYSTEM_CERTS` covers.
