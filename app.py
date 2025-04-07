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
    page_title="Система бронирования встреч",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Добавляем CSS стили
st.markdown(
    """
<style>
    .header-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 2rem auto;
        flex-direction: column;
        max-width: 800px;
        background-color: #2b2b2b;
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid #3c3f41;
    }
    .stButton button {
        width: 100%;
        border-radius: 4px;
        background-color: #2b2b2b;
        border: 1px solid #3c3f41;
        padding: 8px 4px;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        margin: 1px 0;
        color: #a9b7c6;
    }
    .stButton button:hover {
        background-color: #4dabf7;
        color: #2b2b2b;
        border-color: #4dabf7;
        transform: translateY(-1px);
    }
    .date-header {
        background-color: #323232;
        color: #a9b7c6;
        padding: 10px 15px;
        border-radius: 4px;
        margin: 12px 0 8px;
        font-size: 0.9rem;
        border: 1px solid #3c3f41;
    }
    .booking-form {
        background-color: #2b2b2b;
        padding: 25px;
        border-radius: 8px;
        margin-top: 30px;
        border: 1px solid #3c3f41;
    }
    h1 {
        color: #4dabf7;
        text-align: center;
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
        letter-spacing: 1px;
    }
    .subtitle {
        color: #a9b7c6;
        text-align: center;
        margin: 0.5rem 0 0;
        font-size: 1.1rem;
        font-weight: 400;
        opacity: 0.9;
    }
    .calendar-container {
        background-color: #2b2b2b;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #3c3f41;
        margin: 0 -1rem;
    }
    .date-header h3 {
        margin: 0;
        font-size: 1rem;
        font-weight: 500;
        color: #a9b7c6;
    }
    .slot-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 6px;
        padding: 6px 0;
    }
    .stApp {
        background-color: #1e1f22;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    #MainMenu {
        display: none;
    }
    footer {
        display: none;
    }
    div[data-testid="stDecoration"] {
        display: none;
    }
    div[data-testid="stStatusWidget"] {
        display: none;
    }
    .stApp > header {
        display: none;
    }
    .stForm button {
        background-color: #4dabf7;
        color: #2b2b2b;
        font-weight: 500;
        padding: 10px 20px;
        width: 100%;
        margin-top: 10px;
        font-size: 1rem;
    }
    .stForm button:hover {
        background-color: #339af0;
        border-color: #339af0;
    }
    .form-description {
        color: #a9b7c6;
        font-size: 0.9rem;
        margin: 10px 0;
        opacity: 0.8;
    }
    .form-header {
        color: #4dabf7;
        font-size: 1.2rem;
        margin-bottom: 15px;
        font-weight: 500;
    }
    /* Darcula theme additional styles */
    .stTextInput input {
        background-color: #2b2b2b !important;
        color: #a9b7c6 !important;
        border: 1px solid #3c3f41 !important;
        padding: 10px !important;
        font-size: 1rem !important;
    }
    .stTextInput input:focus {
        border-color: #4dabf7 !important;
        box-shadow: none !important;
    }
    div[data-baseweb="base-input"] {
        background-color: #2b2b2b !important;
    }
    .stMarkdown {
        color: #a9b7c6 !important;
    }
    p {
        color: #a9b7c6 !important;
    }
    .stAlert {
        background-color: #2b2b2b !important;
        color: #a9b7c6 !important;
        border: 1px solid #3c3f41 !important;
    }
    .stAlert > div {
        color: #a9b7c6 !important;
    }
    /* Fix for streamlit components */
    button[kind="primary"] {
        background-color: #4dabf7 !important;
        color: #2b2b2b !important;
    }
    button[kind="primary"]:hover {
        background-color: #339af0 !important;
    }
    .stButton button.unavailable {
        background-color: #3c2222 !important;
        color: #ff6b6b !important;
        border-color: #ff6b6b !important;
        cursor: not-allowed !important;
        opacity: 0.7;
    }
    .stButton button.unavailable:hover {
        background-color: #3c2222 !important;
        color: #ff6b6b !important;
        border-color: #ff6b6b !important;
        transform: none !important;
    }
    button.unavailable {
        background-color: #3c2222 !important;
        color: #ff6b6b !important;
        border: 1px solid #ff6b6b !important;
        cursor: not-allowed !important;
        opacity: 0.7 !important;
        pointer-events: none !important;
    }
    button.unavailable:hover {
        background-color: #3c2222 !important;
        color: #ff6b6b !important;
        border-color: #ff6b6b !important;
        transform: none !important;
    }
    .slot-status {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 20px 0;
        padding: 10px;
        background-color: #2b2b2b;
        border-radius: 4px;
        border: 1px solid #3c3f41;
    }
    .status-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #a9b7c6;
        font-size: 0.9rem;
    }
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    .status-dot.available {
        background-color: #4dabf7;
    }
    .status-dot.unavailable {
        background-color: #ff6b6b;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Скрываем меню и футер
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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
    """Получение свободных и занятых слотов из календаря"""
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
    busy_slots = []

    # Преобразуем события в список занятых слотов
    for event in events:
        start = datetime.fromisoformat(
            event["start"].get("dateTime", event["start"].get("date"))
        ).astimezone(pytz.UTC)
        end = datetime.fromisoformat(
            event["end"].get("dateTime", event["end"].get("date"))
        ).astimezone(pytz.UTC)

        # Добавляем все часовые слоты в период события
        current = start
        while current < end:
            busy_slots.append(current)
            current += timedelta(hours=1)

    # Создаем список всех возможных слотов
    all_slots = []
    current = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if current < now:
        current = current + timedelta(days=1)

    while current < end_date:
        if (
            current.hour >= 9 and current.hour < 18 and current.weekday() < 5
        ):  # Рабочий день с 9 до 18
            # Добавляем слот только если встреча закончится до 18:00
            if current.hour < 17:  # Последняя встреча начинается в 17:00
                all_slots.append(current)
        current += timedelta(hours=1)
        if current.hour >= 18:
            current = (current + timedelta(days=1)).replace(hour=9, minute=0)

    # Возвращаем словарь с информацией о статусе каждого слота
    slots_info = {}
    for slot in all_slots:
        # Проверяем, не пересекается ли слот с уже занятыми
        slot_end = slot + timedelta(hours=1)
        is_busy = any(
            (busy <= slot < busy + timedelta(hours=1))
            or (busy < slot_end <= busy + timedelta(hours=1))
            or (slot <= busy < slot_end)
            for busy in busy_slots
        )
        slots_info[slot] = {"is_busy": is_busy}

    return slots_info


def send_email_notification(slot_time, booker_email):
    """Отправка уведомления на email владельца"""
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
            "dateTime": (
                slot_time + timedelta(hours=1)
            ).isoformat(),  # Изменено на 1 час
            "timeZone": "UTC",
        },
        "attendees": [
            {"email": booker_email},
            {"email": GMAIL_SENDER},
        ],
        "sendUpdates": "all",
    }

    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True
    except Exception as e:
        st.error(f"Ошибка при создании события: {str(e)}")
        return False


def main():
    # Добавляем заголовок
    st.markdown(
        """
        <div class="header-container">
            <h1>СВОБОДНЫЕ СЛОТЫ</h1>
            <div class="subtitle">БРАТКОВСКОГО ЕВГЕНИЯ</div>
            <div class="form-description" style="margin-top: 20px; text-align: center;">
            Выберите удобное время для встречи. Длительность встречи - 1 час.<br>
            Рабочий день: с 9:00 до 18:00 (последняя встреча в 17:00)<br>
            После выбора времени вам нужно будет указать свой email для получения подтверждения.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Добавляем легенду статусов
    st.markdown(
        """
        <div class="slot-status">
            <div class="status-item">
                <div class="status-dot available"></div>
                Свободно
            </div>
            <div class="status-item">
                <div class="status-dot unavailable"></div>
                Занято
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Проверяем наличие refresh_token
    if not st.secrets.get("google_refresh_token"):
        st.error("Необходимо настроить OAuth. Пожалуйста, свяжитесь с администратором.")
        st.stop()

    # Получение информации о слотах
    try:
        slots_info = get_free_slots()
    except Exception as e:
        st.error(f"Ошибка при получении слотов: {str(e)}")
        return

    if not slots_info:
        st.warning("⚠️ Нет доступных слотов на ближайшие 2 недели")
        return

    # Группировка слотов по дням
    slots_by_day = {}
    for slot, info in slots_info.items():
        day = slot.strftime("%Y-%m-%d")
        if day not in slots_by_day:
            slots_by_day[day] = []
        slots_by_day[day].append((slot, info))

    # Создаем общий контейнер для календаря
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)

    # Отображение слотов по дням
    for day, slots in slots_by_day.items():
        date_obj = datetime.strptime(day, "%Y-%m-%d")

        # Создаем контейнер для даты
        st.markdown(
            f"""
            <div class="date-header">
                <h3>{date_obj.strftime("%d %B %Y")} · {["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][date_obj.weekday()]}</h3>
            </div>
        """,
            unsafe_allow_html=True,
        )

        # Создаем сетку для временных слотов (6 колонок)
        cols = st.columns(6)
        for i, (slot, info) in enumerate(slots):
            with cols[i % 6]:
                if info["is_busy"]:
                    st.markdown(
                        f'<button class="unavailable" disabled>{slot.strftime("%H:%M")}</button>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(
                        slot.strftime("%H:%M"),
                        key=slot.isoformat(),
                        use_container_width=True,
                    ):
                        st.session_state.selected_slot = slot
                        st.session_state.show_booking_form = True

    st.markdown("</div>", unsafe_allow_html=True)

    # Форма бронирования
    if "show_booking_form" in st.session_state and st.session_state.show_booking_form:
        selected_time = st.session_state.selected_slot.strftime("%d %B %Y, %H:%M")

        st.markdown('<div class="booking-form">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="form-header">📝 Бронирование встречи</div>
            <div class="form-description">
            <b>Выбранное время:</b> {selected_time}<br>
            <b>Длительность:</b> 1 час<br><br>
            Для подтверждения бронирования, пожалуйста, введите ваш email адрес.<br>
            На этот адрес будут отправлены:
            <ul>
                <li>Подтверждение бронирования</li>
                <li>Ссылка для подключения к встрече</li>
                <li>Напоминание за 1 час до встречи</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("booking_form"):
            booker_email = st.text_input(
                "📧 Ваш email адрес",
                help="На этот адрес будет отправлено подтверждение бронирования и детали встречи",
            )
            submitted = st.form_submit_button("✅ Подтвердить бронирование")

            if submitted:
                if not booker_email:
                    st.error("Пожалуйста, введите ваш email адрес")
                else:
                    if create_calendar_event(
                        st.session_state.selected_slot, booker_email
                    ):
                        if send_email_notification(
                            st.session_state.selected_slot.strftime("%Y-%m-%d %H:%M"),
                            booker_email,
                        ):
                            st.success(
                                "🎉 Встреча успешно забронирована! Проверьте вашу почту для получения деталей."
                            )
                        st.session_state.show_booking_form = False
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
