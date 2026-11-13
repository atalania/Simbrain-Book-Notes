# Optional: instant sync when the book changes

By default the notes repo checks the book every 15 minutes. That is as close to "real time" as you can get from your side alone, because GitHub only tells a repository about pushes to that same repository.

If the book's maintainers are happy to help, they can make the book repo ping this repo on every push. The sync then starts within seconds.

## 1. Create a token (you)

1. Go to GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. **Repository access:** *Only select repositories* → `atalania/simbrain-book-notes`.
3. **Permissions → Repository permissions → Contents:** *Read and write* (this is what GitHub requires for `repository_dispatch`).
4. Give it an expiry date and copy the token.

The token can only touch this one notes repository.

## 2. Store it in the book repo (a maintainer)

In `simbrain/NeuralNetworksCogSciBook` → **Settings → Secrets and variables → Actions → New repository secret**, name it `NOTES_REPO_TOKEN` and paste the token.

## 3. Add this workflow to the book repo (a maintainer)

Save as `.github/workflows/notify-notes.yml` in the book repository:

```yaml
name: Notify notes repository
on:
  push:
    branches: [main]
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Ask the notes repo to re-sync its line numbers
        run: |
          curl -sS -X POST \
            -H "Accept: application/vnd.github+json" \
            -H "Authorization: Bearer ${{ secrets.NOTES_REPO_TOKEN }}" \
            https://api.github.com/repos/atalania/simbrain-book-notes/dispatches \
            -d '{"event_type":"book-updated"}'
```

The notes repo's workflow already listens for the `book-updated` event, so nothing else needs to change on your side. The 15-minute schedule can stay as a backup.
