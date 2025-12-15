# 🏃 WeightGame - Gamified Fitness Tracker

A gamified weight loss tracking web application built with Flask and Firebase, featuring daily tasks, progress visualization, and avatar customization.

Challenge 9: Global Health
Route C: Implementation 

---

## ✨ Features

- **Firebase Authentication**: Secure user login and signup with Google Sign-In support
- **Real-time Database**: Firestore integration for persistent data storage
- **Daily Tasks**: Personalized task suggestions based on fitness level and goals
- **Progress Tracking**: Weight entries, workout logs, and goal management
- **Avatar System**: Earn points by completing tasks to customize your avatar
- **Interactive Dashboard**: Visualize your progress with charts and statistics
- **Profile Management**: Track BMI, set goals, and manage personal fitness data

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**: [Download here](https://www.python.org/downloads/)
- **Firebase Project**: Create a project at [Firebase Console](https://console.firebase.google.com/)
- **Git**: `winget install --id Git.Git -e --source winget`

### Installation

1. **Clone the repository**
   ```powershell
   git clone https://github.com/will-doney/WeightLossWebApp.git
   cd WeightLossWebApp
   ```

2. **Set up virtual environment**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure Firebase**
   - Download your Firebase service account key as `firebase-key.json`
   - Place it in the project root directory
   - Update Firebase config in `templates/login.html` and `templates/signup.html`

5. **Run the application**
   ```powershell
   python app.py
   ```
   
   Open http://localhost:5000 in your browser

---

## 📁 Project Structure

```
WeightLossWebApp/
├── app.py                  # Main Flask application entry point
├── requirements.txt        # Python dependencies
├── firebase-key.json       # Firebase credentials (do not commit!)
├── routes/
│   ├── __init__.py        # Routes package initialization
│   ├── main.py            # Home page and error handlers
│   ├── auth.py            # Authentication routes (login, signup, logout)
│   ├── dashboard.py       # Dashboard, profile, weight/workout logging
│   ├── tasks.py           # Task CRUD operations and API
│   ├── other.py           # Settings and avatar customization
│   └── task_library.py    # Task suggestion algorithm
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Base template with navigation
│   ├── home.html          # Landing page
│   ├── login.html         # Login with Firebase Auth
│   ├── signup.html        # Registration with Firebase Auth
│   ├── dashboard.html     # Main dashboard with stats
│   ├── tasks.html         # Task management interface
│   ├── myavatar.html      # Avatar customization
│   ├── settings.html      # User settings
│   └── update_profile.html # Profile update form
└── static/
    ├── css/
    │   └── styles.css     # Application styles
    └── avatars/           # Avatar images
```

---

## 🔧 Technology Stack

- **Backend**: Python 3.13, Flask 3.1
- **Database**: Google Cloud Firestore (NoSQL)
- **Authentication**: Firebase Authentication
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)

---

### Git Best Practices

```powershell
# Always pull latest changes before starting work
git pull origin main

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes, then commit
git add .
git commit -m "Clear description of changes"

# Push to GitHub
git push -u origin feature/your-feature-name
```

### Admin Account Details

User name: admin@admin.admin
Password: adminadmin


## 📊 Database Collections

The app uses these Firestore collections:

- **users**: User profiles (email, avatar, creation date)
- **tasks**: User tasks (name, description, completed status)
- **weight_entries**: Weight log entries with dates
- **workouts**: Workout logs (type, duration, calories)
- **goals**: Weight loss goals (target, deadline, weekly goal)
- **profile_entries**: Profile history (weight, height, BMI, age)
- **avatars**: Avatar points and customization data

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
