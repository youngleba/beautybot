import datetime
from typing import List, Dict

# В будущем можно сделать хранение расписания в БД,
# пока вернем просто пример с доступными слотами.
async def get_master_schedule(selected_date: datetime.date, master_id: int) -> List[Dict]:
    """
    Возвращает список доступных временных слотов для указанного мастера и даты.
    Шаг — 2 часа. Рабочие часы: с 10:00 до 20:00.
    """
    start_hour = 10
    end_hour = 20
    step = 2  # шаг в часах

    today = datetime.date.today()
    if selected_date < today:
        return []  # прошлые дни не доступны

    # создаем список слотов
    slots = []
    for hour in range(start_hour, end_hour, step):
        slot_time = datetime.time(hour, 0)
        slots.append({
            "time": slot_time.strftime("%H:%M"),
            "available": True
        })
    return slots
