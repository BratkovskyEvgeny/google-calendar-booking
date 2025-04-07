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

    # Устанавливаем московский часовой пояс
    moscow_tz = pytz.timezone("Europe/Moscow")
    now = datetime.now(moscow_tz)

    # Начинаем с начала следующего дня
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    end_date = start_date + timedelta(days=14)

    # Получаем занятые слоты
    events_result = (
        service.events()
        .list(
            calendarId="primary",  # Используем primary вместо CALENDAR_ID
            timeMin=start_date.isoformat(),
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
        ).astimezone(moscow_tz)
        end = datetime.fromisoformat(
            event["end"].get("dateTime", event["end"].get("date"))
        ).astimezone(moscow_tz)

        # Пропускаем события, где вы не подтвердили участие
        response_status = next(
            (
                attendee["responseStatus"]
                for attendee in event.get("attendees", [])
                if attendee.get("self", False)
            ),
            event.get("status", "confirmed"),  # Для событий, где вы организатор
        )

        if response_status == "declined":
            continue

        # Добавляем все часовые слоты в период события
        current = start
        while current < end:
            busy_slots.append(current)
            current += timedelta(hours=1)

    # Создаем список всех возможных слотов
    all_slots = []
    current = start_date

    while current < end_date:
        # Проверяем только рабочие дни (0 = понедельник, 4 = пятница)
        if current.weekday() < 5:
            # Добавляем слоты с 9:00 до 17:00 (последняя встреча в 17:00)
            day_start = current.replace(hour=9, minute=0)
            day_end = current.replace(hour=17, minute=0)

            slot_time = day_start
            while slot_time <= day_end:
                all_slots.append(slot_time)
                slot_time += timedelta(hours=1)

        # Переходим к следующему дню
        current = (current + timedelta(days=1)).replace(hour=0, minute=0)

    # Возвращаем словарь с информацией о статусе каждого слота
    slots_info = {}
    for slot in all_slots:
        slot_end = slot + timedelta(hours=1)

        # Проверяем пересечения с занятыми слотами
        is_busy = any(
            (
                busy <= slot < busy + timedelta(hours=1)
            )  # Начало слота попадает в занятый период
            or (
                busy < slot_end <= busy + timedelta(hours=1)
            )  # Конец слота попадает в занятый период
            or (slot <= busy < slot_end)  # Занятый период внутри слота
            for busy in busy_slots
        )

        # Добавляем информацию о слоте
        slots_info[slot] = {
            "is_busy": is_busy,
            "time": slot.strftime("%H:%M"),
            "date": slot.strftime("%Y-%m-%d"),
        }

    return slots_info


def send_email_notification(slot_time, booker_email):
    """Отправка уведомления на email владельца"""
    msg = MIMEMultipart()
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_SENDER
    msg["Subject"] = "🗓️ New Meeting Booking"

    # Создаем HTML версию письма
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4dabf7;">New Meeting Booking</h2>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p><strong>📅 Date and time:</strong> {slot_time}</p>
                <p><strong>📧 Participant email:</strong> {booker_email}</p>
                <p><strong>⏱️ Duration:</strong> 1 hour</p>
            </div>
            <p style="color: #666; font-size: 14px;">
                The meeting has been automatically added to your Google Calendar.<br>
                An invitation has been sent to the participant's email.
            </p>
        </div>
    </body>
    </html>
    """

    # Создаем текстовую версию для клиентов, не поддерживающих HTML
    text_body = f"""
    New Meeting Booking
    
    Date and time: {slot_time}
    Participant email: {booker_email}
    Duration: 1 hour
    
    The meeting has been automatically added to your Google Calendar.
    An invitation has been sent to the participant's email.
    """

    # Добавляем обе версии в письмо
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False


def create_calendar_event(slot_time, booker_email):
    """Создание события в календаре"""
    service = get_google_calendar_service()

    # Убеждаемся, что используем московское время
    moscow_tz = pytz.timezone("Europe/Moscow")
    if slot_time.tzinfo != moscow_tz:
        slot_time = slot_time.astimezone(moscow_tz)

    event = {
        "summary": f"👥 Встреча с {booker_email}",
        "description": f"""
Встреча забронирована через систему бронирования.

Участник: {booker_email}
Длительность: 1 час

Автоматически создано системой бронирования встреч.
""",
        "start": {
            "dateTime": slot_time.isoformat(),
            "timeZone": "Europe/Moscow",
        },
        "end": {
            "dateTime": (slot_time + timedelta(hours=1)).isoformat(),
            "timeZone": "Europe/Moscow",
        },
        "attendees": [
            {"email": booker_email},
            {"email": GMAIL_SENDER},
        ],
        "sendUpdates": "all",
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    try:
        event = service.events().insert(calendarId="primary", body=event).execute()
        return True
    except Exception as e:
        st.error(f"Ошибка при создании события: {str(e)}")
        return False


def main():
    # Добавляем заголовок
    st.markdown(
        """
        <div class="header-container">
            <h1>AVAILABLE SLOTS</h1>
            <div class="subtitle">BRATKOVSKY EVGENY</div>
            <div class="form-description" style="margin-top: 20px; text-align: center;">
            Choose a convenient time for the meeting. Meeting duration - 1 hour.<br>
            Working hours: 9:00 AM to 6:00 PM (last meeting at 5:00 PM)<br>
            After selecting the time, you will need to enter your email to receive confirmation.
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
                Available
            </div>
            <div class="status-item">
                <div class="status-dot unavailable"></div>
                Busy
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
        day = info["date"]
        if day not in slots_by_day:
            slots_by_day[day] = []
        slots_by_day[day].append((slot, info))

    # Создаем общий контейнер для календаря
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)

    # Отображение слотов по дням
    for day, slots in slots_by_day.items():
        date_obj = datetime.strptime(day, "%Y-%m-%d")

        # Форматируем дату в соответствии с настройками (31/12/2025)
        formatted_date = date_obj.strftime("%d/%m/%Y")
        weekday = date_obj.strftime("%A")  # Полное название дня недели на английском

        # Создаем контейнер для даты
        st.markdown(
            f"""
            <div class="date-header">
                <h3>{formatted_date} · {weekday}</h3>
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
                        f'<button class="unavailable" disabled>{info["time"]}</button>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(
                        info["time"],
                        key=slot.isoformat(),
                        use_container_width=True,
                    ):
                        st.session_state.selected_slot = slot
                        st.session_state.show_booking_form = True

    st.markdown("</div>", unsafe_allow_html=True)

    # Форма бронирования
    if "show_booking_form" in st.session_state and st.session_state.show_booking_form:
        # Форматируем время в соответствии с настройками (31/12/2025, 13:00)
        selected_time = st.session_state.selected_slot.strftime("%d/%m/%Y, %H:%M")

        st.markdown('<div class="booking-form">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="form-header">📝 Meeting Booking</div>
            <div class="form-description">
            <b>Selected time:</b> {selected_time}<br>
            <b>Duration:</b> 1 hour<br><br>
            To confirm the booking, please enter your email address.<br>
            You will receive:
            <ul>
                <li>Booking confirmation</li>
                <li>Meeting link</li>
                <li>Reminder 1 hour before the meeting</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("booking_form"):
            booker_email = st.text_input(
                "📧 Your email address",
                help="You will receive booking confirmation and meeting details at this address",
            )
            submitted = st.form_submit_button("✅ Confirm Booking")

            if submitted:
                if not booker_email:
                    st.error("Please enter your email address")
                else:
                    if create_calendar_event(
                        st.session_state.selected_slot, booker_email
                    ):
                        if send_email_notification(
                            st.session_state.selected_slot.strftime("%d/%m/%Y %H:%M"),
                            booker_email,
                        ):
                            st.success(
                                "🎉 Meeting successfully booked! Check your email for details."
                            )
                        st.session_state.show_booking_form = False
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
