# Data handling and public releases

PraisonAI Clips runs jobs and stores outputs locally. Transcription sends source audio to OpenAI, and visual analysis sends sampled frames. API responses, transcripts, screenshots, editor project state, and diagnostic logs can contain private source content and filesystem paths.

## Files to keep private

The repository ignores `.env` credentials, `input/`, `data/`, `output/`, installed editor runtimes, local MCP state, and common media, database, and private-key formats. These rules prevent ordinary additions; they do not remove files already tracked by Git or protect files added with `git add -f`.

Keep `.env.example` limited to empty credentials and safe defaults. Use generic example paths and disposable project names in documentation and integration tests. Preserve public contributor attribution, upstream source references, and third-party license notices.

When sharing diagnostics, inspect transcripts, captions, source names, absolute paths, project identifiers, media hashes, and exported frames. Remove credentials and unrelated source content. Avoid sharing whole workspace archives: ignored files are still included by ordinary archive tools.

The dashboard and preview gallery are intended for private localhost use. The gallery exposes the local job data directory. Do not expose it publicly as a documentation server.

## Before publishing a repository

1. Inspect the files Git will publish, including binary assets and dependency configuration:

   ```sh
   git status --short
   git ls-files
   git diff --cached --stat
   git diff --cached
   ```

2. Confirm that local credentials and generated artifacts are ignored:

   ```sh
   git check-ignore .env data/private-report.json input/private-video.mp4 output/private-video.mp4
   ```

3. Run a secret scanner on the current tree and all reachable history, with redacted output. Also review home-directory paths, personal contact details, private URLs, source-specific notes, and Git author/committer metadata. Pattern matching alone cannot establish that a repository contains no sensitive information.

4. Review branches and tags intended for publication. Removing a value from the latest file does not remove it from earlier commits. History cleanup changes commit identifiers and requires coordination before replacing an existing remote branch. Copies, forks, and remote caches can retain old data. Revoke or rotate any exposed credential independently of history cleanup.

5. Use an appropriate public Git author email for future commits. A repository-local setting can use the exact no-reply address supplied by your Git hosting provider without changing other repositories.

6. Build the documentation and inspect release archives separately. Confirm that packaging did not include ignored workspace data.

   ```sh
   pytest -q
   mkdocs build --strict
   ```

Keep any detailed audit report containing sensitive values outside tracked files. Re-run these checks when adding examples, screenshots, logs, or editor integrations.
