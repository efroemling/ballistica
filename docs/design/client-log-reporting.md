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

## Cloud logger control (per-logger levels)

- `CloudValsPersistent.logger_control` carries a
  `bacommon.loggercontrol.LoggerControlConfig` — a diff over the
  client's base logger config, same shape as the user's own
  `'Log Levels'` app-config value. Persistent (not transient) so it
  applies from the very start of the next run: `baenv._set_log_levels`
  reads the stored `CloudVals` blob pre-engine; fresh vals arriving
  mid-run also re-apply immediately.
- Set per fleet via "Client Logger Control (JSON)" on `/fleetsettings`
  (wire form, e.g. `{"l": {"ba.connectivity": 10}}`); sourced from
  bamaster `FleetGlobals.client_logger_control`.
- The user chooses via the `'Cloud Logger Control'` app-config bool
  (default True; toggle in the dev-console Logging tab). ON: cloud
  config (or base defaults) drives levels and the manual per-logger UI
  is replaced by an explainer. OFF: their own `'Log Levels'` diff, as
  before. `BA_LOG_LEVELS` env var still overrides everything.
- Client-side logic: `babase._cloudloggercontrol` (+ the baenv
  launch path). `cloud_controlled_logging()` is True only when the
  toggle has been ON continuously since launch with no env override —
  toggling OFF even momentarily latches it False for the run.
- That bool rides on every `ClientLogReportMessage` (`cc`) and lands
  as `levels=cloud|user` in the report summary line plus a
  `baCloudControlledLogging` label on every emitted line, so report
  queries can filter for clients showing exactly the levels the
  server configured.

## Integrity signals (blessed / modified)

Successors to the v1 system where clients sent their master-hash
(camouflaged as `newsShow`) + `userRanCommands`/`userModded` and the
legacy server derived `blessed` from a per-build Blessing record.
Now split into two orthogonal client-computed values on every
`ClientLogReportMessage`, sampled at each slice send:

- `blessed` (`bl`, tri-state): pure build integrity — non-debug build
  with an embedded blessing hash whose computed script hash checks
  out (`_baplus.get_blessing_state()`). `None` = the background hash
  calc (game_hash.py, kicked at pyembed init) hadn't finished, or a
  pre-field client. Debug builds are always unblessed.
- `modified` (`md`): user-side taint — commands run, workspaces in
  use, or custom app-scripts dir (`_babase.is_user_modified()`; same
  trio the fatal-error reporter sends). Inherently latching within a
  run, so False = clean-so-far. Note automation-channel execs latch
  it (by design — they run arbitrary code).

Server side: `build=blessed|unblessed|unknown, modded=yes|no|unknown`
in summary lines; `baBlessed`/`baModified` labels on every emitted
line (omitted when unknown). Gold-standard field-data filter:
`baBlessed=1, baModified=0, baCloudControlledLogging=1`.

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

- `tools/pcommand cloud_log_query --src client` on prod, or the
  dev-log search on dev. Summary line:
  `client log report from b<build> <tag>: N entries at index I`.
- Query mechanics — including the `--message` tokenization trap that
  silently breaks per-build attribution and the strict post-filter
  recipe for it — live in the `cloud-logs` Claude skill.

## Driving an investigation

Set a phrase trigger + windows on the fleet, have the target clients
run; pair with raising logger verbosity via the fleet's cloud logger
control config (above) — and filter the resulting reports on
`levels=cloud` so user-tweaked clients don't muddy the picture.

## Alerting interaction (checked 2026-08-15)

Client entries use `resource.type=global` while the bacentral
Warning|Error|Critical alert conditions filter
`resource.type=cloud_run_revision` — client-log noise does not page.
But `Too much log data` watches `global`
(`log_bucket_monthly_bytes_ingested` > 50GiB/month); client logs ran
~0.3GiB/mo at test-track scale, so that alert is the tripwire that
fires first when 1.8 GA multiplies reporters (relevant to the unbuilt
population-sampling knob).
