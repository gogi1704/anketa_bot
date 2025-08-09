import aiosqlite
import datetime
db_path='dialogs.db'


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
                    privacy_policy_date DATETIME DEFAULT CURRENT_TIMESTAMP
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

            await db.commit()

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
                   privacy_policy:str = None, privacy_policy_date:datetime.datetime = None):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT OR REPLACE INTO user_data (user_id, name,is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date ))
        await db.commit()

async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT user_id, name, is_medosomotr, phone, register_date, privacy_policy, privacy_policy_date  FROM user_data WHERE user_id = ?",
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
                "privacy_policy_date":row[6]
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

