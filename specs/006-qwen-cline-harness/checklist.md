# Harness Requirements Checklist

- [x] Exact canonical target and parent/executor roles are named.
- [x] Instructions are not treated as the sole security control.
- [x] Read, write, command, tool, symlink, and post-run mutation boundaries are
  independently specified.
- [x] File-content, exact-write, and loopback-only network containment is
  self-tested before provider execution.
- [x] Deterministic outputs can be pinned by exact SHA-256 so model assertions
  are not accepted as verification.
- [x] Canonical integration remains parent-owned.
- [x] Private data, credentials, network effects, commits, pushes, and
  publication stay unauthorized.
- [x] A live success smoke and direct hostile hook smoke are both required.
- [x] Model/provider limits are not described as unlimited.
- [x] External Kaggle/reviewer/launch evidence is unaffected.
