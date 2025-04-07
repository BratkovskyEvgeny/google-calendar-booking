import os
import pickle
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
import streamlit as st
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.discovery import build

# Загрузка переменных окружения
load_dotenv()

# Настройки
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
GMAIL_SENDER = os.getenv("GMAIL_SENDER", "zhenyabratkovski5@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def get_google_calendar_service():
    """Получение сервиса Google Calendar"""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)


def get_free_slots():
    """Получение свободных слотов из календаря"""
    service = get_google_calendar_service()

    # Получаем временные границы для проверки (следующие 2 недели)
    now = datetime.now(pytz.UTC)
    end_date = now + timedelta(days=14)

    # Получаем занятые слоты
    events_result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=now.isoformat(),
            timeMax=end_date.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    # Создаем список всех возможных слотов (с 9:00 до 18:00, по 30 минут)
    all_slots = []
    current = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if current < now:
        current = current + timedelta(days=1)

    while current < end_date:
        if (
            current.hour >= 9 and current.hour < 18 and current.weekday() < 5
        ):  # Только рабочие часы и дни
            all_slots.append(current)
        current += timedelta(minutes=30)
        if current.hour >= 18:
            current = (current + timedelta(days=1)).replace(hour=9, minute=0)

    # Фильтруем занятые слоты
    free_slots = []
    for slot in all_slots:
        is_free = True
        slot_end = slot + timedelta(minutes=30)

        for event in events:
            start = datetime.fromisoformat(
                event["start"].get("dateTime", event["start"].get("date"))
            ).astimezone(pytz.UTC)
            end = datetime.fromisoformat(
                event["end"].get("dateTime", event["end"].get("date"))
            ).astimezone(pytz.UTC)

            if slot < end and slot_end > start:
                is_free = False
                break

        if is_free:
            free_slots.append(slot)

    return free_slots


def send_email_notification(slot_time, booker_email):
    """Отправка уведомления на email"""
    msg = MIMEMultipart()
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_SENDER
    msg["Subject"] = "Новая бронь встречи"

    body = f"""
    Новая бронь встречи:
    Время: {slot_time}
    Email участника: {booker_email}
    """

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Ошибка при отправке email: {str(e)}")
        return False


def create_calendar_event(slot_time, booker_email):
    """Создание события в календаре"""
    service = get_google_calendar_service()

    event = {
        "summary": f"Встреча с {booker_email}",
        "description": f"Встреча забронирована пользователем {booker_email}",
        "start": {
            "dateTime": slot_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": (slot_time + timedelta(minutes=30)).isoformat(),
            "timeZone": "UTC",
        },
        "attendees": [
            {"email": booker_email},
        ],
    }

    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True
    except Exception as e:
        st.error(f"Ошибка при создании события: {str(e)}")
        return False


def main():
    st.title("Система бронирования встреч")

    # Получение свободных слотов
    try:
        free_slots = get_free_slots()
    except Exception as e:
        st.error(f"Ошибка при получении свободных слотов: {str(e)}")
        return

    if not free_slots:
        st.warning("Нет доступных слотов на ближайшие 2 недели")
        return

    # Отображение доступных слотов
    st.subheader("Доступные слоты:")

    # Группировка слотов по дням
    slots_by_day = {}
    for slot in free_slots:
        day = slot.strftime("%Y-%m-%d")
        if day not in slots_by_day:
            slots_by_day[day] = []
        slots_by_day[day].append(slot)

    # Отображение слотов по дням
    for day, slots in slots_by_day.items():
        st.write(f"**{datetime.strptime(day, '%Y-%m-%d').strftime('%d %B %Y')}**")
        cols = st.columns(4)
        for i, slot in enumerate(slots):
            if cols[i % 4].button(slot.strftime("%H:%M"), key=slot.isoformat()):
                st.session_state.selected_slot = slot
                st.session_state.show_booking_form = True

    # Форма бронирования
    if "show_booking_form" in st.session_state and st.session_state.show_booking_form:
        st.subheader("Форма бронирования")
        with st.form("booking_form"):
            booker_email = st.text_input("Ваш email:")
            submitted = st.form_submit_button("Подтвердить бронирование")

            if submitted and booker_email:
                if create_calendar_event(st.session_state.selected_slot, booker_email):
                    if send_email_notification(
                        st.session_state.selected_slot.strftime("%Y-%m-%d %H:%M"),
                        booker_email,
                    ):
                        st.success(
                            "Встреча успешно забронирована! Проверьте вашу почту."
                        )
                    st.session_state.show_booking_form = False
                    st.rerun()


if __name__ == "__main__":
    main()
