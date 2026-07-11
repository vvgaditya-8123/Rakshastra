# Langfuse Observability Plugin

This plugin ships bundled with Rakshastra but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

Pick one:

```bash
# Interactive: walks you through credentials + SDK install + enable
rakshastra tools  # → Langfuse Observability

# Manual
pip install langfuse
rakshastra plugins enable observability/langfuse
```

## Required credentials

Set these in `~/.rakshastra/.env` (or via `rakshastra tools`):

```bash
RAKSHASTRA_LANGFUSE_PUBLIC_KEY=pk-lf-...
RAKSHASTRA_LANGFUSE_SECRET_KEY=sk-lf-...
RAKSHASTRA_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
rakshastra plugins list                 # observability/langfuse should show "enabled"
rakshastra chat -q "hello"              # then check Langfuse for a "Rakshastra turn" trace
```

## Optional tuning

```bash
RAKSHASTRA_LANGFUSE_ENV=production       # environment tag
RAKSHASTRA_LANGFUSE_RELEASE=v1.0.0       # release tag
RAKSHASTRA_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
RAKSHASTRA_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
RAKSHASTRA_LANGFUSE_DEBUG=true           # verbose plugin logging
```

## Disable

```bash
rakshastra plugins disable observability/langfuse
```
