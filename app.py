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
    msg["Subject"] = "🗓️ New Meeting Request"

    # Создаем HTML версию письма с более подробной информацией
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4dabf7;">New Meeting Request</h2>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p><strong>📅 Date and time:</strong> {slot_time}</p>
                <p><strong>📧 Participant email:</strong> {booker_email}</p>
                <p><strong>⏱️ Duration:</strong> 1 hour</p>
            </div>
            <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #495057;"><strong>What happens next:</strong></p>
                <ul style="color: #495057; margin: 10px 0;">
                    <li>The meeting has been added to your Google Calendar</li>
                    <li>You will receive a Google Calendar invitation</li>
                    <li>You will get an email reminder 1 hour before the meeting</li>
                    <li>You will see a popup notification 10 minutes before the meeting</li>
                </ul>
            </div>
            <div style="background-color: #e7f5ff; padding: 15px; border-radius: 5px;">
                <p style="margin: 0; color: #1971c2;"><strong>Need to reschedule?</strong><br>
                You can accept, decline, or propose a new time directly in Google Calendar.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Создаем текстовую версию для клиентов, не поддерживающих HTML
    text_body = f"""
    New Meeting Request

    📅 Date and time: {slot_time}
    📧 Participant email: {booker_email}
    ⏱️ Duration: 1 hour

    What happens next:
    - The meeting has been added to your Google Calendar
    - You will receive a Google Calendar invitation
    - You will get an email reminder 1 hour before the meeting
    - You will see a popup notification 10 minutes before the meeting

    Need to reschedule?
    You can accept, decline, or propose a new time directly in Google Calendar.
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
        "summary": f"👥 Meeting with {booker_email}",
        "description": f"""
Meeting Request Details:

👤 Participant: {booker_email}
⏱️ Duration: 1 hour
📍 Location: Google Meet (link will be generated automatically)

This meeting was booked through the Meeting Scheduler system.
You can accept, decline, or propose a new time using the options above.

Need to contact the participant? Reply to this invitation or use their email: {booker_email}
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
        "sendUpdates": "all",  # Отправляем уведомления всем участникам
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60},  # Email за час до встречи
                {
                    "method": "popup",
                    "minutes": 10,
                },  # Всплывающее уведомление за 10 минут
            ],
        },
        "conferenceData": {
            "createRequest": {
                "requestId": f"meeting_{int(datetime.now().timestamp())}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    try:
        event = (
            service.events()
            .insert(
                calendarId="primary",
                body=event,
                conferenceDataVersion=1,  # Добавляем поддержку Google Meet
                sendUpdates="all",  # Отправляем уведомления всем участникам
            )
            .execute()
        )
        return True
    except Exception as e:
        st.error(f"Error creating event: {str(e)}")
        return False


def main():
    # Инициализация состояния для отображения дополнительных дней
    if "show_all_days" not in st.session_state:
        st.session_state.show_all_days = False

    # Настраиваем стили
    st.markdown(
        """
        <style>
        /* Общие стили */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #1e1e1e 0%, #2b2b2b 100%);
            color: #e0e0e0;
        }
        
        /* Заголовок */
        .header-container {
            text-align: center;
            padding: 2rem 1rem;
            margin-bottom: 2rem;
            background: rgba(43, 43, 43, 0.7);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 215, 0, 0.1);
            box-shadow: 0 4px 12px rgba(255, 215, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .header-container:hover {
            border-color: rgba(255, 215, 0, 0.2);
            box-shadow: 0 6px 16px rgba(255, 215, 0, 0.08);
        }
        
        .header-container h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(45deg, #ffd700 0%, #ffb700 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .subtitle {
            font-size: 1.2rem;
            color: #ffd700;
            margin-bottom: 1.5rem;
            letter-spacing: 1px;
            opacity: 0.8;
        }
        
        .form-description {
            color: #d4d4d4;
            line-height: 1.6;
            font-size: 1rem;
        }
        
        /* Статус слотов */
        .slot-status {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 2rem 0;
            padding: 1rem;
            background: rgba(43, 43, 43, 0.7);
            border-radius: 10px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 215, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .slot-status:hover {
            border-color: rgba(255, 215, 0, 0.2);
            box-shadow: 0 4px 12px rgba(255, 215, 0, 0.05);
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #d4d4d4;
            font-size: 0.95rem;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            transition: all 0.3s ease;
        }
        
        .status-dot.available {
            background: linear-gradient(45deg, #ffd700 0%, #ffb700 100%);
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
        }
        
        .status-dot.unavailable {
            background: linear-gradient(45deg, #fc8181 0%, #e53e3e 100%);
            box-shadow: 0 0 10px rgba(229, 62, 62, 0.3);
        }
        
        /* Заголовок даты */
        .date-header {
            background: rgba(43, 43, 43, 0.7);
            border-radius: 10px;
            padding: 1rem;
            margin: 2rem 0 1rem 0;
            border: 1px solid rgba(255, 215, 0, 0.1);
            transition: all 0.3s ease;
            animation: slideIn 0.5s ease-out;
        }
        
        .date-header:hover {
            border-color: rgba(255, 215, 0, 0.2);
            box-shadow: 0 4px 12px rgba(255, 215, 0, 0.05);
        }
        
        .date-header h3 {
            color: #ffd700;
            font-size: 1.2rem;
            font-weight: 600;
            margin: 0;
        }
        
        /* Кнопки слотов */
        .stButton button {
            width: 100%;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            background: rgba(255, 215, 0, 0.1);
            color: #ffd700;
            border: 1px solid rgba(255, 215, 0, 0.2);
            animation: fadeIn 0.5s ease-out;
        }
        
        .stButton button:hover {
            background: rgba(255, 215, 0, 0.15);
            border-color: rgba(255, 215, 0, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 215, 0, 0.1);
        }
        
        button.unavailable {
            background: rgba(229, 62, 62, 0.1) !important;
            color: #fc8181 !important;
            border: 1px solid rgba(229, 62, 62, 0.2) !important;
            cursor: not-allowed !important;
            opacity: 0.8 !important;
        }
        
        button.unavailable:hover {
            background: rgba(229, 62, 62, 0.1) !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        /* Форма бронирования */
        .booking-form {
            background: rgba(43, 43, 43, 0.7);
            border-radius: 15px;
            padding: 2rem;
            margin: 2rem 0;
            border: 1px solid rgba(255, 215, 0, 0.1);
            backdrop-filter: blur(10px);
            animation: slideUp 0.5s ease-out;
            transition: all 0.3s ease;
        }
        
        .booking-form:hover {
            border-color: rgba(255, 215, 0, 0.2);
            box-shadow: 0 6px 16px rgba(255, 215, 0, 0.08);
        }
        
        .form-header {
            font-size: 1.5rem;
            font-weight: 600;
            color: #ffd700;
            margin-bottom: 1.5rem;
        }
        
        /* Чекбокс для отображения дополнительных дней */
        .show-more-days {
            background: rgba(43, 43, 43, 0.7);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 215, 0, 0.1);
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .show-more-days:hover {
            border-color: rgba(255, 215, 0, 0.2);
            box-shadow: 0 4px 12px rgba(255, 215, 0, 0.05);
        }
        
        /* Анимации */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .header-container {
            animation: fadeIn 0.6s ease-out;
        }
        
        .slot-status {
            animation: slideIn 0.7s ease-out;
        }
        
        .calendar-container {
            animation: fadeIn 0.8s ease-out;
        }
        
        /* Стилизация чекбокса Streamlit */
        .stCheckbox {
            color: #ffd700 !important;
        }
        
        .stCheckbox > label {
            color: #ffd700 !important;
            font-size: 1rem !important;
        }
        
        .stCheckbox > div[role="checkbox"] {
            border-color: rgba(255, 215, 0, 0.3) !important;
        }
        
        .stCheckbox > div[role="checkbox"][aria-checked="true"] {
            background-color: #ffd700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Добавляем заголовок
    st.markdown(
        """
        <div class="header-container">
            <h1>MEETING SCHEDULER</h1>
            <div class="subtitle">BRATKOVSKY EVGENY</div>
            <div class="form-description">
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

    # Добавляем чекбокс для отображения дополнительных дней
    st.markdown('<div class="show-more-days">', unsafe_allow_html=True)
    st.checkbox("📅 Показать все доступные дни", key="show_all_days")
    st.markdown("</div>", unsafe_allow_html=True)

    # Создаем общий контейнер для календаря
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)

    # Отображение слотов по дням с учетом выбранного количества дней
    sorted_days = sorted(slots_by_day.keys())
    days_to_show = sorted_days if st.session_state.show_all_days else sorted_days[:3]

    for day in days_to_show:
        slots = slots_by_day[day]
        date_obj = datetime.strptime(day, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d/%m/%Y")
        weekday = date_obj.strftime("%A")

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
