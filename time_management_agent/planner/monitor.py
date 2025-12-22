from database import get_pending_tasks, save_schedule

def replan_tasks():
    pending = get_pending_tasks()

    day = "Replanned Day"
    start_hour = 6

    for task in pending:
        subject = task[0]
        time_slot = f"{start_hour}:00 - {start_hour + 2}:00"
        save_schedule(day, subject, time_slot, "replanned")
        start_hour += 2