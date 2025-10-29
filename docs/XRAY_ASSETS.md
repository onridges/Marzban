# Xray binary and assets (developer guide)

This project integrates with the Xray binary and expects two environment variables:

- `XRAY_EXECUTABLE_PATH` — path to the Xray executable at runtime.
- `XRAY_ASSETS_PATH` — path to the directory containing Xray JSON templates and other assets.

Important notes:

- Do NOT commit Xray binaries or other proprietary assets to this repository.
- For local development you can point `XRAY_EXECUTABLE_PATH` to `/bin/true` to
  avoid executing the real binary; this is useful when running database migrations
  or other tasks that import modules which would otherwise call Xray at import-time.

Recommended ways to provide the Xray binary and assets in Docker / Compose:

1) Mount on the service at runtime (recommended):

```yaml
services:
  marzban:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./xray/bin:/opt/xray/bin:ro
      - ./xray/assets:/opt/xray/assets:ro
    environment:
      XRAY_EXECUTABLE_PATH: /opt/xray/bin/xray
      XRAY_ASSETS_PATH: /opt/xray/assets
```

2) Copy at image-build time (only if you have a licensed or allowed binary):

COPY is possible but be careful not to check the binary into source control.

Troubleshooting:

- If the app errors during import referencing the Xray binary, set `XRAY_EXECUTABLE_PATH=/bin/true`
  temporarily to bypass execution until you provide a real binary.
