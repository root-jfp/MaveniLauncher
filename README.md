# Maveni Launcher prototype

This Windows launcher reads `launcher.json`, downloads a CI/CD-hosted JSON
manifest, verifies every changed file with SHA-256, and starts the configured
game executable.

The manifest can be hosted as a GitHub Release asset, GitHub Pages file, or any
HTTPS endpoint. The next step is adding the GitHub Actions workflow that builds
the client, calculates the manifest hashes, and publishes the files.

Run from Python 3.11+ with:

```powershell
python launcher.py
```

The launcher has no third-party Python dependencies. It is ready to package as
a single Windows executable with PyInstaller after the manifest URL and game
distribution location are chosen.
