# ClearDOH - Quick Start Guide

## For Non-Developers 👋

Welcome! This guide will help you get ClearDOH running on your computer, even if you've never coded before.

## Step 1: Install Required Software

### Install Python (Backend)
1. Go to https://www.python.org/downloads/
2. Download Python 3.9 or newer
3. Run the installer
4. **Important**: Check "Add Python to PATH" during installation

### Install Node.js (Frontend)
1. Go to https://nodejs.org/
2. Download the LTS version
3. Run the installer

### Verify Installation
Open Terminal (Mac) or Command Prompt (Windows) and type:
```bash
python --version
node --version
```

You should see version numbers for both.

## Step 2: Set Up the Backend

### Open Terminal and navigate to the project:
```bash
cd Cost-Report/backend
```

### Create a virtual environment:
```bash
python -m venv venv
```

### Activate the virtual environment:
**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Create environment file:
```bash
cp .env.example .env
```

### Start the backend server:
```bash
python -m uvicorn main:app --reload
```

You should see: `Uvicorn running on http://127.0.0.1:8000`

**Keep this terminal window open!**

## Step 3: Set Up the Frontend

### Open a NEW terminal window:
```bash
cd Cost-Report/frontend
```

### Install dependencies:
```bash
npm install
```

### Start the frontend:
```bash
npm run dev
```

You should see: `Local: http://localhost:3000`

**Keep this terminal window open too!**

## Step 4: Use the App

1. Open your web browser
2. Go to: http://localhost:3000
3. You should see the ClearDOH home page!

## Using ClearDOH

### Create Your First Report:

1. **Click "Create New Cost Report"**
2. **Enter Agency Details:**
   - Agency Name (e.g., "ABC Home Care")
   - Year (e.g., 2024)
3. **Click "Create & Start"**

### Upload Your Files:

4. **Drag and drop your files** into the upload boxes:
   - Payroll Register (PDF or CSV)
   - Trial Balance (Excel or CSV)
   - Visit Data/Schedule 5 (Excel or CSV)

5. **Click "Start Processing"**
   - The app will process files in the background (5-15 minutes)
   - You'll see a loading indicator

### Review Flagged Items:

6. **Review any yellow-flagged items**
   - These are items the AI wasn't 100% confident about
   - Click "Approve" if the suggested tag is correct
   - Click "Correct" to enter your own tag
   - Usually 0-20 items to review

### Generate Final Report:

7. **Click "Generate Final Report"**
   - The app creates your complete Excel file
   - Takes 1-2 minutes

8. **Download your report!**
   - Click "Download Excel Report"
   - You now have a complete DOH Cost Report

## Troubleshooting

### Backend won't start:
- Make sure virtual environment is activated (you should see `(venv)` in terminal)
- Try: `pip install -r requirements.txt` again

### Frontend won't start:
- Delete `node_modules` folder
- Run `npm install` again

### Can't access http://localhost:3000:
- Make sure both backend AND frontend are running
- Check for error messages in terminal windows

### Files won't upload:
- Check file size (max 50MB)
- Make sure backend is running (http://localhost:8000)
- Check terminal for error messages

## Getting Help

- Check the main README.md for technical details
- Look in the `/docs` folder for SOPs
- All error messages will appear in the terminal windows

## Stopping the App

When you're done:
1. Go to each terminal window
2. Press `Ctrl+C` (or `Cmd+C` on Mac)
3. Type `deactivate` in the backend terminal to exit virtual environment

## Next Time You Start

You only need to:
1. Open 2 terminal windows
2. Backend terminal:
   ```bash
   cd Cost-Report/backend
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   python -m uvicorn main:app --reload
   ```
3. Frontend terminal:
   ```bash
   cd Cost-Report/frontend
   npm run dev
   ```

That's it! You're now running ClearDOH locally. 🎉
