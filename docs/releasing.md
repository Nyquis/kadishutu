# Releasing

Releases are built and published by `.github/workflows/release.yml` when a
`v*` tag is pushed. A manual fallback exists for when Actions is unavailable.

## Versioning

| Change | Bump |
| --- | --- |
| Breaking or incompatible behavior (pre-1.0) | minor, `0.3.0` |
| New feature or screen | minor, `0.3.0` |
| Fix or data correction | patch, `0.2.1` |
| Docs, tests, CI, refactor | none |

`version` lives in `pyproject.toml`, `pixi.toml`, and `pixi.lock`. All three must
agree, and the build fails if `pyproject.toml` and `pixi.toml` drift. Bump them
only when cutting a release, as the last commit before the tag.

Development builds keep the current version. The short commit in the archive
name, for example `kadishutu-windows-v0.2.0-58875fc.zip`, distinguishes them.

## Automated release

1. Bump `version` in `pyproject.toml` and `pixi.toml`.
2. Run `pixi install` so `pixi.lock` records the new version.
3. Run `pixi run test`, `pixi run lint`, and `pixi run typecheck`.
4. Commit with `chore: release v0.2.0`.
5. Tag the commit and push only that tag:

   ```shell
   git tag v0.2.0
   git push origin v0.2.0
   ```

6. Watch the `Release` workflow. It will:
   - fail before building if the tag does not match the project version;
   - install UPX 5.2.1 after verifying a pinned SHA-256;
   - build, run the leak gate, and smoke test `kadishutu.exe help`;
   - write `SHA256SUMS.txt` and attest build provenance;
   - publish the release with generated notes.
7. Verify the published release:

   ```shell
   gh release view v0.2.0
   gh attestation verify <downloaded archive> --repo Nyquis/kadishutu
   ```

   Then extract the archive, run the editor, and open a save before announcing
   it.

## Manual fallback

Use this only when the workflow is unavailable. It produces an archive without
build provenance, so say so in the release notes.

```shell
git status --short      # must be empty
pixi run build
Get-FileHash dist/pyinstaller/windows/*.zip -Algorithm SHA256
```

Write the digest to `SHA256SUMS.txt` and publish:

```shell
gh release create v0.2.0 <archive> SHA256SUMS.txt --verify-tag --generate-notes
```

## Recovery

- **Tag pushed by mistake, nothing published yet:** delete the remote and local
  tag, fix the problem, and tag again.

  ```shell
  git push --delete origin v0.2.0
  git tag -d v0.2.0
  ```

- **Release published with a broken build:** delete the release and the tag,
  bump the patch version, and release again. Do not move or reuse a published
  tag; users and attestations both rely on it staying put.
- **Checksum mismatch on download:** re-download. If it persists, the release
  asset is wrong; treat it as the previous case.
