# GitHub upload guide

Upload the contents of **paper-supp/** as the repository root. Preserve the subdirectories and both dotfiles.

## Large files

Three archived files are configured in `.gitattributes` for Git Large File Storage (LFS):

| File | Bytes |
|---|---:|
| `data/processed/coding/nsf_coding_evidence.csv` | 111,729,068 |
| `data/processed/coding/nsfc_coding_evidence.csv` | 93,732,914 |
| `figures/supplementary/figures8b/figure5d_discrete_mirrored_ridgelines_reconstructed.tiff` | 70,859,006 |

GitHub blocks ordinary Git files larger than 100 MiB and warns about files larger than 50 MiB. The package therefore tracks all three files above 50 MiB through LFS. See the official [large-file documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) and [Git LFS documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).

Use Git with Git LFS installed rather than dragging this complete package into the browser upload form. `.gitattributes` declares the rules; the packaging process did not install LFS or convert the local payloads into pointer files.

## Publish with Git

After creating the desired repository in your own GitHub account, open a terminal in `paper-supp/` and run:

```bash
git lfs install
git init
git add .
git lfs ls-files
git status
git commit -m "Add supplementary data and figure source archive"
git branch -M main
```

Confirm that `git lfs ls-files` lists the three files above. Then add your actual repository URL as `origin` and push `main`. The repository URL is intentionally not invented here. Account-specific LFS storage and bandwidth availability must be checked for the account used to publish.

The `.gitattributes` file also disables line-ending normalization to preserve the original checksums of archived text files. Keep that setting when creating the first commit.

## Verify after downloading

```bash
git lfs pull
python code/01_verify_package.py
```

An LFS pointer is not the full CSV/TIFF payload. If checksum verification fails for a large file, confirm that its actual contents were downloaded through LFS.

## Release metadata

Add the final author names, article citation, repository URL, and applicable author-approved licenses before a public release. Figure S1 is not included in the supplied source folder; add the actual source files if it is meant to be part of the public supplement. Existing raw data, code dependencies, and rights must be described as they actually exist; do not describe this archive as a fully validated one-command reproduction package.

No upload or remote repository creation was performed while preparing this local package.
