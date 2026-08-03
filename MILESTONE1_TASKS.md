# Milestone 1 tasks

This file lists the immediate tasks to complete Milestone 1 (Repository Audit, bug fix planning, compatibility skeletons).

- [ ] Run shellcheck across all shell scripts and fix critical issues.
- [ ] Move NOPASSWD scripts to /usr/local/bin or reduce sudoers scope.
- [ ] Add checksum/signature verification to cek_integritas_sistem.sh download step.
- [ ] Add CI job for shell linting and static checks.
- [ ] Replace unsafe temp file usage with mktemp and add trap cleanup.
- [ ] Convert atur_output_audio.sh autop-runner to call app/compat/asound.sh (plan migration).

