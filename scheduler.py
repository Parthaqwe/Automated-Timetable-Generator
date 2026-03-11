import models
import random

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '1:00-2:00', '2:00-3:00']

def generate_all_timetables():
    """Generates a non-conflicting timetable for all branches."""
    conn = models.get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing timetable
    cursor.execute('DELETE FROM timetable')
    
    # Fetch all branches, subjects, and teachers
    branches = cursor.execute('SELECT * FROM branches').fetchall()
    subjects = cursor.execute('SELECT * FROM subjects').fetchall()
    teachers = cursor.execute('SELECT * FROM teachers').fetchall()
    
    # Group teachers by subject
    subject_teacher_map = {}
    for t in teachers:
        if t['subject'] not in subject_teacher_map:
            subject_teacher_map[t['subject']] = []
        subject_teacher_map[t['subject']].append(t['name'])
        
    # Group subjects by branch
    branch_subjects_map = {}
    for s in subjects:
        if s['branch'] not in branch_subjects_map:
            branch_subjects_map[s['branch']] = []
        branch_subjects_map[s['branch']].append(s['name'])
    
    # Track teacher schedules to prevent double booking
    teacher_schedule = {t['name']: {d: {} for d in DAYS} for t in teachers}
    
    # Track teacher hours per day to enforce max 5 hours constraint
    teacher_hours = {t['name']: {d: 0 for d in DAYS} for t in teachers}
    
    # Generate schedule for each branch
    for branch in branches:
        branch_name = branch['name']
        branch_subs = branch_subjects_map.get(branch_name, [])
        
        if not branch_subs:
            continue # No subjects configured for this branch
            
        # Distribute the 25 weekly slots (5 slots/day * 5 days) among the branch's subjects
        total_slots = len(DAYS) * len(SLOTS)
        periods_per_sub = total_slots // len(branch_subs) if len(branch_subs) > 0 else 0
        rem = total_slots % len(branch_subs) if len(branch_subs) > 0 else 0
        
        schedule_pool = []
        for s in branch_subs:
            schedule_pool.extend([s] * periods_per_sub)
        
        # Distribute remaining slots randomly
        rem_subjects = random.sample(branch_subs, rem) if len(branch_subs) >= rem else branch_subs * (rem // len(branch_subs)) + random.sample(branch_subs, rem % len(branch_subs))
        schedule_pool.extend(rem_subjects)
            
        random.shuffle(schedule_pool)
        
        idx = 0
        for day in DAYS:
            for slot in SLOTS:
                if idx >= len(schedule_pool):
                    break
                    
                subject = schedule_pool[idx]
                
                # Find an available teacher for this subject
                available_teachers = subject_teacher_map.get(subject, [])
                
                # We shuffle to ensure fair distribution of workload among teachers of the same subject
                random.shuffle(available_teachers)
                assigned_teacher = "None" # Default to none if no teacher found
                
                for t in available_teachers:
                    # Constraint 1: Not assigned to another class in same slot
                    # Constraint 2: Cannot teach more than 5 hours a day (actually this is true since slots=5, but we enforce it anyway)
                    if slot not in teacher_schedule[t][day] and teacher_hours[t][day] < 5:
                        assigned_teacher = t
                        break
                
                if assigned_teacher != "None":
                    teacher_schedule[assigned_teacher][day][slot] = branch_name
                    teacher_hours[assigned_teacher][day] += 1
                    
                cursor.execute('''
                    INSERT INTO timetable (day, slot, subject, teacher, branch)
                    VALUES (?, ?, ?, ?, ?)
                ''', (day, slot, subject, assigned_teacher, branch_name))
                    
                idx += 1
                
    conn.commit()
    conn.close()

if __name__ == '__main__':
    generate_all_timetables()
    print("Timetable generated successfully.")
