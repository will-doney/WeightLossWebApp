#🚀 1. Get the project on your computer
#🔹 Step 1: Install these tools

Everyone needs to install these once:

Git
winget install --id Git.Git -e --source winget

Node.js (LTS version)
winget install OpenJS.NodeJS.LTS

A GitHub account

#🔹 Step 2: Clone (download) the repository

Open your terminal (PowerShell on Windows) and type:

git clone https://github.com/will-doney/WeightLossWebApp.git


This downloads the project to your computer.

Then go into the folder:

cd WeightLossWebApp

#🔹 Step 3: Install project files

The node_modules folder is not stored on GitHub.
Run this to install everything the project needs:

npm install

#🔹 Step 4: Run the app locally
npm run dev


You’ll see a local link like:

http://localhost:5173/


Click it to open the project in your browser. 🎉

# 💻 2. Basic Git Commands (with explanations)

# These are the main commands you and the team will use every day.

Action	Command	What it does
Check what’s changed	git status	Shows what files have been modified
Add files to commit	git add .	Tells Git to include all your changes
Save (commit) changes locally	git commit -m "Describe what you did"	Records your changes in Git
Get latest code from GitHub	git pull	Updates your folder with new team changes
Send your commits to GitHub	git push	Uploads your work to the repo
🌿 3. How to make changes safely (branches)

When working on new features or fixes, don’t edit directly on main.
Instead, create a branch — a separate workspace for your changes.

#Create a new branch:
git checkout -b feature/new-feature-name


Example:

git checkout -b feature/login-page

#After editing your code:
git add .
git commit -m "Add login page"
git push -u origin feature/login-page


Then go to GitHub — you’ll see a button to “Compare & Pull Request”.
Click it → describe your change → click Create pull request.

This lets your teammates review before merging into main.

# 🔁 4. Keeping your code up to date

# Before you start working each day, always pull the latest code:

git checkout main
git pull


Then create your branch from that updated main branch.

# 🧠 5. Common Git Issues (and fixes)
Problem	What to do
error: failed to push some refs	Run: git pull origin main --allow-unrelated-histories, then git push
nothing to commit, working tree clean	You haven’t changed anything yet — no problem
Merge conflict	Git will show the file with conflicts — open it, fix it manually, then run:
git add .
git commit
git push
# 🧩 6. Project Setup Summary
# Download the project
git clone https://github.com/will-doney/WeightLossWebApp.git

# Move into the project folder
cd WeightLossWebApp

# Install dependencies
npm install

# Run locally
npm run dev

# Make changes and commit
git add .
git commit -m "Your message"
git push

#🧑‍💻 7. Team Workflow Summary

# Pull the latest changes

git pull


# Create a new branch

git checkout -b feature/your-feature


# Work, then commit your changes

git add .
git commit -m "Describe changes"


# Push your branch to GitHub

git push -u origin feature/your-feature


Open a Pull Request on GitHub for review

#💡 8. Extra Tips

Commit often — small commits are easier to review.

Write clear messages like "Fix login form validation".

Always pull before pushing to avoid merge conflicts.

#If something breaks, you can always check previous commits with:

git log
