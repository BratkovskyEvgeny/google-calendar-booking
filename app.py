import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
import streamlit as st
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Загрузка переменных окружения
load_dotenv()

# Настройка страницы
st.set_page_config(
    page_title="Система бронирования встреч", page_icon="📅", layout="centered"
)

# Добавляем CSS стили
st.markdown(
    """
<style>
    .profile-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 2rem auto 3rem;
        flex-direction: column;
        max-width: 800px;
        padding: 20px;
    }
    .profile-photo {
        width: 180px;
        height: 180px;
        border-radius: 50%;
        object-fit: cover;
        margin-bottom: 1.5rem;
        border: 4px solid #1f61eb;
        box-shadow: 0 4px 12px rgba(31, 97, 235, 0.2);
        transition: transform 0.3s ease;
    }
    .profile-photo:hover {
        transform: scale(1.05);
    }
    .stButton button {
        width: 100%;
        border-radius: 5px;
        background-color: #f0f2f6;
        border: none;
        padding: 10px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #1f61eb;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(31, 97, 235, 0.2);
    }
    .time-slot {
        padding: 5px;
        text-align: center;
    }
    .date-header {
        background-color: #1f61eb;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(31, 97, 235, 0.1);
    }
    .booking-form {
        background-color: #f0f2f6;
        padding: 25px;
        border-radius: 12px;
        margin-top: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    h1 {
        color: #1f61eb;
        text-align: center;
        margin: 1rem 0 0.5rem;
        font-size: 2.2rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .subtitle {
        color: #666;
        text-align: center;
        margin-bottom: 1rem;
        font-size: 1.4rem;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    .slot-container {
        display: grid;
        gap: 10px;
        margin-bottom: 20px;
    }
    .date-header h3 {
        margin: 0;
        font-size: 1.2rem;
        font-weight: 500;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Настройки из Streamlit secrets
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = st.secrets["calendar_id"]
GMAIL_SENDER = st.secrets["gmail_sender"]
GMAIL_APP_PASSWORD = st.secrets["gmail_app_password"]
CLIENT_ID = st.secrets["google_client_id"]
CLIENT_SECRET = st.secrets["google_client_secret"]


def get_google_calendar_service():
    """Получение сервиса Google Calendar"""
    try:
        # Создаем учетные данные напрямую из secrets
        creds = Credentials(
            None,  # No token yet
            refresh_token=st.secrets.get("google_refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=st.secrets["google_client_id"],
            client_secret=st.secrets["google_client_secret"],
            scopes=SCOPES,
        )

        # Обновляем токен
        creds.refresh(Request())

        # Создаем и возвращаем сервис
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        st.error(f"Ошибка аутентификации: {str(e)}")
        st.error("Проверьте настройки OAuth и refresh token в секретах Streamlit.")
        st.stop()


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
    # Добавляем профиль и заголовок
    st.markdown(
        """
        <div class="profile-container">
            <img src="assets/profile.jpg" class="profile-photo" alt="Евгений Братковский">
            <h1>СВОБОДНЫЕ СЛОТЫ</h1>
            <div class="subtitle">БРАТКОВСКОГО ЕВГЕНИЯ</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Проверяем наличие refresh_token
    if not st.secrets.get("google_refresh_token"):
        st.error("Необходимо настроить OAuth. Пожалуйста, свяжитесь с администратором.")
        st.stop()

    # Получение свободных слотов
    try:
        free_slots = get_free_slots()
    except Exception as e:
        st.error(f"Ошибка при получении свободных слотов: {str(e)}")
        return

    if not free_slots:
        st.warning("⚠️ Нет доступных слотов на ближайшие 2 недели")
        return

    # Группировка слотов по дням
    slots_by_day = {}
    for slot in free_slots:
        day = slot.strftime("%Y-%m-%d")
        if day not in slots_by_day:
            slots_by_day[day] = []
        slots_by_day[day].append(slot)

    # Отображение слотов по дням
    for day, slots in slots_by_day.items():
        date_obj = datetime.strptime(day, "%Y-%m-%d")

        # Создаем контейнер для даты с красивым форматированием
        st.markdown(
            f"""
            <div class="date-header">
                <h3>{date_obj.strftime("%d %B %Y")}, {["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][date_obj.weekday()]}</h3>
            </div>
        """,
            unsafe_allow_html=True,
        )

        # Создаем сетку для временных слотов
        cols = st.columns(4)
        for i, slot in enumerate(slots):
            with cols[i % 4]:
                if st.button(
                    slot.strftime("%H:%M"),
                    key=slot.isoformat(),
                    use_container_width=True,
                ):
                    st.session_state.selected_slot = slot
                    st.session_state.show_booking_form = True

    # Форма бронирования
    if "show_booking_form" in st.session_state and st.session_state.show_booking_form:
        st.markdown('<div class="booking-form">', unsafe_allow_html=True)
        st.subheader("📝 Форма бронирования")
        with st.form("booking_form"):
            booker_email = st.text_input("📧 Ваш email:")
            submitted = st.form_submit_button("✅ Подтвердить бронирование")

            if submitted and booker_email:
                if create_calendar_event(st.session_state.selected_slot, booker_email):
                    if send_email_notification(
                        st.session_state.selected_slot.strftime("%Y-%m-%d %H:%M"),
                        booker_email,
                    ):
                        st.success(
                            "🎉 Встреча успешно забронирована! Проверьте вашу почту."
                        )
                    st.session_state.show_booking_form = False
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
