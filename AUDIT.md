# AUDIT.md

Project: bel-sekolah-dan-tarhim-otomatis — Installer-bel-v15.sh audit
Repository: saroppudin/bel-sekolah-dan-tarhim-otomatis

Date: 2026-08-03
Auditor: automated assistant (initial pass)

SUMMARY
-------
This document records the results of a focused audit of the installer and runtime shell scripts present in the repository (primary file inspected: Installer-bel-v15.sh and its generated scripts). The purpose is to capture current features, potential issues (bugs, security, maintainability), and an actionable prioritized remediation plan to start Milestone 1 of the migration to Audio School System v2.

HIGHLIGHTS / FEATURES (observed)
--------------------------------
- Rich, well-documented installer with many pragmatic field fixes (Bluetooth pairing/trust, bluealsa a2dp-source, AutoEnable, polkit/dbus rules).
- Dynamic ALSA routing via atur_output_audio.sh (writes /etc/asound.conf) supporting Bluetooth and line-out modes.
- Systemd units (tahrim-daemon.service, bt-boot-connect.service, integritas-sistem.timer/service) for scheduler, reconnect, and integrity checks.
- Recovery automation (cek_integritas_sistem.sh) to auto-download installer from GitHub and restore missing files if /home wipe occurs.
- Robust logging strategy to /var/log/otomasi_audio.log and logrotate configuration.
- Use of file locks (flock) to avoid concurrent bluetoothctl operations and to serialize playback switching.
- Scheduler implementation via cron scripts (cek_harian.sh, cek_ujian.sh) with backward-compatible config files (jadwal_harian.conf, jadwal_ujian.conf).

DETECTED ISSUES (PRIORITIZED)
-----------------------------
Critical / High
- sudoers NOPASSWD entry for a script under ${DIR_BASE} (/home/${USER_SISTEM}/atur_output_audio.sh) can allow a local non-root user who can edit files in that path to escalate to root. (Security risk)
- cek_integritas_sistem.sh auto-downloads and executes an installer script from GitHub without verifying a cryptographic signature or checksum. This creates a supply-chain risk if GitHub account is compromised or MITM occurs.
- Some places lack strict quoting of variable expansions in file and command arguments (e.g. cp/mv/find usage). This may cause word splitting or globbing failures for paths with spaces.

Medium
- Installer tries to install packages in a single apt call earlier; this was fixed for polkit but other package installs still may fail if one package name is incorrect. Consider isolating critical packages and handling failures more gracefully.
- Using 'tar -xzf' directly on downloaded tarball without verifying or extracting only expected files may be unsafe.
- The backup copy logic copies `${DIR_BASE}/*.sh ${DIR_BASE}/*.conf` — will miss nested or other config files; consider a more deterministic backup list and exclusion rules.

Low / Maintainability
- Mixed languages in comments (Indonesian) — fine for current maintainers, but future contributors may prefer English.
- Several duplicated patterns across scripts (logging, probing, validation) that will be cleaned in migration. This increases maintenance overhead currently.

Potential Race/Robustness
- Some temporary files use predictable names in /tmp without explicit umask or secure mktemp usage (though mktemp used in some places). Ensure all temporary files use mktemp and are cleaned.
- Some uses of `crontab -l | grep -v` to filter installed crons could remove unrelated lines if patterns are too broad; be careful with exact anchoring.

SECURITY RECOMMENDATIONS
------------------------
- Move any NOPASSWD scripts out of writable user-controlled directories into root-owned immutable paths (e.g. /usr/local/bin) and reference the absolute path in sudoers.
- Add cryptographic signature or checksum verification for any auto-downloaded installer or tarball; if not possible, at least verify GitHub release tag and HTTPS certificate pinning where feasible.
- Harden file uploads and copied files: explicit ownership, restrictive permissions, and validation for file types.
- Reduce NOPASSWD scope to the minimum required commands; avoid wildcards where possible.

REFactoring SUGGESTIONS (Milestone 1 immediate)
-----------------------------------------------
1. Create a compatibility/ directory and split large installer-generated scripts into small wrappers that expose a stable function API (e.g. compat/bluetooth.sh, compat/audio.sh, compat/asound.sh, compat/system.sh, compat/backup.sh). These wrappers will be used by the Python backend later.
2. Normalize logging usage to a single helper (catat in scripts) and prefer a structured log format (JSON lines) for easier ingestion.
3. Introduce strict quoting and safer temp file usage across scripts. Replace any `> /tmp/name` with `mktemp` and `trap` cleanup.
4. Replace direct execution of downloaded scripts with verified installers (signature or checksum) or require manual acceptance.

MIGRATION / NEXT ACTIONS (PRIORITIZED)
--------------------------------------
1. Create compatibility module skeletons in repository (app/compat/) to prepare for the Python Compatibility Layer. (This commit)
2. Produce AUDIT.md (this file) and open issues for critical security items (sudoers NOPASSWD, unchecked installer download verification).
3. Implement small fixes in installer scripts that are non-behavioral but harden security (move NOPASSWD paths, add checksum check placeholder) — but do not change user-visible behavior until migration tests exist.
4. Implement automated shell linting (shellcheck) in CI and fix high-severity shellcheck findings.
5. Add unit tests for compatibility wrappers (to be executed in CI) that mock system commands.

MILESTONE-1 TASK LIST (short)
----------------------------
- [x] Create AUDIT.md (this file)
- [x] Create compatibility module skeletons (stubs) in app/compat/
- [ ] Run shellcheck and fix critical warnings
- [ ] Hardening: move NOPASSWD scripts to /usr/local/bin and update sudoers (or reduce scope)
- [ ] Add checksum/signature verification for auto-download installer (placeholder until signing infra available)
- [ ] Add CI job for shell lint + static checks

FILES CREATED IN THIS COMMIT
----------------------------
- AUDIT.md
- app/compat/bluetooth.sh (skeleton)
- app/compat/audio.sh (skeleton)
- app/compat/asound.sh (skeleton)
- app/compat/system.sh (skeleton)
- app/compat/backup.sh (skeleton)
- MILESTONE1_TASKS.md

NOTES
-----
This audit is an initial pass focused on safety and migration readiness. A follow-up deeper audit is recommended to review additional repository files and test-run the installer in a controlled VM to capture dynamic runtime issues.

End of audit.
