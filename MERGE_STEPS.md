# Commit your changes, then merge origin/frontend-upgrade

## Step 1: Commit your current work

```powershell
cd c:\Users\volem\Documents\CS\projects\ifyousayyes

# Stage everything (including new comment/moderation code)
git add -A
git status   # confirm what will be committed

git commit -m "feat: dashboard search/sort, community comments, dedupe and risk-prefer logic"
```

## Step 2: Merge origin/frontend-upgrade

```powershell
git merge origin/frontend-upgrade
```

## Step 3: If you see conflicts

**Files that may conflict** (both your branch and frontend-upgrade change them):

| File | Your side | frontend-upgrade side |
|------|-----------|------------------------|
| `frontend/app/page.tsx` | Inline SVG icons, current layout | Different grid + "Dangerous" risk pill, possibly lucide icons |
| `frontend/components/drug-interaction-form.tsx` | Your form + health check, DEFAULT_SUBSTANCES | New UI with lucide-react (ShieldAlert, etc.), swap button, different styling |
| `frontend/app/dashboard/DashboardClient.tsx` | Search bar, sort, dedupe by name | May have different dashboard code |
| `frontend/app/dashboard/[id]/SubstanceProfilePage.tsx` | Dosage display, CommentSection, RiskWarning | May have different detail page |
| `frontend/components/RiskWarning.tsx` | Your modal + checkbox | May differ |
| `frontend/lib/substance-types.ts` | Your types | May differ |

- Open each conflicted file, look for `<<<<<<<`, `=======`, `>>>>>>>`.
- Keep your logic (search, sort, comments, dedupe, risk warning) and merge in any UI/design you want from frontend-upgrade (e.g. "Dangerous" pill, swap button, lucide icons **only if** you add/upgrade lucide-react so ShieldAlert exists).
- After editing: `git add <file>` for each resolved file.

Then finish the merge:

```powershell
git add -A
git commit -m "Merge origin/frontend-upgrade; keep search/sort/comments/dedupe, take chosen UI from upgrade"
```

## Step 4: Push

```powershell
git push origin main
```

If the merge had no conflicts, `git merge origin/frontend-upgrade` will complete without opening an editor and you can push right after.
