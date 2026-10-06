# Client hosting

The launcher uses a per-file manifest. The launcher repository contains the
manifest builder, but the game client itself should be stored on HTTPS storage
or on the Maveni web server, not committed to normal Git history.

Configure the GitHub Actions secret `CLIENT_BASE_URL` to the public directory
that contains the client files. Its directory layout must match the manifest,
for example:

```text
https://downloads.example.invalid/maveni/client/pack/PC.eix
https://downloads.example.invalid/maveni/client/pack/PC.epk
```

Then place the client files in a CI workspace directory named `client/` before
running the release workflow. The workflow calculates every SHA-256 hash and
publishes `manifest.json` with the launcher release.
