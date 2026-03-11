from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import models
import scheduler
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Needed for flash messages

# Ensure DB is initialized
models.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    conn = models.get_db_connection()
    teacher_count = conn.execute('SELECT COUNT(*) FROM teachers').fetchone()[0]
    subject_count = conn.execute('SELECT COUNT(*) FROM subjects').fetchone()[0]
    branch_count = conn.execute('SELECT COUNT(*) FROM branches').fetchone()[0]
    conn.close()
    return render_template('dashboard.html', 
                           teacher_count=teacher_count, 
                           subject_count=subject_count, 
                           branch_count=branch_count)

@app.route('/teachers', methods=('GET', 'POST'))
def teachers():
    conn = models.get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form['subject']
        if not name or not subject:
            flash('Name and Subject are required!')
        else:
            conn.execute('INSERT INTO teachers (name, subject) VALUES (?, ?)', (name, subject))
            conn.commit()
            flash('Teacher added successfully!')
            return redirect(url_for('teachers'))
            
    teachers_list = conn.execute('SELECT * FROM teachers').fetchall()
    conn.close()
    return render_template('teachers.html', teachers=teachers_list)

@app.route('/subjects', methods=('GET', 'POST'))
def subjects():
    conn = models.get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        branch = request.form['branch']
        if not name or not branch:
            flash('Name and Branch are required!')
        else:
            conn.execute('INSERT INTO subjects (name, branch) VALUES (?, ?)', (name, branch))
            conn.commit()
            flash('Subject added successfully!')
            return redirect(url_for('subjects'))
            
    subjects_list = conn.execute('SELECT * FROM subjects').fetchall()
    # Need branches for the dropdown
    branches_list = conn.execute('SELECT * FROM branches').fetchall()
    conn.close()
    return render_template('subjects.html', subjects=subjects_list, branches=branches_list)

@app.route('/branches', methods=('GET', 'POST'))
def branches():
    conn = models.get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        if not name:
            flash('Branch name is required!')
        else:
            try:
                conn.execute('INSERT INTO branches (name) VALUES (?)', (name,))
                conn.commit()
                flash('Branch added successfully!')
            except Exception as e:
                flash('Branch already exists or error occurred.')
            return redirect(url_for('branches'))
            
    branches_list = conn.execute('SELECT * FROM branches').fetchall()
    conn.close()
    return render_template('branches.html', branches=branches_list)

@app.route('/generate', methods=('GET', 'POST'))
def generate():
    if request.method == 'POST':
        scheduler.generate_all_timetables()
        flash('Timetable generated successfully for all branches!')
        return redirect(url_for('timetable'))
    return render_template('generate.html')

@app.route('/timetable')
def timetable():
    conn = models.get_db_connection()
    branches = conn.execute('SELECT * FROM branches').fetchall()
    
    selected_branch = request.args.get('branch')
    if not selected_branch and branches:
        selected_branch = branches[0]['name']
        
    cursor = conn.cursor()
    if selected_branch:
        schedule_data = cursor.execute('SELECT * FROM timetable WHERE branch = ?', (selected_branch,)).fetchall()
    else:
        schedule_data = []
        
    # Organize data into a grid: grid[day][slot] = {'subject': ..., 'teacher': ...}
    grid = {d: {s: None for s in scheduler.SLOTS} for d in scheduler.DAYS}
    for row in schedule_data:
        grid[row['day']][row['slot']] = {'subject': row['subject'], 'teacher': row['teacher']}
        
    conn.close()
    return render_template('timetable.html', branches=branches, selected_branch=selected_branch, grid=grid, days=scheduler.DAYS, slots=scheduler.SLOTS)

@app.route('/workload')
def workload():
    conn = models.get_db_connection()
    teachers = conn.execute('SELECT * FROM teachers').fetchall()
    schedule_data = conn.execute('SELECT * FROM timetable').fetchall()
    conn.close()
    
    # Calculate hours per day per teacher
    workload_data = {t['name']: {d: 0 for d in scheduler.DAYS} for t in teachers}
    for row in schedule_data:
        if row['teacher'] != 'None' and row['teacher'] in workload_data:
            workload_data[row['teacher']][row['day']] += 1
            
    # Add total
    for t in workload_data:
        workload_data[t]['Total'] = sum(workload_data[t].values())
        
    return render_template('workload.html', workload=workload_data, days=scheduler.DAYS)

@app.route('/export/excel')
def export_excel():
    conn = models.get_db_connection()
    df = pd.read_sql_query("SELECT * FROM timetable", conn)
    conn.close()
    
    response = make_response(df.to_csv(index=False))
    response.headers["Content-Disposition"] = "attachment; filename=timetable.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/export/pdf')
def export_pdf():
    # PDF export requires pdfkit and wkhtmltopdf installed on the system
    import pdfkit
    conn = models.get_db_connection()
    branches = conn.execute('SELECT * FROM branches').fetchall()
    
    selected_branch = request.args.get('branch')
    if not selected_branch and branches:
        selected_branch = branches[0]['name']
        
    cursor = conn.cursor()
    if selected_branch:
        schedule_data = cursor.execute('SELECT * FROM timetable WHERE branch = ?', (selected_branch,)).fetchall()
    else:
        schedule_data = []
        
    grid = {d: {s: None for s in scheduler.SLOTS} for d in scheduler.DAYS}
    for row in schedule_data:
        grid[row['day']][row['slot']] = {'subject': row['subject'], 'teacher': row['teacher']}
        
    conn.close()
    
    html = render_template('timetable_pdf.html', selected_branch=selected_branch, grid=grid, days=scheduler.DAYS, slots=scheduler.SLOTS)
    try:
        pdf = pdfkit.from_string(html, False)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=timetable_{selected_branch}.pdf'
        return response
    except Exception as e:
        flash(f"PDF Export Error: Ensure wkhtmltopdf is installed. ({str(e)})")
        return redirect(url_for('timetable'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
