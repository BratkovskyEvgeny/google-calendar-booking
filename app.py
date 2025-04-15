import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
import streamlit as st
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Настройка страницы (должна быть первой командой Streamlit)
st.set_page_config(
    page_title="Система бронирования встреч",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Создаем директорию для логов, если её нет
logs_dir = os.path.join(os.getcwd(), "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Полный путь к файлу логов
log_file = os.path.join(logs_dir, "email_logs.txt")

# Настройка логирования
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

# Выводим информацию о расположении файла логов
st.sidebar.markdown("### Информация о логах")
st.sidebar.info(f"Файл логов: {log_file}")

# Добавляем кнопку для просмотра логов
if st.sidebar.button("Показать логи"):
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            logs = f.read()
            if logs:
                st.sidebar.code(logs)
            else:
                st.sidebar.info("Файл логов пуст")
    except FileNotFoundError:
        st.sidebar.error("Файл логов не найден")
    except Exception as e:
        st.sidebar.error(f"Ошибка при чтении логов: {str(e)}")


# Функция для логирования
def log_email_operation(message, level="info"):
    """Записывает сообщение в лог и отображает его на странице"""
    if level == "info":
        logging.info(message)
    elif level == "error":
        logging.error(message)
    elif level == "warning":
        logging.warning(message)

    # Добавляем временную метку к сообщению
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {message}"


# Загрузка переменных окружения
load_dotenv()

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
        gap: 20px;
        margin: 20px 0;
        justify-content: center;
    }
    .status-item {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    .status-dot.available {
        background: rgba(43, 43, 43, 0.7);
        border: 1px solid rgba(255, 215, 0, 0.1);
    }
    .status-dot.unavailable {
        background: linear-gradient(145deg, #dc3545, #c82333);
    }
    /* Стили для контейнера сообщений */
    .messages-container {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 300px;
        z-index: 9999;
        background: rgba(43, 43, 43, 0.95);
        border-radius: 8px;
        border: 1px solid rgba(255, 215, 0, 0.2);
        backdrop-filter: blur(10px);
        padding: 10px;
        max-height: 80vh;
        overflow-y: auto;
    }

    .message {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 6px;
        font-size: 0.9rem;
        animation: fadeIn 0.3s ease;
    }

    .message.info {
        background: rgba(13, 110, 253, 0.2);
        border: 1px solid rgba(13, 110, 253, 0.3);
        color: #8bb9fe;
    }

    .message.success {
        background: rgba(25, 135, 84, 0.2);
        border: 1px solid rgba(25, 135, 84, 0.3);
        color: #75b798;
    }

    .message.error {
        background: rgba(220, 53, 69, 0.2);
        border: 1px solid rgba(220, 53, 69, 0.3);
        color: #ea868f;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Увеличиваем время отображения стандартных уведомлений */
    div[data-testid="stNotificationContent"] {
        animation: none !important;
        transition: opacity 0.5s ease !important;
    }

    /* Стили для слотов */
    .stButton > button {
        width: 100%;
        padding: 10px;
        margin: 5px 0;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.3s ease;
        text-align: center;
        color: #a9b7c6;
        background: rgba(43, 43, 43, 0.7);
        border: 1px solid rgba(255, 215, 0, 0.1);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }

    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);
        background: rgba(255, 165, 0, 0.2) !important;
        border-color: rgba(255, 165, 0, 0.4) !important;
        animation: pulse 1.5s infinite;
    }

    /* Стиль для выбранного слота */
    .stButton > button[aria-pressed="true"] {
        background: rgba(255, 165, 0, 0.4) !important;
        border-color: rgba(255, 165, 0, 0.6) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(255, 165, 0, 0.4);
        transform: translateY(-2px) scale(1.02);
    }

    @keyframes pulse {
        0% {
            box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);
        }
        50% {
            box-shadow: 0 4px 20px rgba(255, 165, 0, 0.4);
        }
        100% {
            box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);
        }
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 165, 0, 0.2),
            transparent
        );
        transition: 0.5s;
    }

    .stButton > button:hover::before {
        left: 100%;
    }

    .stButton > button.unavailable {
        background: linear-gradient(145deg, #dc3545, #c82333) !important;
        cursor: not-allowed;
        opacity: 0.7;
    }

    .stButton > button.unavailable:hover {
        transform: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(145deg, #dc3545, #c82333) !important;
        animation: none;
    }

    .stButton > button.unavailable::before {
        display: none;
    }

    /* Анимированный градиентный фон */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #1e1e1e, #2b2b2b, #1e1e1e, #2d2d2d);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }

    @keyframes gradientBG {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }

    /* Улучшенный заголовок */
    .header-container {
        text-align: center;
        padding: 3rem 1.5rem;
        margin-bottom: 2.5rem;
        background: rgba(43, 43, 43, 0.9);
        border-radius: 20px;
        backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 215, 0, 0.2);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInDown 1s ease-out;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .header-container:hover {
        border-color: rgba(255, 215, 0, 0.4);
        box-shadow: 0 15px 50px rgba(255, 215, 0, 0.2);
        transform: translateY(-8px);
    }
    
    .header-container h1 {
        font-size: 2.5rem;
        font-weight: 900;
        margin-bottom: 0.8rem;
        background: linear-gradient(120deg, 
            #ffd700 0%, 
            #ffc107 25%, 
            #ffab00 50%,
            #ffd700 75%,
            #ffc107 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.4);
        letter-spacing: 2px;
        line-height: 1.4;
        animation: shine 3s linear infinite;
    }
    
    @keyframes shine {
        to {
            background-position: 200% center;
        }
    }
    
    .subtitle {
        font-size: 1.4rem;
        margin: 1.2rem 0;
        letter-spacing: 3px;
        font-weight: 600;
        text-transform: uppercase;
        background: linear-gradient(120deg, 
            #ffffff 0%, 
            #e0e0e0 50%,
            #ffffff 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        opacity: 0.95;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        animation: shine 4s linear infinite, pulse 2s ease-in-out infinite;
    }
    
    .form-description {
        color: #e0e0e0;
        line-height: 1.8;
        font-size: 1.1rem;
        margin: 2rem 0 0;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
        opacity: 0.9;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    }

    @keyframes pulse {
        0% {
            transform: scale(1);
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        50% {
            transform: scale(1.05);
            text-shadow: 3px 3px 6px rgba(255, 215, 0, 0.4);
        }
        100% {
            transform: scale(1);
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
    }

    /* Улучшенные кнопки слотов */
    .stButton > button {
        width: 100%;
        padding: 12px;
        margin: 5px 0;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: center;
        color: #a9b7c6;
        background: rgba(43, 43, 43, 0.7);
        border: 1px solid rgba(255, 215, 0, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }

    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 15px rgba(255, 165, 0, 0.3);
        background: rgba(255, 165, 0, 0.15) !important;
        border-color: rgba(255, 165, 0, 0.4) !important;
        animation: pulseGlow 2s infinite;
    }

    @keyframes pulseGlow {
        0% {
            box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);
        }
        50% {
            box-shadow: 0 4px 25px rgba(255, 165, 0, 0.5);
        }
        100% {
            box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);
        }
    }

    /* Эффект свечения при наведении */
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 165, 0, 0.2),
            transparent
        );
        transition: 0.8s;
        transform: skewX(-15deg);
    }

    .stButton > button:hover::before {
        left: 100%;
        transition: 0.8s;
    }

    /* Улучшенные индикаторы статуса */
    .slot-status {
        display: flex;
        gap: 30px;
        margin: 20px 0;
        justify-content: center;
        padding: 15px;
        background: rgba(43, 43, 43, 0.8);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 215, 0, 0.1);
        transform: translateY(0);
        transition: all 0.3s ease;
    }

    .slot-status:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 215, 0, 0.2);
    }

    .status-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 16px;
        border-radius: 8px;
        background: rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }

    .status-item:hover {
        background: rgba(0, 0, 0, 0.3);
        transform: translateY(-1px);
    }

    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        transition: all 0.3s ease;
    }

    .status-dot.available {
        background: rgba(43, 43, 43, 0.7);
        border: 1px solid rgba(255, 215, 0, 0.1);
        animation: glowPulse 2s infinite;
    }

    @keyframes glowPulse {
        0% {
            box-shadow: 0 0 5px rgba(255, 215, 0, 0.3);
        }
        50% {
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
        }
        100% {
            box-shadow: 0 0 5px rgba(255, 215, 0, 0.3);
        }
    }

    /* Улучшенная форма бронирования */
    .booking-form {
        background: rgba(43, 43, 43, 0.8);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 215, 0, 0.1);
        backdrop-filter: blur(20px);
        transform: translateY(0);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: slideUp 0.5s ease-out;
    }

    .booking-form:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 215, 0, 0.2);
        box-shadow: 0 8px 32px rgba(255, 215, 0, 0.1);
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Улучшенные поля ввода */
    .stTextInput > div > div {
        background: rgba(43, 43, 43, 0.7) !important;
        border: 1px solid rgba(255, 215, 0, 0.1) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput > div > div:hover,
    .stTextInput > div > div:focus-within {
        border-color: rgba(255, 215, 0, 0.3) !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.1) !important;
    }

    /* Улучшенные уведомления */
    .stAlert {
        background: rgba(43, 43, 43, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 215, 0, 0.1) !important;
        animation: slideIn 0.5s ease-out !important;
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    /* Медиа-запросы для мобильных устройств */
    @media screen and (max-width: 768px) {
        .header-container {
            padding: 2rem 0.8rem;
            margin-bottom: 2rem;
            border-radius: 16px;
        }
        
        .header-container h1 {
            font-size: 1.8rem;
            letter-spacing: 1px;
            margin-bottom: 1rem;
            line-height: 1.3;
            padding: 0 0.3rem;
        }

        .mobile-break {
            display: block;
        }
        
        .subtitle {
            font-size: 1.2rem;
            letter-spacing: 1.5px;
            margin: 1rem 0;
            line-height: 1.6;
            padding: 0 0.5rem;
            word-spacing: 2px;
        }
        
        .form-description {
            font-size: 0.9rem;
            line-height: 1.5;
            margin: 1.5rem 0 0;
            padding: 0 0.8rem;
        }
    }

    /* Медиа-запросы для маленьких мобильных устройств */
    @media screen and (max-width: 480px) {
        .header-container {
            padding: 1.5rem 0.6rem;
            margin-bottom: 1.5rem;
        }
        
        .header-container h1 {
            font-size: 1.6rem;
            letter-spacing: 0.5px;
            padding: 0 0.2rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
            letter-spacing: 1px;
            padding: 0 0.3rem;
            word-spacing: 1px;
        }
        
        .form-description {
            font-size: 0.85rem;
            line-height: 1.4;
            margin: 1.2rem 0 0;
            padding: 0 0.5rem;
        }
    }

    /* Для очень маленьких экранов */
    @media screen and (max-width: 360px) {
        .header-container h1 {
            font-size: 1.4rem;
            letter-spacing: 0px;
            padding: 0 0.2rem;
        }
        
        .subtitle {
            font-size: 1rem;
            letter-spacing: 0.5px;
            word-spacing: 1px;
        }
    }

    /* Для десктопов */
    @media screen and (min-width: 769px) {
        .mobile-break {
            display: none;
        }
        
        .header-container h1 {
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
        }
        
        .subtitle {
            font-size: 1.6rem;
            letter-spacing: 2px;
            word-spacing: 4px;
            margin: 1.5rem 0;
        }
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

# Удаляем отладочную информацию
# st.write(f"Email отправителя: {GMAIL_SENDER}")
# st.write(f"Длина пароля приложения: {len(GMAIL_APP_PASSWORD)}")

# Словарь для перевода названий дней недели
WEEKDAYS = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье",
}


def get_week_dates():
    """Возвращает список дат на неделю вперед"""
    today = datetime.now()
    week_dates = []
    for i in range(7):
        date = today + timedelta(days=i)
        # Получаем название дня недели на русском
        weekday_name = WEEKDAYS[date.strftime("%A")]
        week_dates.append(
            {"date": date, "formatted": f"{weekday_name}, {date.strftime('%d.%m')}"}
        )
    return week_dates


def get_calendar_service():
    """Получает сервис Google Calendar с автоматическим обновлением токена"""
    try:
        # Проверяем наличие необходимых секретов
        required_secrets = [
            "google_client_id",
            "google_client_secret",
            "google_refresh_token",
            "token_uri",
        ]

        if not all(key in st.secrets for key in required_secrets):
            st.error("❌ Отсутствуют необходимые учетные данные OAuth")
            return None

        # Создаем объект Credentials с refresh token
        creds = Credentials(
            None,  # access token изначально None
            refresh_token=st.secrets["google_refresh_token"],
            token_uri=st.secrets["token_uri"],
            client_id=st.secrets["google_client_id"],
            client_secret=st.secrets["google_client_secret"],
            scopes=["https://www.googleapis.com/auth/calendar"],
        )

        # При первом использовании creds автоматически запросит новый access token
        # используя refresh token
        service = build("calendar", "v3", credentials=creds)
        return service

    except Exception as e:
        st.error(f"❌ Ошибка при создании сервиса: {str(e)}")
        return None


def get_credentials():
    """Получает учетные данные для доступа к Google Calendar API."""
    try:
        # Проверяем наличие учетных данных в секретах
        if all(
            key in st.secrets
            for key in [
                "google_client_id",
                "google_client_secret",
                "google_refresh_token",
            ]
        ):
            return Credentials(
                None,  # Токен будет получен при первом запросе
                refresh_token=st.secrets["google_refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=st.secrets["google_client_id"],
                client_secret=st.secrets["google_client_secret"],
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
        else:
            st.error(
                "Не найдены учетные данные OAuth. Пожалуйста, проверьте настройки."
            )
            return None
    except Exception as e:
        st.error(f"Ошибка при получении учетных данных: {str(e)}")
        return None


def get_available_slots(date_obj):
    """Получает список доступных слотов на указанную дату"""
    try:
        service = get_calendar_service()
        if not service:
            return []

        # Получаем начало и конец дня
        start_time = datetime.combine(date_obj, datetime.min.time())
        end_time = datetime.combine(date_obj, datetime.max.time())

        # Получаем события из календаря
        events_result = (
            service.events()
            .list(
                calendarId=st.secrets["calendar_id"],
                timeMin=start_time.isoformat() + "Z",
                timeMax=end_time.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        # Создаем список всех возможных слотов
        all_slots = []
        current_time = datetime.combine(date_obj, datetime.min.time())
        while current_time < end_time:
            if current_time.hour >= 9 and current_time.hour < 18:  # Рабочие часы
                all_slots.append(current_time)
            current_time += timedelta(minutes=30)

        # Отмечаем занятые слоты
        busy_slots = set()
        for event in events:
            event_start = datetime.fromisoformat(
                event["start"]["dateTime"].replace("Z", "+00:00")
            )
            event_end = datetime.fromisoformat(
                event["end"]["dateTime"].replace("Z", "+00:00")
            )

            current = event_start
            while current < event_end:
                busy_slots.add(current)
                current += timedelta(minutes=30)

        # Формируем список доступных слотов
        available_slots = []
        for slot in all_slots:
            if slot not in busy_slots:
                # Получаем название дня недели на русском
                weekday = WEEKDAYS[slot.strftime("%A")]
                available_slots.append(
                    {
                        "time": slot,
                        "formatted": f"{weekday}, {slot.strftime('%d.%m')} {slot.strftime('%H:%M')}",
                    }
                )

        return available_slots

    except Exception as e:
        st.error(f"❌ Ошибка при получении слотов: {str(e)}")
        return []


def send_email_notification(slot_time, booker_email):
    """Отправка уведомления на email"""
    try:
        # Проверяем наличие настроек
        if not GMAIL_SENDER:
            error_msg = log_email_operation(
                "Не указан email отправителя в настройках", "error"
            )
            st.session_state.messages.append(("error", error_msg))
            st.error(error_msg)
            return False

        if not GMAIL_APP_PASSWORD:
            error_msg = log_email_operation(
                "Не указан пароль приложения Gmail в настройках", "error"
            )
            st.session_state.messages.append(("error", error_msg))
            st.error(error_msg)
            return False

        info_msg = log_email_operation(
            f"Подготовка к отправке email на адрес: {booker_email}"
        )
        st.session_state.messages.append(("info", info_msg))
        st.info(info_msg)

        # Создаем основное сообщение
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_SENDER
        msg["To"] = booker_email
        msg["Subject"] = "🎉 Встреча успешно забронирована!"

        log_email_operation(f"Создано сообщение с темой: {msg['Subject']}")

        # HTML версия письма
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <h2 style="color: #1e88e5; margin-bottom: 20px;">Подтверждение бронирования</h2>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #333; margin-top: 0;">Детали встречи:</h3>
                    <p><strong>📅 Дата и время:</strong> {slot_time}</p>
                    <p><strong>⏱️ Продолжительность:</strong> 1 час</p>
                    <p><strong>👥 Участники:</strong> {booker_email}</p>
                </div>
                
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="color: #1e88e5; margin-top: 0;">Что дальше?</h4>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Вы получите приглашение в Google Calendar</li>
                        <li>В приглашении будет ссылка на Google Meet</li>
                        <li>За час до встречи придет напоминание</li>
                        <li>За 10 минут появится уведомление</li>
                    </ul>
                </div>
                
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px;">
                    <p style="margin: 0;"><strong>Нужно перенести встречу?</strong><br>
                    Вы можете предложить другое время через Google Calendar.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Текстовая версия
        text_body = f"""
        🎉 Встреча успешно забронирована!

        📅 Дата и время: {slot_time}
        ⏱️ Продолжительность: 1 час
        👥 Участники: {booker_email}

        Что дальше?
        - Вы получите приглашение в Google Calendar
        - В приглашении будет ссылка на Google Meet
        - За час до встречи придет напоминание
        - За 10 минут появится уведомление

        Нужно перенести встречу?
        Вы можете предложить другое время через Google Calendar.
        """

        # Добавляем обе версии в письмо
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        st.info("Подключение к серверу Gmail...")

        # Отправляем письмо
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                log_email_operation("Установлено SSL-соединение с smtp.gmail.com")

                try:
                    log_email_operation(f"Попытка входа с email: {GMAIL_SENDER}")
                    server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
                    log_email_operation("Успешная авторизация на сервере Gmail")

                    # Отправляем копию организатору
                    log_email_operation("Отправка копии организатору...")
                    # Создаем новое сообщение для организатора
                    msg_copy = MIMEMultipart("alternative")
                    msg_copy["From"] = GMAIL_SENDER
                    msg_copy["To"] = GMAIL_SENDER
                    msg_copy["Subject"] = f"📋 Новая встреча: {booker_email}"
                    msg_copy.attach(MIMEText(text_body, "plain"))
                    msg_copy.attach(MIMEText(html_body, "html"))
                    server.send_message(msg_copy)
                    log_email_operation("Копия организатору отправлена успешно")

                    # Отправляем основное письмо участнику
                    log_email_operation(
                        f"Отправка письма участнику ({booker_email})..."
                    )
                    server.send_message(msg)
                    log_email_operation("Письмо участнику отправлено успешно")

                    success_msg = log_email_operation(
                        "✅ Все уведомления успешно отправлены!"
                    )
                    st.success(success_msg)
                    return True

                except smtplib.SMTPAuthenticationError as auth_error:
                    error_msg = log_email_operation(
                        f"Ошибка аутентификации Gmail: {str(auth_error)}", "error"
                    )
                    st.error(error_msg)
                    return False

        except smtplib.SMTPException as smtp_error:
            error_msg = log_email_operation(
                f"Ошибка SMTP при отправке: {str(smtp_error)}", "error"
            )
            st.error(error_msg)
            return False

    except Exception as e:
        error_msg = log_email_operation(
            f"Общая ошибка при отправке email: {str(e)}", "error"
        )
        st.error(error_msg)
        return False


def create_calendar_event(slot_time, booker_email):
    """Создание события в календаре"""
    service = get_calendar_service()

    # Убеждаемся, что используем московское время
    moscow_tz = pytz.timezone("Europe/Moscow")
    if slot_time.tzinfo != moscow_tz:
        slot_time = slot_time.astimezone(moscow_tz)

    event = {
        "summary": f"👥 Встреча с {booker_email}",
        "description": f"""
Детали встречи:

👤 Участник: {booker_email}
⏱️ Продолжительность: 1 час
📍 Место: Google Meet (ссылка будет сгенерирована автоматически)

Эта встреча была забронирована через систему планирования встреч.
Вы можете принять, отклонить или предложить другое время, используя опции выше.

Нужно связаться с участником? Ответьте на это приглашение или используйте email: {booker_email}
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

    # Инициализация состояния для сообщений
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Добавляем стили для сообщений
    st.markdown(
        """
        <style>
        /* Стили для контейнера сообщений */
        .messages-container {
            position: fixed;
            top: 20px;
            right: 20px;
            width: 300px;
            z-index: 9999;
            background: rgba(43, 43, 43, 0.95);
            border-radius: 8px;
            border: 1px solid rgba(255, 215, 0, 0.2);
            backdrop-filter: blur(10px);
            padding: 10px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .message {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 6px;
            font-size: 0.9rem;
            animation: fadeIn 0.3s ease;
        }

        .message.info {
            background: rgba(13, 110, 253, 0.2);
            border: 1px solid rgba(13, 110, 253, 0.3);
            color: #8bb9fe;
        }

        .message.success {
            background: rgba(25, 135, 84, 0.2);
            border: 1px solid rgba(25, 135, 84, 0.3);
            color: #75b798;
        }

        .message.error {
            background: rgba(220, 53, 69, 0.2);
            border: 1px solid rgba(220, 53, 69, 0.3);
            color: #ea868f;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Увеличиваем время отображения стандартных уведомлений */
        div[data-testid="stNotificationContent"] {
            animation: none !important;
            transition: opacity 0.5s ease !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Отображаем контейнер с сообщениями
    if st.session_state.messages:
        messages_html = '<div class="messages-container">'
        for msg_type, msg_text in st.session_state.messages:
            messages_html += f'<div class="message {msg_type}">{msg_text}</div>'
        messages_html += "</div>"
        st.markdown(messages_html, unsafe_allow_html=True)

    # Настраиваем стили
    st.markdown(
        """
        <style>
        /* Общие стили */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #1e1e1e 0%, #2b2b2b 100%);
            color: #e0e0e0;
            padding: 0 !important;
        }
        
        [data-testid="stVerticalBlock"] {
            padding: 0 !important;
            gap: 0 !important;
        }
        
        /* Заголовок */
        .header-container {
            text-align: center;
            padding: 2.5rem 1rem;
            margin-bottom: 2rem;
            background: rgba(43, 43, 43, 0.8);
            border-radius: 16px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 215, 0, 0.15);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            transition: all 0.4s ease;
        }
        
        .header-container:hover {
            border-color: rgba(255, 215, 0, 0.3);
            box-shadow: 0 12px 40px rgba(255, 215, 0, 0.15);
            transform: translateY(-5px);
        }
        
        .header-container h1 {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(120deg, #ffd700 0%, #ffc107 50%, #ffab00 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            letter-spacing: 1px;
            line-height: 1.3;
        }
        
        .subtitle {
            font-size: 1.3rem;
            color: #e0e0e0;
            margin: 1rem 0;
            letter-spacing: 2px;
            font-weight: 500;
            text-transform: uppercase;
            background: linear-gradient(120deg, #ffffff 0%, #e0e0e0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            opacity: 0.9;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        .form-description {
            color: #d4d4d4;
            line-height: 1.6;
            font-size: 1rem;
            margin: 1.5rem 0 0;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Статус слотов */
        .slot-status {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: rgba(43, 43, 43, 0.7);
            border-radius: 8px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 215, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        /* Чекбокс для отображения дополнительных дней */
        .show-more-days {
            background: rgba(43, 43, 43, 0.7);
            border-radius: 8px;
            padding: 0.5rem;
            margin: 0.5rem 0;
            border: 1px solid rgba(255, 215, 0, 0.1);
            transition: all 0.3s ease;
            text-align: center;
        }
        
        /* Заголовок даты */
        .date-header {
            background: rgba(43, 43, 43, 0.7);
            border-radius: 8px;
            padding: 0.5rem;
            margin: 0.5rem 0;
            border: 1px solid rgba(255, 215, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .date-header h3 {
            color: #ffd700;
            font-size: 1rem;
            font-weight: 600;
            margin: 0;
        }
        
        /* Кнопки слотов */
        .stButton button {
            width: 100%;
            padding: 0.5rem;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            background: rgba(255, 215, 0, 0.1);
            color: #ffd700;
            border: 1px solid rgba(255, 215, 0, 0.2);
            margin: 0 !important;
        }
        
        /* Форма бронирования */
        .booking-form {
            background: rgba(43, 43, 43, 0.7);
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid rgba(255, 215, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .form-header {
            font-size: 1.2rem;
            font-weight: 600;
            color: #ffd700;
            margin-bottom: 0.5rem;
        }
        
        /* Стилизация колонок Streamlit */
        [data-testid="stHorizontalBlock"] {
            gap: 0.25rem !important;
            padding: 0 !important;
        }
        
        /* Убираем отступы у элементов формы */
        .stTextInput {
            margin: 0 !important;
        }
        
        .stTextInput > div {
            margin: 0 !important;
        }
        
        .stForm > div {
            margin-bottom: 0 !important;
        }
        
        .stForm [data-testid="stFormSubmitButton"] {
            margin: 0 !important;
        }
        
        /* Убираем отступы у чекбокса */
        .stCheckbox {
            margin: 0 !important;
        }
        
        .stCheckbox > div {
            margin: 0 !important;
        }
        
        /* Убираем отступы у алертов */
        .stAlert {
            margin: 0.5rem 0 !important;
            padding: 0.5rem !important;
        }
        
        /* Убираем отступы у markdown */
        .stMarkdown {
            margin: 0 !important;
        }
        
        .stMarkdown > div {
            margin: 0 !important;
        }
        
        /* Календарь */
        .calendar-container {
            padding: 0.5rem;
            margin: 0;
            background: rgba(43, 43, 43, 0.7);
            border-radius: 8px;
            border: 1px solid rgba(255, 215, 0, 0.1);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Добавляем заголовок
    st.markdown(
        """
        <div class="header-container">
            <h1>СВОБОДНЫЕ СЛОТЫ</h1>
            <div class="subtitle">БРАТКОВСКИЙ<br class="mobile-break"> ЕВГЕНИЙ<br class="mobile-break"> ВИКТОРОВИЧ</div>
            <div class="form-description">
                Выберите удобное время для встречи. Продолжительность встречи - 1 час.<br>
                Рабочие часы: с 9:00 до 18:00 (последняя встреча в 17:00)<br>
                После выбора времени вам нужно будет ввести email для получения подтверждения.
            </div>
        </div>

        <!-- Скрипт для автоматического обновления страницы -->
        <script>
            function getMillisecondsUntilMidnight() {
                const now = new Date();
                const midnight = new Date(now);
                midnight.setHours(24, 0, 0, 0);
                return midnight - now;
            }

            function scheduleRefresh() {
                const msUntilMidnight = getMillisecondsUntilMidnight();
                setTimeout(function() {
                    // Обновляем страницу
                    window.location.reload();
                    // После обновления снова планируем следующее обновление
                    scheduleRefresh();
                }, msUntilMidnight);
            }

            // Запускаем планировщик обновлений
            scheduleRefresh();

            // Добавляем индикатор следующего обновления
            function updateNextRefreshTime() {
                const msUntilMidnight = getMillisecondsUntilMidnight();
                const hoursLeft = Math.floor(msUntilMidnight / (1000 * 60 * 60));
                const minutesLeft = Math.floor((msUntilMidnight % (1000 * 60 * 60)) / (1000 * 60));
                
                const refreshInfo = document.getElementById('next-refresh-info');
                if (refreshInfo) {
                    refreshInfo.textContent = `Следующее обновление через: ${hoursLeft}ч ${minutesLeft}м`;
                }
                
                // Обновляем каждую минуту
                setTimeout(updateNextRefreshTime, 60000);
            }

            // Создаем элемент для отображения времени до следующего обновления
            document.addEventListener('DOMContentLoaded', function() {
                const refreshInfo = document.createElement('div');
                refreshInfo.id = 'next-refresh-info';
                refreshInfo.className = 'refresh-info';
                document.querySelector('.header-container').appendChild(refreshInfo);
                updateNextRefreshTime();
            });
        </script>

        <style>
        /* Добавляем стили для индикатора обновления */
        .refresh-info {
            font-size: 0.9rem;
            color: #888;
            margin-top: 1rem;
            text-align: center;
            font-style: italic;
            opacity: 0.8;
            transition: opacity 0.3s ease;
        }

        .refresh-info:hover {
            opacity: 1;
        }

        @media screen and (max-width: 768px) {
            .refresh-info {
                font-size: 0.8rem;
                margin-top: 0.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Добавляем легенду статусов
    st.markdown(
        """
        <div class="slot-status">
            <div class="status-item">
                <div class="status-dot available"></div>
                Доступно
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
        slots_info = get_available_slots(datetime.now())
    except Exception as e:
        st.error(f"Ошибка при получении слотов: {str(e)}")
        return

    if not slots_info:
        st.warning("⚠️ Нет доступных слотов на ближайшие 2 недели")
        return

    # Группировка слотов по дням
    slots_by_day = {}
    for slot, info in slots_info:
        day = info["date"].strftime("%Y-%m-%d")
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
                        f'<button class="unavailable" disabled>{info["formatted"]}</button>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(
                        info["formatted"],
                        key=f"slot_{slot.isoformat()}",
                        use_container_width=True,
                        type="secondary",
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
            <div class="form-header">📝 Бронирование встречи</div>
            <div class="form-description">
            <b>Выбранное время:</b> {selected_time}<br>
            <b>Продолжительность:</b> 1 час<br><br>
            Для подтверждения бронирования, пожалуйста, введите ваш email-адрес.<br>
            Вы получите:
            <ul>
                <li>Подтверждение бронирования</li>
                <li>Ссылку на встречу</li>
                <li>Напоминание за 1 час до встречи</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("booking_form"):
            booker_email = st.text_input(
                "📧 Ваш email адрес",
                help="На этот адрес вы получите подтверждение бронирования и детали встречи",
                placeholder="zhenyabratkovski5@gmail.com",
            )
            submitted = st.form_submit_button("✅ Подтвердить бронирование")

            if submitted:
                if not booker_email:
                    st.session_state.messages.append(
                        ("error", "Пожалуйста, введите ваш email адрес")
                    )
                    st.error("Please enter your email address")
                else:
                    if create_calendar_event(
                        st.session_state.selected_slot, booker_email
                    ):
                        if send_email_notification(
                            st.session_state.selected_slot.strftime("%d/%m/%Y %H:%M"),
                            booker_email,
                        ):
                            st.session_state.messages.append(
                                (
                                    "success",
                                    "🎉 Встреча успешно забронирована! Проверьте вашу почту.",
                                )
                            )
                            st.success(
                                "🎉 Meeting successfully booked! Check your email for details."
                            )
                        st.session_state.show_booking_form = False
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
