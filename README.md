1. Setup (First Time Only)
✅ 1.1 Install the tools

Make sure everyone has:

Git

Node.js (LTS version)

A GitHub account → https://github.com

✅ 1.2 Clone the repository

Once you’ve been added as a collaborator (the owner will invite you):

git clone https://github.com/will-doney/WeightLossWebApp.git
cd WeightLossWebApp


This downloads the project to your computer.

✅ 1.3 Install dependencies

Since node_modules aren’t stored on GitHub:

npm install


This will install all the project’s libraries.

🧩 2. Running the Project Locally

To start the development server:

npm run dev


Then open the link shown in your terminal (usually http://localhost:5173/).

This runs the app locally so you can build and test features.

🔄 3. Basic Git Commands (for everyday use)
Action	Command	Description
See what’s changed	git status	Shows modified files
Stage changes	git add .	Prepares all files to commit
Commit changes	git commit -m "Your message"	Saves your changes locally
Pull latest updates	git pull	Updates your copy with team changes
Push your work	git push	Uploads commits to GitHub
🌿 4. Working on Features (Branching Workflow)

To avoid overwriting each other’s work, we’ll use branches.

🪴 Create a new branch
git checkout -b feature/your-feature-name


Example:

git checkout -b feature/login-page

🛠️ Make your changes, then:
git add .
git commit -m "Add login page UI"
git push -u origin feature/login-page

🔁 Create a Pull Request (PR)

Go to the repo on GitHub.

You’ll see a message like “Compare & pull request”.

Click it → describe your change → click Create pull request.

Another team member reviews and merges it into main.

🧹 5. Keeping Your Local Copy Updated

Before starting new work:

git checkout main
git pull


This ensures you’re always working from the latest version.

🧠 6. Common Problems
🟥 “error: failed to push some refs to origin main”

Your local copy is behind GitHub.
Run:

git pull origin main --allow-unrelated-histories
git push

🟨 “nothing to commit, working tree clean”

Means you haven’t changed any tracked files — you’re good.

🚀 7. Deployment

This project can be deployed in two ways:

Option 1: GitHub Pages

We use the gh-pages
 package.
To deploy manually:

npm run build
npm run deploy


Your live site will be at:
👉 https://will-doney.github.io/WeightLossWebApp/

Option 2: Netlify

Go to https://netlify.com

Log in → “Add New Site” → “Import existing project”

Select this repo

Build command: npm run build

Publish directory: dist

Click Deploy

🧩 8. Project Structure Overview
WeightLossWebApp/
│
├── src/                # React components & logic
├── public/             # Static assets
├── dist/               # Build output (ignored in Git)
├── package.json        # Dependencies & scripts
├── vite.config.js      # Vite configuration
└── .gitignore          # Files ignored by Git

🧑‍💻 9. Team Workflow Summary

Pull the latest changes

Create a branch for your work

Make changes

Commit and push

Open a Pull Request

Get it reviewed and merged into main

❤️ 10. Quick Tips

Commit often with clear messages.

Never work directly on the main branch.

Always run git pull before starting new work.

Communicate in PRs and use GitHub issues to track tasks.
