# 🏃 Weight Loss Web App

A gamified weight loss tracking application built with Python Flask and HTML/CSS, featuring daily tasks, progress visualization, and avatar customization.

---

## 🚀 Getting Started

### Prerequisites
Install these tools once:
- **Git**: `winget install --id Git.Git -e --source winget`
- **Python 3.13+**: [Download here](https://www.python.org/downloads/)
- **GitHub Account**: [Create one here](https://github.com)

### Initial Setup

1. **Clone the repository**
   ```powershell
   git clone https://github.com/will-doney/WeightLossWebApp.git
   cd WeightLossWebApp
   ```

2. **Create and activate virtual environment**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```powershell
   python app.py
   ```
   Open http://localhost:5000 in your browser

---

## 📤 GitHub Workflow (For Team Collaboration)

### Before Starting Work
```powershell
# Always pull the latest changes first
git checkout main
git pull origin main
```

### Making Changes
```powershell
# Create a feature branch (never work directly on main)
git checkout -b feature/your-feature-name

# Example:
git checkout -b feature/login-validation
```

### Committing Your Work
```powershell
# Check what files changed
git status

# Stage your changes
git add .

# Commit with clear message
git commit -m "Add login form validation"

# Push to GitHub
git push -u origin feature/your-feature-name
```

### Creating a Pull Request
1. Go to GitHub → your branch
2. Click "Compare & Pull Request"
3. Add description of your changes
4. Request team review
5. After approval, merge to main

---

## 💡 Coding Best Practices

### Commits
- ✅ Make small, focused commits (one feature per commit)
- ✅ Write clear commit messages: "Fix password validation" not "stuff"
- ✅ Commit frequently (at least once per task)
- ❌ Don't commit large changes all at once

### Branches
- ✅ Create a new branch for every feature/fix
- ✅ Use descriptive names: `feature/login`, `bugfix/typo`, `docs/readme`
- ✅ Delete old branches after merging
- ❌ Never push directly to main

### Code Quality
- ✅ Add comments for complex logic
- ✅ Keep functions small and focused
- ✅ Use meaningful variable names
- ✅ Test your changes before pushing
- ❌ Don't leave debugging print statements
- ❌ Don't commit sensitive data (API keys, passwords)

### Pull Requests
- ✅ Keep PRs focused on one feature
- ✅ Add description of what changed and why
- ✅ Wait for team review before merging
- ✅ Respond to feedback promptly

---

## 🔧 Common Git Issues

| Problem | Solution |
|---------|----------|
| "error: failed to push some refs" | Run `git pull origin main`, resolve conflicts, then `git push` |
| "nothing to commit" | You haven't made changes yet |
| Merge conflict | Open conflicted file, resolve manually, then `git add .` and `git commit` |
| Wrong branch | `git checkout branch-name` |
| Need to undo commits | `git revert HEAD~1` (creates new commit) or `git reset HEAD~1` (keeps changes) |

---

## 📁 Project Structure

```
WeightLossWebApp/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── firebase-key.json   # Firebase credentials (don't share!)
├── templates/          # HTML templates
├── static/             # CSS and static assets
└── backend/            # Additional backend code
```

---

## 🔐 Security Notes

- **Never commit** firebase-key.json or .env files
- **Never hardcode** passwords or API keys
- Use environment variables for secrets
- Check .gitignore before pushing sensitive files

