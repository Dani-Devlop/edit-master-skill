# Security Policy

## Supported versions

The skill is a single markdown file plus templates, examples and docs. No
executable code ships in this repository. Security fixes land on the latest
release only.

| Version | Supported |
|---------|-----------|
| 1.0.0 and later | Yes |
| Earlier releases | No |

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report vulnerabilities **via GitHub private vulnerability reporting on this
repository** (Security tab, "Report a vulnerability"), which notifies the
repository owner Dani-Devlop privately. If private vulnerability reporting
is unavailable to your account, contact the repository owner Dani-Devlop
privately through GitHub.

When reporting, include:

- the affected file and the version or commit you are on;
- the agent and setup you used;
- steps to reproduce the problem;
- the impact you observed or expect.

Because this repository ships prompts, templates and documentation, the
reports most likely to matter concern prompt-injection behavior, unsafe
tool commands printed in the docs (ffmpeg and similar), or repository
content being reused in a way that misleads people. Report those the same
way, privately.

## Response timeline

- **Acknowledgment within 72 hours** of a report arriving.
- **Fix or mitigation within 30 days**, or a stated reason and a target
  date if the fix genuinely needs longer.

## Public disclosure policy

Disclosure is coordinated: the fix ships first, then a public note follows.
Credit goes to the reporter by default; say so at report time if you prefer
anonymity. Exploit details are not published before the fix is available.

## Thanks

Thank you for responsible disclosure. A private report beats a public
surprise, and every report gets read.
