# Build and Release Process

## Development Installation

Install project dependencies into the virtual environment:
```bash
pipenv install --dev
```

Subarulink will be installed as an editable package within the virtual environment:

Make changes to code.

Run subarulink:
```bash
pipenv run subarulink
```

## Releasing (automated, recommended)

Releases are published automatically by the
[`Release`](.github/workflows/release.yml) GitHub Actions workflow, which builds
the distributions and uploads them to **PyPI** using PyPI
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC). This also
produces [PEP 740](https://peps.python.org/pep-0740/) digital attestations
(Sigstore-signed provenance), shown as verified publisher attestations on the
project's PyPI page. No API tokens are stored in the repo.

To cut a release:

1. Bump `__version__` in `subarulink/__version__.py` and merge to `master`.
2. Create a git tag and a **GitHub Release** for it (Releases → Draft a new
   release → choose/create tag `v<version>` → Publish release).
3. Publishing the release triggers the workflow, which builds and publishes to
   PyPI, attaching PEP 740 attestations to the upload.

### One-time setup (done in the browser)

Trusted Publishing must be registered once on PyPI before the workflow can
publish. On **PyPI**, go to the project's *Publishing* settings (or
*Your projects → Publishing* for a new project) and add a GitHub Actions trusted
publisher with:

| Field             | Value         |
| ----------------- | ------------- |
| Owner             | `G-Two`       |
| Repository        | `subarulink`  |
| Workflow filename | `release.yml` |
| Environment name  | `pypi`        |

Optionally, protect the `pypi` environment in the repo's GitHub settings
(Settings → Environments) with required reviewers.

## Building the Package (local sanity check)

To build the distributions locally without publishing (e.g. to inspect the
sdist/wheel contents):
```bash
pipenv run python -m build
```

This creates files in `dist/`:
- `subarulink-<version>.tar.gz` (source distribution)
- `subarulink-<version>-py3-none-any.whl` (wheel)

Publishing is handled exclusively by the automated release workflow above, which
uploads to PyPI with PEP 740 attestations via Trusted Publishing. Local uploads
with `twine` are no longer supported (and would not produce attestations); if you
ever need an emergency manual upload, install it ad hoc with
`pipenv run pip install twine`.
