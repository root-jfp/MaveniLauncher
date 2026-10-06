# Maveni Launcher prototype

This Windows launcher reads `launcher.json`, downloads a CI/CD-hosted JSON
manifest, verifies every changed file with SHA-256, and starts the configured
game executable.

The manifest is downloaded from the latest GitHub Release. The release workflow
builds the Windows executable and manifest. Set the `CLIENT_BASE_URL` GitHub
Actions secret and provide the client files in a `client/` workspace directory
before releasing; see `CLIENT_HOSTING.md`.

Run from Python 3.11+ with:

```powershell
python launcher.py
```

The launcher has no third-party Python dependencies. It is ready to package as
a single Windows executable with PyInstaller after the manifest URL and game
distribution location are chosen.
