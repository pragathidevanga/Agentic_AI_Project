from database import save_schedule

DAYS = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6"]

def create_weekly_schedule(tasks, hours):
    timetable = []
    day_index = 0

    for task in tasks:
        day = DAYS[day_index % len(DAYS)]
        time_slot = f"{hours} hours"

        save_schedule(day, task, time_slot)

        # ✅ RETURNING 3 VALUES
        timetable.append((day, task, time_slot))

        day_index += 1

    return timetable
