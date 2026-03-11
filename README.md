# Automated Timetable Generator

A full-stack web application to automatically generate college timetables based on teachers, subjects, branches, and scheduling constraints.

## Features
- Manage Teachers, Subjects, and Branches
- Automatic Timetable Generation ensuring no scheduling conflicts
- Export generated timetable to PDF/Excel
- Responsive Bootstrap Interface

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you want to use the PDF export feature, you must have [wkhtmltopdf](https://wkhtmltopdf.org/) installed on your system and added to your system PATH.*

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Application**
   Open your browser and navigate to `http://127.0.0.1:5000`
