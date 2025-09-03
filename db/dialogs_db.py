import aiosqlite
import datetime
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
db_path='dialogs.db'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # на уровень выше папки db
CREDS_PATH = os.path.join(BASE_DIR, "docs", "anamnez-bot-fd6467c32f62.json")

async def init_db():
        async with aiosqlite.connect(db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS patient_dialogs (
                    telegram_id INTEGER PRIMARY KEY,
                    dialog_text TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_data (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    is_medosomotr TEXT,
                    phone TEXT,
                    register_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    privacy_policy TEXT,
                    privacy_policy_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    get_dop_tests TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_anketa (
                    user_id INTEGER PRIMARY KEY,
                    organization_or_inn TEXT,
                    osmotr_date DATETIME,
                    age INTEGER,
                    weight REAL,
                    height REAL,
                    smoking TEXT,
                    alcohol TEXT,
                    physical_activity TEXT,
                    hypertension TEXT,
                    sugar TEXT,
                    chronic_diseases TEXT,
                    FOREIGN KEY(user_id) REFERENCES user_data(user_id)
                )
            """)

            await db.execute("""
                        CREATE TABLE IF NOT EXISTS message_links (
                            group_message_id INTEGER PRIMARY KEY,
                            user_id INTEGER NOT NULL
                        )
                    """)

            await db.execute("""
                        CREATE TABLE IF NOT EXISTS user_reply_state (
                            user_id INTEGER PRIMARY KEY,
                            manager_message_id INTEGER
                        )
                    """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS dialog_states (
                    user_id INTEGER PRIMARY KEY,
                    dialog_state TEXT NOT NULL
                )
            """)

            await db.commit()
        await sync_from_google_sheets()


# ==== Настройки Google API ====
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_NAME = "anamnez_db"  # Имя файла в Google Sheets


# ==== Подключение к Google Sheets ====
def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME)
    return {
        "patient_dialogs": sheet.worksheet("patient_dialogs"),
        "user_data": sheet.worksheet("user_data"),
        "user_anketa": sheet.worksheet("user_anketa"),
        "message_links": sheet.worksheet("message_links"),
        "user_reply_state": sheet.worksheet("user_reply_state"),
        "dialog_states": sheet.worksheet("dialog_states"),
    }

# ==== Загрузка данных из Google Sheets в SQLite ====
async def sync_from_google_sheets():
    sheets = get_sheet()
    async with aiosqlite.connect(db_path) as db:
        # Очистка таблиц
        await db.execute("DELETE FROM patient_dialogs")
        await db.execute("DELETE FROM user_data")
        await db.execute("DELETE FROM user_anketa")
        await db.execute("DELETE FROM message_links")
        await db.execute("DELETE FROM user_reply_state")
        await db.execute("DELETE FROM dialog_states")

        # patient_dialogs
        rows = sheets["patient_dialogs"].get_all_values()[1:]
        for r in rows:
            telegram_id, dialog_text, updated_at = r
            await db.execute(
                "INSERT INTO patient_dialogs (telegram_id, dialog_text, updated_at) VALUES (?, ?, ?)",
                (int(telegram_id), dialog_text, updated_at)
            )

        # user_data
        rows = sheets["user_data"].get_all_values()[1:]
        for r in rows:
            user_id, name, is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date, get_dop_tests = r
            await db.execute(
                "INSERT INTO user_data (user_id, name, is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (int(user_id), name, is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date, get_dop_tests)
            )

        # user_anketa
        rows = sheets["user_anketa"].get_all_values()[1:]
        for r in rows:
            user_id, organization_or_inn, osmotr_date, age, weight, height, smoking, alcohol, physical_activity, hypertension, sugar, chronic_diseases = r
            await db.execute(
                """INSERT INTO user_anketa (
                    user_id, organization_or_inn, osmotr_date, age, weight, height,
                    smoking, alcohol, physical_activity, hypertension, sugar, chronic_diseases
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (int(user_id), organization_or_inn, osmotr_date,
                 int(age) if age else None,
                 float(weight) if weight else None,
                 float(height) if height else None,
                 smoking, alcohol, physical_activity, hypertension, sugar, chronic_diseases)
            )

        # message_links
        rows = sheets["message_links"].get_all_values()[1:]
        for r in rows:
            group_message_id, user_id = r
            await db.execute(
                "INSERT INTO message_links (group_message_id, user_id) VALUES (?, ?)",
                (int(group_message_id), int(user_id))
            )

        # user_reply_state
        rows = sheets["user_reply_state"].get_all_values()[1:]
        for r in rows:
            user_id, manager_message_id = r
            await db.execute(
                "INSERT INTO user_reply_state (user_id, manager_message_id) VALUES (?, ?)",
                (int(user_id), int(manager_message_id) if manager_message_id else None)
            )

        # dialog_states
        rows = sheets["dialog_states"].get_all_values()[1:]
        for r in rows:
            user_id, dialog_state = r
            await db.execute(
                "INSERT INTO dialog_states (user_id, dialog_state) VALUES (?, ?)",
                (int(user_id), dialog_state)
            )

        await db.commit()
        print("[✅] Данные из Google Sheets загружены в SQLite")

# ==== Выгрузка данных из SQLite в Google Sheets ====
async def sync_to_google_sheets():
    sheets = get_sheet()
    async with aiosqlite.connect(db_path) as db:

        # patient_dialogs
        async with db.execute("SELECT telegram_id, dialog_text, updated_at FROM patient_dialogs") as cur:
            rows = await cur.fetchall()
        sheets["patient_dialogs"].clear()
        sheets["patient_dialogs"].update("A1", [["telegram_id", "dialog_text", "updated_at"]] + rows)

        # user_data
        async with db.execute("SELECT user_id, name, is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date FROM user_data, get_dop_tests") as cur:
            rows = await cur.fetchall()
        sheets["user_data"].clear()
        sheets["user_data"].update("A1", [["user_id", "name", "is_medosomotr", "phone", "register_date", "privacy_policy", "privacy_policy_date, get_dop_tests"]] + rows)

        # user_anketa
        async with db.execute("""SELECT user_id, organization_or_inn, osmotr_date, age, weight, height, smoking, alcohol, physical_activity, hypertension, sugar, chronic_diseases FROM user_anketa""") as cur:
            rows = await cur.fetchall()
        sheets["user_anketa"].clear()
        sheets["user_anketa"].update("A1", [["user_id", "organization_or_inn", "osmotr_date", "age", "weight", "height", "smoking", "alcohol", "physical_activity", "hypertension", "sugar", "chronic_diseases"]] + rows)

        # message_links
        async with db.execute("SELECT group_message_id, user_id FROM message_links") as cur:
            rows = await cur.fetchall()
        sheets["message_links"].clear()
        sheets["message_links"].update("A1", [["group_message_id", "user_id"]] + rows)

        # user_reply_state
        async with db.execute("SELECT user_id, manager_message_id FROM user_reply_state") as cur:
            rows = await cur.fetchall()
        sheets["user_reply_state"].clear()
        sheets["user_reply_state"].update("A1", [["user_id", "manager_message_id"]] + rows)

        # dialog_states
        async with db.execute("SELECT user_id, dialog_state FROM dialog_states") as cur:
            rows = await cur.fetchall()
        sheets["dialog_states"].clear()
        sheets["dialog_states"].update("A1", [["user_id", "dialog_state"]] + rows)

        print("[✅] Данные из SQLite выгружены в Google Sheets")

# ==== Периодическая синхронизация ====
async def periodic_sync(interval: int = 7200):
    while True:
        await asyncio.sleep(interval)
        try:
            await sync_to_google_sheets()
            print(f"Успешная синхронизация.")
        except Exception as e:
            print(f"Ошибка при синхронизации в Google Sheets: {e}")


#______ DIALOGS
async def append_answer(telegram_id: int, text: str):
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT dialog_text FROM patient_dialogs WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = await cursor.fetchone()

            # Собираем обновлённый текст
            new_entry = f"{text.strip()}\n"
            if row:
                dialog_text = row[0] + new_entry
            else:
                dialog_text = new_entry

            # Обновление или вставка
            await db.execute("""
                INSERT INTO patient_dialogs (telegram_id, dialog_text, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    dialog_text = excluded.dialog_text,
                    updated_at = excluded.updated_at
            """, (telegram_id, dialog_text, datetime.datetime.now(datetime.UTC)))
            await db.commit()

async def get_dialog( telegram_id: int) -> str:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT dialog_text FROM patient_dialogs WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else ""

async def delete_dialog( telegram_id: int):
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "DELETE FROM patient_dialogs WHERE telegram_id = ?",
                (telegram_id,)
            )
            await db.commit()
#______


#______ USERS
async def add_user(user_id: int, name: str, is_medosomotr:str = None, phone: str = None,
                   register_date = datetime.datetime.now(datetime.UTC),
                   privacy_policy:str = None, privacy_policy_date:datetime.datetime = None, get_dop_tests:str = None):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT OR REPLACE INTO user_data (user_id, name,is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date, get_dop_tests)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date, get_dop_tests ))
        await db.commit()

async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT user_id, name, is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date, get_dop_tests FROM user_data WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {
                "user_id": row[0],
                "name": row[1],
                "is_medosomotr": row[2],
                "phone": row[3],
                "register_date": row[4],
                "privacy_policy":row[5],
                "privacy_policy_date":row[6],
                "get_dop_tests":row[7]
            }
        return None

async def delete_user(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "DELETE FROM user_data WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def get_all_user_ids():
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT DISTINCT user_id FROM user_data") as cursor:
            return [row[0] async for row in cursor]
#______


#______ ANKETA
async def add_or_update_anketa(
    user_id: int,
    organization_or_inn: str = None,
    osmotr_date: datetime.datetime = None,
    age: int = None,
    weight: float = None,
    height: float = None,
    smoking: str = None,
    alcohol: str = None,
    physical_activity: str = None,
    hypertension: str = None,
    sugar: str = None,
    chronic_diseases: str = None
):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO user_anketa (
                user_id, organization_or_inn, osmotr_date, age, weight, height,
                smoking, alcohol, physical_activity,
                hypertension, sugar, chronic_diseases
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                organization_or_inn = excluded.organization_or_inn,
                osmotr_date = excluded.osmotr_date,
                age = excluded.age,
                weight = excluded.weight,
                height = excluded.height,
                smoking = excluded.smoking,
                alcohol = excluded.alcohol,
                physical_activity = excluded.physical_activity,
                hypertension = excluded.hypertension,
                sugar = excluded.sugar,
                chronic_diseases = excluded.chronic_diseases
        """, (
            user_id, organization_or_inn, osmotr_date, age, weight, height,
            smoking, alcohol, physical_activity,
            hypertension, sugar, chronic_diseases
        ))
        await db.commit()


async def update_anketa_fields(user_id: int, change_json: dict) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        # Получаем текущую анкету
        cursor = await db.execute("""
            SELECT * FROM user_anketa WHERE user_id = ?
        """, (user_id,))
        row = await cursor.fetchone()

        if not row:
            print(f"Анкета для user_id={user_id} не найдена.")
            return None

        columns = [
            "user_id", "organization_or_inn", "osmotr_date", "age", "weight", "height",
            "smoking", "alcohol", "physical_activity",
            "hypertension", "sugar", "chronic_diseases"
        ]
        anketa_dict = dict(zip(columns, row))

        # Применяем изменения с приведением типов
        for key, value in change_json.items():
            if key in anketa_dict:
                old_value = anketa_dict[key]
                if isinstance(old_value, int):
                    anketa_dict[key] = int(value)
                elif isinstance(old_value, float):
                    anketa_dict[key] = float(value)
                else:
                    anketa_dict[key] = value

        # Обновляем только изменённые поля
        update_fields = [f"{key} = ?" for key in change_json if key in anketa_dict]
        update_values = [anketa_dict[key] for key in change_json if key in anketa_dict]

        if update_fields:
            update_query = f"""
                UPDATE user_anketa
                SET {', '.join(update_fields)}
                WHERE user_id = ?
            """
            await db.execute(update_query, (*update_values, user_id))
            await db.commit()

        return anketa_dict

async def get_anketa(user_id: int) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("""
            SELECT * FROM user_anketa WHERE user_id = ?
        """, (user_id,))
        row = await cursor.fetchone()
        if row:
            columns = [
                "user_id", "organization_or_inn", "osmotr_date", "age", "weight", "height",
                "smoking", "alcohol", "physical_activity",
                "hypertension", "sugar", "chronic_diseases"
            ]
            return dict(zip(columns, row))
        return None

async def delete_anketa(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "DELETE FROM user_anketa WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

#______

#STATE
async def set_dialog_state(user_id: int, state: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO dialog_states (user_id, dialog_state)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET dialog_state=excluded.dialog_state
        """, (user_id, state))
        await db.commit()


async def get_dialog_state(user_id: int) -> str | None:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("""
            SELECT dialog_state FROM dialog_states WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def delete_dialog_state(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            DELETE FROM dialog_states WHERE user_id = ?
        """, (user_id,))
        await db.commit()

#______

async def save_message_link(group_msg_id: int, user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT OR REPLACE INTO message_links (group_message_id, user_id)
            VALUES (?, ?)
        """, (group_msg_id, user_id))
        await db.commit()

async def get_user_id_by_group_message(group_msg_id: int):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT user_id FROM message_links WHERE group_message_id = ?", (group_msg_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def save_user_reply_state(user_id: int, manager_msg_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT OR REPLACE INTO user_reply_state (user_id, manager_message_id)
            VALUES (?, ?)
        """, (user_id, manager_msg_id))
        await db.commit()

async def get_user_reply_state(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT manager_message_id FROM user_reply_state WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def delete_user_reply_state(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM user_reply_state WHERE user_id = ?", (user_id,))
        await db.commit()

