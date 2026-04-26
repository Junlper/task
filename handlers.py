from datetime import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import get_db
from keyboards import menu_keyboard, settings_keyboard

router = Router()


class CreateEnemy(StatesGroup):
    waiting_for_name = State()
    waiting_for_main_pic = State()
    waiting_for_task = State()


TEXTS = {
    'ru': {
        'registered': 'Вы зарегистрированы! Используйте /menu',
        'menu': 'Меню:',
        'enter_name': 'Введите имя противника:',
        'send_pic': 'Отправьте картинку противника:',
        'enter_task': 'Введите задачу на сегодня:',
        'enemy_created': 'Противник создан! Задача на сегодня добавлена.',
        'no_tasks': 'На сегодня задач нет.\nТекущий уровень: {level}',
        'progress': 'Уровень: {level}\nПрогресс: {percent}% (нужно {required}%)\nВыполнено: {done}/{total}',
        'choose_lang': 'Выберите язык:',
        'lang_changed': 'Язык изменён на русский',
    },
    'en': {
        'registered': 'You are registered! Use /menu',
        'menu': 'Menu:',
        'enter_name': 'Enter enemy name:',
        'send_pic': 'Send enemy picture:',
        'enter_task': 'Enter task for today:',
        'enemy_created': 'Enemy created! Task for today added.',
        'no_tasks': 'No tasks for today.\nCurrent level: {level}',
        'progress': 'Level: {level}\nProgress: {percent}% (need {required}%)\nDone: {done}/{total}',
        'choose_lang': 'Choose language:',
        'lang_changed': 'Language changed to English',
    }
}


async def get_lang(user_id):
    db = await get_db()
    row = await db.execute_fetchall(
        "SELECT language FROM users WHERE user_id=?", (user_id,)
    )
    await db.close()
    if row:
        return row[0][0]
    return 'ru'


def get_required_percentage(level):
    if level == 0:
        return 49
    elif level == 1:
        return 59
    elif level == 2:
        return 69
    elif level == 3:
        return 79
    elif level == 4:
        return 89
    else:
        return 100


@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.from_user is None:
        return

    user_id = message.from_user.id
    db = await get_db()

    result = await db.execute_fetchall(
        "SELECT user_id FROM users WHERE user_id=?", (user_id,)
    )

    if not result:
        await db.execute(
            "INSERT INTO users (user_id, level) VALUES (?,0)",
            (user_id,)
        )
        await db.commit()
        print(f"Создан новый пользователь: {user_id}")

    await db.close()

    lang = await get_lang(user_id)
    await message.answer(TEXTS[lang]['registered'])


@router.message(Command('menu'))
async def cmd_menu(message: Message):
    lang = await get_lang(message.from_user.id)
    await message.answer(TEXTS[lang]['menu'], reply_markup=menu_keyboard(lang))


@router.callback_query(F.data == "create_enemy")
async def start_create_enemy(callback: CallbackQuery, state: FSMContext):
    lang = await get_lang(callback.from_user.id)
    await callback.message.answer(TEXTS[lang]['enter_name'])
    await state.set_state(CreateEnemy.waiting_for_name)
    await callback.answer()


@router.message(CreateEnemy.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    await state.update_data(name=message.text)
    await message.answer(TEXTS[lang]['send_pic'])
    await state.set_state(CreateEnemy.waiting_for_main_pic)


@router.message(CreateEnemy.waiting_for_main_pic, F.photo)
async def process_main_pic(message: Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    file_id = message.photo[-1].file_id
    await state.update_data(main_pic=file_id)
    await message.answer(TEXTS[lang]['enter_task'])
    await state.set_state(CreateEnemy.waiting_for_task)


@router.message(CreateEnemy.waiting_for_task)
async def process_task(message: Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    data = await state.get_data()
    user_id = message.from_user.id
    today = datetime.now().weekday() + 1
    today_date = datetime.now().strftime("%Y-%m-%d")

    db = await get_db()

    await db.execute(
        "INSERT INTO enemies (user_id, name, main_pic, task_text, task_date, created_date) VALUES (?,?,?,?,?,?)",
        (user_id, data["name"], data["main_pic"], message.text, today, today_date)
    )

    await db.commit()
    await db.close()

    await message.answer(TEXTS[lang]['enemy_created'])
    await state.clear()


@router.callback_query(F.data == "progress")
async def show_progress(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_lang(user_id)
    today = datetime.now().weekday() + 1
    today_date = datetime.now().strftime("%Y-%m-%d")

    db = await get_db()

    user = await db.execute_fetchall(
        "SELECT level, last_check_date FROM users WHERE user_id=?", (user_id,)
    )

    if not user:
        await callback.answer()
        await db.close()
        return

    level = user[0][0]
    last_check = user[0][1]

    if last_check != today_date:
        enemies_yesterday = await db.execute_fetchall(
            "SELECT id FROM enemies WHERE user_id=? AND created_date=?",
            (user_id, last_check)
        )

        if enemies_yesterday:
            total = len(enemies_yesterday)
            done_count = 0

            for (enemy_id,) in enemies_yesterday:
                row = await db.execute_fetchall(
                    "SELECT done FROM enemies WHERE id=?", (enemy_id,)
                )
                if row and row[0][0]:
                    done_count += 1

            percent = int((done_count / total) * 100) if total > 0 else 0
            required = get_required_percentage(level)

            if percent >= required:
                new_level = level + 1
                if new_level > 5:
                    new_level = 5
            else:
                new_level = 0

            await db.execute(
                "UPDATE users SET level=?, last_check_date=? WHERE user_id=?",
                (new_level, today_date, user_id)
            )

            level = new_level
        else:
            await db.execute(
                "UPDATE users SET last_check_date=? WHERE user_id=?",
                (today_date, user_id)
            )

    enemies = await db.execute_fetchall(
        "SELECT id, name, task_text, done FROM enemies WHERE user_id=? AND task_date=?",
        (user_id, today)
    )

    if not enemies:
        await callback.message.answer(TEXTS[lang]['no_tasks'].format(level=level))
        await callback.answer()
        await db.close()
        return

    required = get_required_percentage(level)

    total = len(enemies)
    done_count = sum(1 for e in enemies if e[3])
    percent = int((done_count / total) * 100) if total > 0 else 0

    builder = InlineKeyboardBuilder()

    for enemy_id, name, task_text, done in enemies:
        if done:
            builder.button(
                text=f"[V] {name}",
                callback_data=f"undo_{enemy_id}"
            )
        else:
            builder.button(
                text=f"[ ] {name}",
                callback_data=f"do_{enemy_id}"
            )

    builder.adjust(1)

    await callback.message.answer(
        TEXTS[lang]['progress'].format(level=level, percent=percent, required=required, done=done_count, total=total),
        reply_markup=builder.as_markup()
    )
    await callback.answer()
    await db.close()


@router.callback_query(F.data.startswith("do_"))
async def mark_done(callback: CallbackQuery):
    enemy_id = int(callback.data.split("_")[1])

    db = await get_db()

    await db.execute(
        "UPDATE enemies SET done=1 WHERE id=?",
        (enemy_id,)
    )

    await db.commit()
    await db.close()

    await show_progress(callback)


@router.callback_query(F.data.startswith("undo_"))
async def mark_undone(callback: CallbackQuery):
    enemy_id = int(callback.data.split("_")[1])

    db = await get_db()

    await db.execute(
        "UPDATE enemies SET done=0 WHERE id=?",
        (enemy_id,)
    )

    await db.commit()
    await db.close()

    await show_progress(callback)


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    lang = await get_lang(callback.from_user.id)
    await callback.message.answer(TEXTS[lang]['choose_lang'], reply_markup=settings_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    new_lang = callback.data.split("_")[1]
    user_id = callback.from_user.id

    db = await get_db()
    await db.execute(
        "UPDATE users SET language=? WHERE user_id=?",
        (new_lang, user_id)
    )
    await db.commit()
    await db.close()

    await callback.message.answer(TEXTS[new_lang]['lang_changed'])
    await callback.answer()