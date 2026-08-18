# Client Log Reporting

**Description:** The triggered-window client log-report system — CloudVals spec/config, window mechanics, and the recipes for reading reports and driving investigations.

Shipped prod 2026-08-11 (build 22971 / 1.8.0a79). Clients ship a bounded
window of their engine log to the master server when a trigger fires;
reports land in Cloud Logging tagged `baSrc=client`.

## Spec + config

- `CloudValsTransient.log_report` carries a
  `bacommon.logreporting.LogReportSpec`: `trigger_level` (`tl`, LogLevel
  int value; WARNING=2) OR `trigger_phrases` (`tp`, substrings —
  deliberately no regex), `max_before_entries` (`mb`),
  `max_after_entries` (`ma`, None = rest of run). One window per run; no
  re-arming.
- Set per fleet via the "Client Log Report Spec (JSON)" field on
  `/fleetsettings` (the form POST needs `opfleet` as a FORM field, not a
  query param). Live on dev+prod: `{"tl": 2, "mb": 1000, "ma": 1000}`.
  Sourced from bamaster `FleetGlobals.client_log_report`.
- CloudVals split: `CloudValsPersistent` (config-cached; applies
  pre-connectivity next run; build-blind-safe values only) vs transient
  (per-run; server can tailor per build).

## Mechanics

- Pre-roll ships immediately on trigger (no arm delay); follow-up slices
  on a 5s poll; cursor advances only on confirmed sends
  (`send_message_future`); bounded 1.5s final flush at shutdown.
- Server dedupes overlap per `private_app_instance_uuid` (Valkey
  cursor); that uuid is also a `logextra` option
  (`baPrivateAppInstanceUuid`) on every client-log line.
- Evicted window entries ship as `entries_lost` → an explicit
  placeholder line at the gap (same pattern in basn `_ship_logs` /
  `LogsAndEventsMessage.entries_lost`).
- Dev builds tag the build token `-dev` (build 22978+; AppInstanceInfo's
  dev-build flag → AppFastClientData) so local testing is filterable
  from field data.
- Pure logic + tests: `bacommon/logreporting.py` /
  `tests/test_bacommon/`.

## Reading reports

- `tools/pcommand cloud_log_query --message '<text>'` on prod
  (`baSrc=client`), or the dev-log search on dev. Summary line:
  `client log report from b<build> <tag>: N entries at index I`.
- **Attribution trap:** `--message 'client log | b22972'` matches
  loosely — Cloud Logging tokenizes the text (the `|` is not literal),
  so other builds' entries flood in and per-build attribution silently
  lies. Correct recipe: dump via `--filter 'labels.baSrc="client"'`,
  then post-filter strictly on the parsed `b<build>` token. Stack line
  numbers in reports are a reliable build-fingerprint cross-check.

## Driving an investigation

Set a phrase trigger + windows on the fleet, have the target clients
run; pair with raising logger verbosity (transient per-logger levels
are the designed-but-not-built next step — pressure is growing: one
obfuscated mod produces hundreds of pushcall warnings/day across
players).

## Alerting interaction (checked 2026-08-15)

Client entries use `resource.type=global` while the bacentral
Warning|Error|Critical alert conditions filter
`resource.type=cloud_run_revision` — client-log noise does not page.
But `Too much log data` watches `global`
(`log_bucket_monthly_bytes_ingested` > 50GiB/month); client logs ran
~0.3GiB/mo at test-track scale, so that alert is the tripwire that
fires first when 1.8 GA multiplies reporters (relevant to the unbuilt
population-sampling knob).
