# Remove accidentally committed database files

If `planner.db` or `planner.db-journal` are already on GitHub, `.gitignore` alone will NOT remove them. From the cloned repo, run:

```bash
git rm --cached --ignore-unmatch planner.db planner.db-journal
git add .gitignore
git commit -m "Stop tracking local database files"
git push
```

This keeps local copies and removes the tracked files from the latest commit. If the database ever contained sensitive information, deleting it in a new commit does not erase prior Git history: review history and rotate any exposed credentials if applicable.
