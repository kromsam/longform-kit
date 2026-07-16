# Security Policy

## Reporting

Report suspected vulnerabilities through a private GitHub security advisory at
<https://github.com/kromsam/longform-kit/security/advisories/new>. Do not open a
public issue until a fix or mitigation is available.

Include the affected version, operating system, reproduction steps, impact, and
any proposed mitigation. Reports are handled on a best-effort basis while the
project is pre-1.0.

## Trust Model

Quarto extensions, Lua filters, project scripts, and Agent Skills are executable
code. Review changes to these files before rendering an untrusted project. A
checked-in extension is pinned source, not inert document data.

Longform Kit builds do not require network access or credentials. Keep Zotero
tokens, connector credentials, API keys, and private-library exports out of the
repository. Optional AI or Zotero connectors should be read-only unless a user
explicitly authorizes a write.

Bibliography files and manuscript content are untrusted inputs. Do not add shell
evaluation, remote includes, or automatic downloads based on values read from
them. CI workflows should use read-only repository permissions, pin third-party
actions to commit SHAs, and expose no secrets to pull-request builds.

Only the latest 0.x release receives security fixes until a 1.0 support policy
is published.
