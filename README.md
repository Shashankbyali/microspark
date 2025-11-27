# ⚡ MicroSpark

Transform 5-20 minutes into lifelong mastery! MicroSpark is a web application that helps you track your daily practice sessions and build consistent habits.

## Features

- 🔐 **User Authentication**: Sign up and sign in to track your personal progress
- 🎯 **Skill Tracking**: Choose any skill you want to practice and select timer duration (5, 10, 15, or 20 minutes)
- ⏱️ **Practice Timer**: Beautiful circular timer to track your practice sessions
- 📸 **Proof Upload**: Upload proof of your practice (images, videos, or PDFs)
- 🔥 **Daily Streak**: Track your consecutive days of practice with motivational messages
- 📊 **Progress Dashboard**: View your statistics, skill breakdown, and session history

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Database**: SQLite

## Installation

1. Clone or download this repository

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Sign Up/Sign In**: Create an account or sign in to your existing account
2. **Choose a Skill**: Enter the skill you want to practice and select your preferred duration (5, 10, 15, or 20 minutes)
3. **Practice**: Start the timer and focus on your practice
4. **Upload Proof**: After completing your session, upload proof of your practice
5. **Track Progress**: View your daily streak, statistics, and session history on the progress page

## Project Structure

```
MicroSpark/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── index.html        # Landing page (sign in/sign up)
│   ├── choose_skill.html # Skill selection and timer page
│   └── progress.html     # Progress dashboard
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       ├── auth.js       # Authentication logic
│       ├── skill.js      # Skill tracking and timer logic
│       └── progress.js   # Progress display logic
└── uploads/              # Directory for uploaded proof files
```

## Database Schema

- **users**: Stores user account information
- **skills**: Tracks skills that users want to practice
- **sessions**: Records completed practice sessions with proof

## Notes

- The application uses SQLite for simplicity. For production, consider using PostgreSQL or MySQL
- File uploads are limited to 16MB
- Allowed file types: images (png, jpg, jpeg, gif), videos (mp4, mov, avi), and PDFs
- The secret key should be changed in production

## License

This project is open source and available for personal and educational use.

