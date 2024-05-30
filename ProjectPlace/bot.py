# IMPORTS
import logging
from config import TOKEN, leader_client_id, leader_client_secret
import asyncio, asyncpg
import psycopg2
from datetime import date
from datetime import timedelta
import random
import re
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
import requests

# IMPORTS

####START####
conn=psycopg2.connect(
    dbname="ppbot",
    user="postgres",
    password="DaS3VLQZ@IOp",
    host="127.0.0.1",
    port="5432"

)

leader_client_id=leader_client_id
leader_client_secret=leader_client_secret

get_access_token_url='https://apps.leader-id.ru/api/v1/oauth/token'

back_button_state=0

current_date_for_events=date.today()
last_date_for_events=date.today() + timedelta(days=14)

get_hot_point_events_url=('https://apps.leader-id.ru/api/v1/events/search?paginationPage=1&paginationSize=15&sort'
                          f'=popularity&dateFrom={current_date_for_events}&dateTo={last_date_for_events}&formats=&onlyActual=1&placeIds[]=1034')
create_events_url='https://leader-id.ru/events/'

moderator_id=1700929284

logging.basicConfig(level=logging.INFO)
bot=Bot(token=TOKEN)
dp=Dispatcher()


class Tech_Support_User(StatesGroup):
    request=State()


class Tech_Support_Admin(StatesGroup):
    answer=State()
    mailing=State()
    menu=State()
    req_id=State()


class Menu_States(StatesGroup):
    experts_area_state=State()
    expert_menu_state=State()
    choose_expert_state=State()


#######KEYBOARDS###########
main_menu=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text='Эксперты'), KeyboardButton(text='Новости'), KeyboardButton(text='Видео-курс')],
    [KeyboardButton(text='Записаться на мероприятие'), KeyboardButton(text='Подать заявку на акселератор'),
     KeyboardButton(text='Техническая поддержка')],
    [KeyboardButton(text='Личный кабинет'), KeyboardButton(text='Тестирование')]
])

registration_area_interest=InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Рынок и маркетинг', callback_data='Market and marketing'),
     InlineKeyboardButton(text='Интеллектуальная собственность', callback_data='Intellectual property')],
    [InlineKeyboardButton(text='Юридические и бухгалтерские вопросы', callback_data='Legal issues'),
     InlineKeyboardButton(text='Технические вопросы по IT', callback_data='IT issues')],
    [InlineKeyboardButton(text='CustDev', callback_data='CustDev Expertise'),
     InlineKeyboardButton(text='Инвестиции', callback_data='Investment')],
    [InlineKeyboardButton(text='Экспертиза проектов по IT', callback_data='IT Expertise'),
     InlineKeyboardButton(text='Электроника и связь', callback_data='Electronics')]
])

experts_area=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text='Рынок и маркетинг'), KeyboardButton(text='Интеллектуальная собственность')],
    [KeyboardButton(text='Юридические и бухгалтерские вопросы'), KeyboardButton(text='Технические вопросы по IT')],
    [KeyboardButton(text='Экспертиза CustDev'), KeyboardButton(text='Инвестиции'),
     KeyboardButton(text='Электроника и связь')],
    [KeyboardButton(text='Меню')]
])

news_keyboard=InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Новости СБИ ТУСУР', callback_data='sbi_news')]
])

main_menu_inline=InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Меню', callback_data='menu_callback')]
])

admin_menu=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text='Посмотреть все запросы'), KeyboardButton(text='Сделать рассылку')],
    [KeyboardButton(text='Меню')]
])

market_keyboard=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Валерия Цибульникова'), KeyboardButton(text='Мария Брусянина')],
            [KeyboardButton(text='Виктор Горбачев'), KeyboardButton(text='Вера Пудкова')],
            [KeyboardButton(text='Назад')]
        ])
intellectual_property_keyboard=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text="Валентина Мельникова")], [KeyboardButton(text='Назад')]
        ])
legal_issues_keyboard=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Галина Волкова')], [KeyboardButton(text='Назад')]
        ])
technical_issues_keyboard=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Роман Кульшин'), KeyboardButton(text='Иван Тикшаев')],
            [KeyboardButton(text='Назад')]
        ])
cust_expertise_keyboard=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Глеб Садыков'), KeyboardButton(text='Василий Лихачев'),
             KeyboardButton(text='Александр Смирнов')], [KeyboardButton(text='Назад')]
        ])
investment_keyboard=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Глеб Садыков'), KeyboardButton(text='Василий Лихачев')],
            [KeyboardButton(text='Назад')]
        ])
electonics_keyboard=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Юрий Гриценко'), KeyboardButton(text='Андрей Ивлев')], [KeyboardButton(text='Назад')]
        ])
#######KEYBOARDS###########


def handle_messages(message, user_chat_id):
    buttons=types.ReplyKeyboardMarkup(resize_keyboard=True)
    items1=types.KeyboardButton('Удалить запрос')
    back=types.KeyboardButton('Меню')
    buttons.add(items1, back)
    message.answer(int(user_chat_id[0]), message.text, reply_markup=buttons)


def check_moder_status(user_id):
    cur=conn.cursor()
    cur.execute('SELECT status FROM admin_users WHERE user_id = %s', (user_id,))
    status=cur.fetchone()[0]
    cur.close()
    return status


####ОБРАБОТКА КОММАНД И ТЕКСТА####
@dp.message(CommandStart())
async def cmd_start(message: Message):
    global current_user_id
    current_user_id=message.from_user.id
    cur=conn.cursor()

    cur.execute('SELECT user_id FROM users WHERE user_id = %s',
                (message.from_user.id,))
    user_id=cur.fetchall()

    if len(user_id) == 0:
        cur.execute('INSERT INTO users (user_id, user_chat_id, user_name) VALUES (%s, %s, %s)',
                    (message.from_user.id, message.chat.id, message.from_user.first_name))
        await message.answer(
            f'Приветик, {message.from_user.first_name}! Это чат-бот для акселерации, выбери интересующие тебя области, для дальнейшей работы с ботом:)',
            reply_markup=registration_area_interest)
    else:
        cur.execute('SELECT user_interest FROM users WHERE user_id=%s', (message.from_user.id,))
        user_interest=str(cur.fetchone()[0])
        cur.execute('SELECT urls FROM useful_information_urls WHERE interest_area=%s', (user_interest,))
        useful_information_list=cur.fetchall()
        rand_num=random.randint(0, (len(useful_information_list) - 1))
        useful_information=""
        useful_information+=str(useful_information_list[rand_num])
        useful_information=re.sub(r'[(),\']', '', useful_information)
        await message.answer(
            f'Привет, {message.from_user.first_name}!\nЭто может быть интересно: {useful_information}',
            reply_markup=main_menu)
        await message.answer(f'Если недостаточно информации, то можно получить весь список по кнопке ниже', reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Получить все ссылки', callback_data='get_all_info_urls')]
        ]))
    conn.commit()
    cur.close()


@dp.message(Command('news'))
async def news(message: Message):
    await message.answer('https://sbi.tusur.ru/#news')


@dp.message(Command('site', 'website'))
async def site(message: Message):
    await message.answer('https://sbi.tusur.ru')


@dp.message(Command('study'))
async def study(message: Message):
    await send_video_menu(message)


@dp.message(F.text == 'Видео-курс')
async def study(message: Message):
    await send_video_menu(message)

@dp.message(F.text == "акселерация" or F.text == "аксель")
async def akseleration(message: Message):
    await message.answer("Акселератор - это программа по развитию предпринимательских талантов среди молодежи")


@dp.message(F.text == "как подать заявку" or F.text == "Как подать заявку")
async def application_aksel(message: Message):
    await message.answer("Для того, чтобы подать заявку на акселерационную программу нужно собрать команду и"
                         "придумать идею для проекта. Подать можно здесь: ("
                         "https://startup-poligon.ru/accelerator)")


@dp.message(F.text == "Эксперты")
async def experts_menu(message: Message):
    await message.answer('Эксперты', reply_markup=experts_area)


@dp.message(F.text == "Личный кабинет")
async def personal_account(message: Message):
    buttons=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Изменить сферу интересов', callback_data='change_interest_area')]
    ])
    cur=conn.cursor()
    user_id=message.from_user.id
    cur.execute('SELECT user_name, user_interest FROM users WHERE user_id = %s',
                (user_id,))
    rows=cur.fetchall()
    for row in rows:
        user_name, user_interest=row
    await message.answer(f'<b>Данные профиля</b>'
                         f'\nИмя: {user_name}'
                         f'\nОбласть интересов: {user_interest}', parse_mode=ParseMode.HTML, reply_markup=buttons)


@dp.message(F.text == "Меню")
async def go_to_main_menu(message: Message):
    await message.answer("Меню", reply_markup=main_menu)


@dp.message(F.text == "Назад")
async def back_button(message: Message):
    global back_button_state
    if back_button_state == 'choose_expert_state':
        back_button_state = 'expert_area_state'
        await message.answer('Назад', reply_markup=experts_area)
    elif back_button_state == 'market_experts_menu_state':
        back_button_state = 'choose_expert_state'
        await message.answer('Назад', reply_markup=market_keyboard)
    elif back_button_state == 'intellectual_experts_menu_state':
        back_button_state = 'choose_expert_state'
        await message.answer("Назад", reply_markup=intellectual_property_keyboard)
    elif back_button_state == 'legal_experts_menu_state':
        back_button_state = 'choose_expert_state'
        await message.answer('Назад', reply_markup=legal_issues_keyboard)
    elif back_button_state == 'tech_issues_experts_menu_state':
        back_button_state = 'choose_expert_state'
        await message.answer('Назад', reply_markup=technical_issues_keyboard)
    elif back_button_state == 'custdev_experts_menu_state':
        back_button_state = 'choose_expert_state'
        await message.answer("Назад", reply_markup=cust_expertise_keyboard)
    elif back_button_state == 'investment_experts_menu_state':
        back_button_state = 'choose_expert_state'
        await message.answer("Назад", reply_markup=investment_keyboard)
    elif back_button_state == 'electeonics_experts_menu_state':
        back_button_state = 'choose_expert_state'
        await message.answer("Назад", reply_markup =electonics_keyboard)
@dp.message(F.text == "Новости")
async def new_button(message: Message):
    await message.answer("Новости", reply_markup=news_keyboard)


@dp.message(Command('expert', 'expertlist', 'experts'))
async def expert_areas(message: Message):
    await message.answer('Эксперты', reply_markup=experts_area)


@dp.message(F.text == "Удалить запрос")
async def delete_request(message: Message):
    cur=conn.cursor()
    delete_row_id=message.from_user.id
    try:
        cur.execute("DELETE FROM req_queue WHERE user_id = %s", (delete_row_id,))
        conn.commit()
        await message.answer(f"Запрос удален")
    except Exception as e:
        await message.answer("Запрос не удален, попробуйте позже")


@dp.message(F.text == "Техническая поддержка")
async def technical_support(message: Message, state: FSMContext):
    await state.set_state(Tech_Support_User.request)
    await message.answer('Напишите ваш вопрос', reply_markup=main_menu_inline)


@dp.message(Tech_Support_User.request)
async def technical_support_request(message: Message, state: FSMContext):
    await state.update_data(request=message.text)
    data=await state.get_data()
    try:
        put_message_db(str(list(data.values())[0]), message.from_user.id)
        await message.answer("Запрос успешно отправлен")
        await state.clear()
    except Exception as e:
        await message.answer("Не удалось отправить запрос, попробуйте позже")


@dp.message(F.text == "Записаться на мероприятие")
async def leader_events(message: Message):
    cur=conn.cursor()
    cur.execute('SELECT token_date FROM access_token')
    access_token_date=cur.fetchone()[0]
    cur.close()
    date_difference=date.today() - access_token_date
    if date_difference.days < 14:
        cur=conn.cursor()
        cur.execute('SELECT access_token FROM access_token')
        access_token=cur.fetchone()[0]
        cur.close()
        events_headers={'Authorization': f'Bearer {access_token}'}
        try:
            get_events_response=requests.get(get_hot_point_events_url, headers=events_headers)
        except Exception:
            bot.send_message(message.chat.id, 'Не удалось связаться с сервером Leader-id. Попробуйте позже')
        if get_events_response.status_code == 200:
            events=get_events_response.json()
            events_ids=[event["id"] for event in events["items"]]
            if len(events_ids) > 0:
                await message.answer('Вот список доступных мероприятий:')
                for event in events_ids:
                    await message.answer(f'{create_events_url}{event}')
            else:
                await message.answer('Нет мероприятий на ближайшее время')
        else:
            await message.answer(f'Ошибка в получении мероприятий {get_events_response.text}')
    else:
        cur=conn.cursor()
        cur.execute('SELECT refresh_token FROM access_token')
        refresh_token=cur.fetchone()[0]
        refresh_data={
            'client_id': leader_client_id,
            'client_secret': leader_client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        try:
            refresh_response=requests.post(get_access_token_url, json=refresh_data)
        except Exception:
            bot.send_message(message.chat.id, 'Не удалось подключиться к Leader-id')
        if refresh_response.status_code == 200:
            access_token=refresh_response.json()['access_token']
            refresh_token=refresh_response.json()['refresh_token']
            current_date=date.today()
            cur=conn.cursor()
            cur.execute(f'UPDATE access_token SET access_token = %s, refresh_token = %s, token_date = %s',
                        (str(access_token), str(refresh_token), current_date))
            conn.commit()
            cur.close()

            events_headers={'Authorization': f'Bearer {access_token}'}
            try:
                get_events_response=requests.get(get_hot_point_events_url, headers=events_headers)
            except Exception:
                await message.answer('Не удалось получить доступ к leader-id, попробуйте позже '
                                     'или обратитесь в тех. поддержку')
            if get_events_response.status_code == 200:
                events=get_events_response.json()
                events_ids=[event["id"] for event in events["items"]]
                await message.answer('Вот список доступных мероприятий:')
                for event in events_ids:
                    await message.answer(f'{create_events_url}{event}')
            else:
                await message.answer(f'Ошибка в получении мероприятий')
        else:
            await message.answer(f'Ошибка аутентификации\n {refresh_response.text}')


####КОНЕЦ ОБРАБОТКА КОММАНД И ТЕКСТА####


####ОПРОСЫ#####

user_score=0


def get_question_by_order(order):
    cur=conn.cursor()
    cur.execute("SELECT questions FROM anketa_questions WHERE id = %s", (order,))
    question_data=cur.fetchone()
    return question_data[0]


async def get_options_by_question_id(question_id):
    cur=conn.cursor()
    cur.execute("SELECT answer FROM anketa_answers WHERE question_id = %s", (question_id,))
    options_data=cur.fetchall()
    options=[option[0] for option in options_data]
    return options


async def continue_poll(user_id, current_question_index):
    poll_questions=get_question_by_order(current_question_index)
    poll_options=get_options_by_question_id(current_question_index)
    await bot.send_poll(user_id,
                        question=poll_questions,
                        options=poll_options,
                        type='regular',
                        is_anonymous=False)


@dp.message(Command('anketa'))
async def anketa(message: types.Message):
    global current_question_index
    await message.answer('Сейчас вы будете проходить тестирование на уровень компетенций предпринимателя')
    current_question_index=1
    questions=get_question_by_order(current_question_index)
    options=get_options_by_question_id(current_question_index)
    await message.answer_poll(question=questions,
                              options=options,
                              type='regular',
                              is_anonymous=False)

@dp.message(F.text == 'Тестирование')
async def anketa(message: types.Message):
    global current_question_index
    await message.answer('Сейчас вы будете проходить тестирование на уровень компетенций предпринимателя')
    current_question_index=1
    questions=get_question_by_order(current_question_index)
    options=get_options_by_question_id(current_question_index)
    await message.answer_poll(question=questions,
                              options=options,
                              type='regular',
                              is_anonymous=False)


@dp.poll_answer()
async def poll_answer(poll_answer: types.PollAnswer):
    user_id=poll_answer.user.id
    global user_score
    user_score+=int(poll_answer.option_ids[0])
    global current_question_index
    if current_question_index <= 11:
        current_question_index+=1
        await continue_poll(user_id, current_question_index)
    else:
        if 0 <= user_score <= 11:
            await bot.send_message(user_id,
                                   f'Спасибо за проходение опроса, ваш результат: низкий уровень компетенций. \nДля того чтобы улучшить свои навыки, можете посмотреть наш видео-курс по команде \b"/study".')
        elif 12 <= user_score <= 16:
            await bot.send_message(user_id,
                                   f'Спасибо за проходение опроса, ваш результат: уровень компетенций - ниже среднего. \nСоветуем вам пройти видео-курс по команде \b"/study", а затем попробуйте пройти акселерацию, она поможет вам улучшить свои навыки.')
        elif 17 <= user_score <= 21:
            await bot.send_message(user_id,
                                   f'Спасибо за проходение опроса, ваш результат: средний уровень компетенций. \nЗапишитесь на акселерацию, попробуйте свои силы в создании и продвижении стартапа')
        else:
            await bot.send_message(user_id,
                                   f'Спасибо за проходение опроса, ваш результат: высокий уровень компетенций. \nОтлично! Записывайтесь на акселерацию, у вас все получится!')


####КОНЕЦ ОПРОСЫ#####


####ОБРАБОТКА КОЛЛБЭКОВ####

@dp.callback_query(F.data == 'get_all_info_urls')
async def get_all_info_urls(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('SELECT user_interest1 FROM users WHERE user_id=%s', (callback.from_user.id,))
    user_interest=str(cur.fetchone()[0])
    cur.execute('SELECT urls FROM useful_information_urls WHERE interest_area=%s', (user_interest,))
    useful_information_list=cur.fetchall()
    for url in range(len(useful_information_list)):
        useful_information=str(useful_information_list[url])
        useful_information=re.sub(r'[(),\']', '', useful_information)
        await callback.message.answer(useful_information)
    await callback.message.answer(f'Это немного, но это честная работа', reply_markup=main_menu)
    conn.commit
    cur.close()
@dp.callback_query(F.data == 'Market and marketing')
async def market_callback(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('UPDATE users SET user_interest = %s WHERE user_id = %s',
                ('рынок', callback.from_user.id))
    conn.commit()
    cur.close()
    await callback.message.answer('Вы выбрали Рынок и Маркетинг', reply_markup=main_menu)


@dp.callback_query(F.data == 'Electonics')
async def market_callback(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('UPDATE users SET user_interest = %s WHERE user_id = %s',
                ('электроника', callback.from_user.id))
    conn.commit()
    cur.close()
    await callback.message.answer('Вы выбрали Электроника и связь', reply_markup=main_menu)


@dp.callback_query(F.data == 'IT Expertise')
async def market_callback(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('UPDATE users SET user_interest = %s WHERE user_id = %s',
                ('ит экспертиза', callback.from_user.id))
    conn.commit()
    cur.close()
    await callback.message.answer('Вы выбрали Экспертиза проектов IT', reply_markup=main_menu)


@dp.callback_query(F.data == 'Intellectual property')
async def intellectual_property_callback(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('UPDATE users SET user_interest = %s WHERE user_id = %s',
                ('Интеллектуальная собственность', callback.from_user.id))
    conn.commit()
    cur.close()
    await callback.message.answer("Вы выбрали Интеллектуальную собственность", reply_markup=main_menu)


@dp.callback_query(F.data == 'Legal issues')
async def legal_issues_callback(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('UPDATE users SET user_interest = %s WHERE user_id = %s',
                ('Юр. и бух. вопросы', callback.from_user.id))
    conn.commit()
    cur.close()
    await callback.message.answer("Вы выбрали Юридические и бухгалтерские вопросы", reply_markup=main_menu)


@dp.callback_query(F.data == 'IT issues')
async def it_issues_callback(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('UPDATE users SET user_interest = %s WHERE user_id = %s',
                ('Тех. вопросы по IT', callback.from_user.id))
    conn.commit()
    cur.close()
    await callback.message.answer("Вы выбрали Технические вопросы по IT", reply_markup=main_menu)


@dp.callback_query(F.data == 'CustDev Expertise')
async def cust_expertise_callback(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('UPDATE users SET user_interest = %s WHERE user_id = %s',
                ('Экспертиза CustDev', callback.from_user.id))
    conn.commit()
    cur.close()
    await callback.message.answer("Вы выбрали Экспертиза CustDev", reply_markup=main_menu)


@dp.callback_query(F.data == 'Investment')
async def investment_callback(callback: types.CallbackQuery):
    cur=conn.cursor()
    cur.execute('UPDATE users SET user_interest = %s WHERE user_id = %s',
                ('Инвестиции', callback.from_user.id))
    conn.commit()
    cur.close()
    await callback.message.answer('Вы выбрали Инветиции', reply_markup=main_menu)


@dp.callback_query(F.data == 'change_interest_area')
async def change_interest_area_callback(callback: types.CallbackQuery):
    await callback.message.answer('Выберите интересующую вас область', reply_markup=registration_area_interest)


@dp.callback_query(F.data == 'sbi_news')
async def sbi_callback(callback: types.CallbackQuery):
    await callback.message.answer('Новости СБИ ТУСУР\nhttps://sbi.tusur.ru/#news')


@dp.callback_query(F.data == 'menu_callback')
async def menu_callback(callback: types.CallbackQuery):
    await callback.message.answer("Меню", reply_markup=main_menu)


@dp.callback_query(lambda query: query.data in ['back', 'forward'])
async def handle_navigation_buttons(callback_query: types.CallbackQuery):
    global current_video_index

    if callback_query.data == 'back':
        current_video_index=(current_video_index - 1) % len(videos)
    elif callback_query.data == 'forward':
        current_video_index=(current_video_index + 1) % len(videos)

    await send_video_menu(callback_query.message)


@dp.callback_query(F.data == 'add_viewed_vid')
async def add_viewed_vid(callback: types.CallbackQuery):
    await callback.answer('Спасибо за просмотр')
    cur=conn.cursor()
    cur.execute('SELECT user_viewed_vids FROM users WHERE user_id=%s', (current_user_id,))
    rows=cur.fetchall()
    user_viewes=int(rows[0])
    user_viewes+=1
    cur.execute('UPDATE users SET user_viewed_vids = %s WHERE user_id = %s',
                (user_viewes, current_user_id))
    conn.commit()
    cur.close()


####КОНЕЦ ОБРАБОТКА КОЛЛБЭКОВ####

####Видео-курс####
videos=[
    {"title": "Приветственное видео", "url": "youtube.com"},
    {"title": "Технологический суверенитет РФ", "url": "youtube.com"},
    {"title": "Инновационный продукт", "url": "youtube.com"},
    {"title": "Методология развития клиентов (часть 1)", "url": "youtube.com"},
    {"title": "Методология развития клиентов (часть 2)", "url": "youtube.com"},
    {"title": "Методология JTBD", "url": "youtube.com"},
    {"title": "Анализ рынка", "url": "youtube.com"},
    {"title": "Сегментация", "url": "youtube.com"},
    {"title": "Бизнес-моделирование", "url": "youtube.com"},
    {"title": "Маркетинг и PR (часть 1)", "url": "youtube.com"},
    {"title": "Маркетинг и PR (часть 2)", "url": "youtube.com"},
    {"title": "Управление результатами ИД", "url": "youtube.com"},
    {"title": "Юнит-экономика (часть 1)", "url": "youtube.com"},
    {"title": "Юнит-экономика (часть 2)", "url": "youtube.com"},
    {"title": "Государственные инвестиции", "url": "youtube.com"},
    {"title": "Постакселерация", "url": "youtube.com"}
]

current_video_index=0


async def send_video_menu(message: types.Message):
    keyboard=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back"),
                                                    InlineKeyboardButton(text="Выбрать",
                                                                         url=videos[current_video_index]["url"]),
                                                    InlineKeyboardButton(text="Вперед", callback_data="forward")]])

    await message.answer(
        f"Выберите видео ({current_video_index + 1}/{len(videos)}):\n{videos[current_video_index]['title']}",
        reply_markup=keyboard)


################################ РЕАКЦИЯ НА КНОПКИ ГЛАВНОГО МЕНЮ ################################
@dp.message(F.text == "Подать заявку на акселератор")
@dp.message(F.text == "Сайт")
@dp.message(F.text == "Глеб Садыков")
@dp.message(F.text == "Валерия Цибульникова")
@dp.message(F.text == "Мария Брусянина")
@dp.message(F.text == "Валентина Мельникова")
@dp.message(F.text == "Галина Волкова")
@dp.message(F.text == "Роман Кульшин")
@dp.message(F.text == "Василий Лихачев")
@dp.message(F.text == "Виктор Горбачев")
@dp.message(F.text == "Александр Смирнов")
@dp.message(F.text == "Юрий Гриценко")
@dp.message(F.text == "Иван Тикшаев")
@dp.message(F.text == "Андрей Ивлев")
@dp.message(F.text == "Вера Пудкова")
@dp.message(F.text == "Рынок и маркетинг")
@dp.message(F.text == "Электроника и связь")
@dp.message(F.text == "Интеллектуальная собственность")
@dp.message(F.text == "Юридические и бухгалтерские вопросы")
@dp.message(F.text == "Технические вопросы по IT")
@dp.message(F.text == "Экспертиза CustDev")
@dp.message(F.text == "Инвестиции")
@dp.message()
async def func_message(message: Message):
    global back_button_state
    if message.text == 'Подать заявку на акселератор':
        await message.answer(f'Подать заявку на акселерацию можно тут:\nhttps://startup-poligon.ru/accelerator')

    elif message.text == 'Сайт':
        await message.answer('https://sbi.tusur.ru/')

    elif message.text == 'Глеб Садыков':
        back_button_state='investment_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]])
        await message.answer_photo(photo='https://disk.yandex.ru/i/Q6CiwnZ3AelntQ')
        await message.answer(f'<strong>Глеб Садыков.</strong>'
                             f'\n• Эксперт, ментор акселерации TomsHUB 2021, руководитель акселератора UNIVERSITY УМНИК, руковаодитель акселерационной программы ТУСУР'
                             f'\n• Экспертная деятельность продолжается на протяжении 3-х лет, имеются подтверждающие документы. Принял участие в 10-ти программах акселерации.'
                             f'\n Общая насмотренность более 1500 проектов. Организатор акселерационных программ: Стартап-Полигон, Искусственный интеллект ТУСУР,  "UNIVERCITY УМНИК", '
                             f'\nментор акселераторов Архипелаг 2022, 2023, TomskHUB 2021-2023, член консорциума "Большой университет Томска" в направлении Технологическое предпринимательство, '
                             f'\nлидер Предпринимательской Точки кипения ТУСУР. Доверенный эксперт НТИ, эксперт АСИ, эксперт ФСИ. '
                             f'\nПартнёр компаний экосистем МТС и Яндекс. Привлёк в проекты более 300 млн. руб. '
                             f'\n• Заинтересован в проектах: TRL 2-6 от "сформулирована концепция технологии" до "есть полноценный работающий прототип".'
                             f'\n• Стаж более 12 лет.'
                             f'\n• telegram id - @Nixxxy.', parse_mode=ParseMode.HTML, reply_markup=buttons)



    elif message.text == 'Валерия Цибульникова':
        back_button_state = 'market_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]])
        await message.answer_photo(
            photo='https://storage.tusur.ru/files/162184/230-324!mn/2023-03-25_18.49.11_(2)_(1).JPG')
        await message.answer(f'<strong>Валерия Цибульникова.</strong>'
                             f'\n• Имеет опыт работы в финансовый консалтинге проектов,  также опыт более 15 лет работы в инвестициях и бизнес-планировании, 3 года опыта работы экспертом НТИ, также ведет курс по технологическому предпринимательству.'
                             f'\n• Директор филиала инвестиционной компании АО «ИнвестАгент» в г.Томске, директор филиала АНО «Международная академия инвестиций и трейдинга»'
                             f'\n• Проекты, в которых эксперт принимает участие: Повышение финансовой грамотности населения, разработка онлайн тренажёров для отработки навыков инвестирования, разработка финансовых моделей стартап проектов и др.'
                             f'\n• Заинтересована в проектах на любом этапе развития.'
                             f'\n• Стаж 20 лет.'
                             f'\n• telegram id - @@Valeriya_Ts70.', parse_mode=ParseMode.HTML,
                             reply_markup=buttons)

    elif message.text == 'Мария Брусянина':
        back_button_state='market_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]])
        await message.answer_photo(
            photo='https://downloader.disk.yandex.ru/preview/74880226d0166d04285083c6bce55d23b5f9de837015d6fedd9899a259b4a43e/662958f1/LUwxDGv_GjTVE6dg8b8ufCKzAxjqljC1KnHXA6M8b0RTzwlzKDUTtwRFO4UfjVqM4RDIUKtJ6yD9gj6fLZ9Qng%3D%3D?uid=0&filename=%D0%91%D1%80%D1%83%D1%81%D1%8F%D0%BD%D0%B8%D0%BD%D0%B0_%D0%9C%D0%A1.jpeg&disposition=inline&hash=&limit=0&content_type=image%2Fjpeg&owner_uid=0&tknv=v2&size=1879x931')
        await message.answer(f'<strong>Мария Брусянина</strong>'
                             f'\n• Имеет 15-ти летний опыт работы в маркетинге и образовании: проведение исследований, разработка стратегий, программ продвижения, образовательных курсов, модулей для студентов, представителей бизнеса (Президентская программа)'
                             f'\n• Эксперт акселерационной программы, к.э.н. '
                             f'\n• Проекты, в которых эксперт принимает участие: «Школа нейротехнологий», СибГМУ, «МастерДент», СК «Мастер», SkyDent (Новосибирск).'
                             f'\n• Заинтересована в проектах на любом этапе развития.'
                             f'\n• Стаж 15 лет.'
                             f'\n• telegram id - @Maria_brusyanina.', parse_mode=ParseMode.HTML, reply_markup=buttons)
    elif message.text == 'Александр Смирнов':
        back_button_state='custdev_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]])
        await message.answer_photo(photo='https://disk.yandex.ru/i/J0GIDUk-cjk93Q')
        await message.answer(f'<strong>Смирнов Александр Олегович</strong>'
                             f'\n• Имеет 6-ти летний опыт работы'
                             f'\n• Участие в акселерационных программах в разных ролях '
                             f'\n(линейный, трекер, ведущий трекер, старший трекер, спикер, тренер, академический директор, эксперт):'
                             f'\nСибГМУ, ТУСУР, ТГПУ, ТГУ, ТПУ, ТюмГУ, НГТУ, НГУЭУ, МТС Гараж, АСИ, TomskHub, Архипелаг'
                             f'\n• Реализовал 7 продуктов в области цифровизации сельского хозяйства, в их числе: '
                             f'\nAgroERP система, почвенные датчики с применением mash-сети, дистанционный сенсор определения элементов питания в почве, '
                             f'\nАвтоматизированная система учёта уборочных работ, дроны-ретрансляторы мобильной связи'
                             f'\n• Имеется опыт создания IT продуктов. Запускает свой стартап'
                             f'\n• Заинтересован в проектах на любом этапе развития.'
                             f'\n• telegram id - @smirallive', parse_mode=ParseMode.HTML, reply_markup=buttons)
    elif message.text == 'Юрий Гриценко':
        back_button_state = 'electeonics_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]])
        await message.answer_photo(photo='https://storage.tusur.ru/files/158252/230-324!mn/Gricenko.jpeg')
        await message.answer(f'<strong>Юрий Гриценко</strong>'
                             f'\n• Имеет 10 летний опыт работы в сфере инновационной деятельности университета, региона, страны'
                             f'\n• Участвовал в Более чем в 10-ти акселерационных программах, ответственный исполнитель и руководитель  в 5-ти крупных НИОКР на общую сумму более 300 млн. руб,'
                             f'\n руководитель программ ПУТП в университете. Эксперт заявок в программы УМНИК, Студенческий Стартап,СТАРТ ФСИ.'
                             f'\n• Общий стаж работы – 28 лет; стаж управленческой деятельности – 8 лет, '
                             f'\nначальник Инновационного управления; стаж научно-педагогической деятельности – 24 года'
                             f'\n• Заинтересован в проектах на любом этапе развития.'
                             f'\n• telegram id - @Iksyuunya', parse_mode=ParseMode.HTML, reply_markup=buttons)

    elif message.text == 'Валентина Мельникова':
        back_button_state='intellectual_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]
        ])
        await message.answer_photo(photo='https://storage.tusur.ru/files/116195/230-324!mn/Melnikova.jpg')
        await message.answer(f'Валентина Мельникова: Зав. кафедрой ИГПиПОИД.\n'
                             'ООО «Компания «Томское агентство инновационного развития», генеральный директор\n'
                             'Ссылка на experts.nti.work: https://experts.nti.work/e-registry/3271/profile\n'
                             f' telegram id - @Valentina_Melnikowa',
                             reply_markup=buttons)
    elif message.text == "Виктор Горбачев":
        back_button_state = 'market_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]
        ])
        await message.answer_photo(photo='https://disk.yandex.ru/i/EJ2Vzs7FcPYEYg')
        await message.answer(f'<strong>Виктор Горбачев</strong>'
                             f'\n• Имеет 4-х летний опыт в области запуска новых продуктов и выявлении точек роста работающих'
                             f'\n• Участвовал в следующих проектах: Menu.money в качестве CEO, ВкусВилл - трекинг продуктовых команд, Heritage, Correcto.oniline,'
                             f'\nKupi.co - менеджер продукта, стартап-студия VentureLamp - CEO, Акселератор ФРИИ - менеджер продукта'
                             f'\n• Был трекером более 50-ти продуктовых команд'
                             f'\n• Интересующий уровень проектов: разработан MVP'
                             f'\n• telegram id - @victor_gorbachev', parse_mode=ParseMode.HTML, reply_markup=buttons)
    elif message.text == 'Василий Лихачев':
        back_button_state='investment_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]
        ])
        await message.answer_photo(photo='https://disk.yandex.ru/i/xv9joy8bEX6f6A')
        await message.answer(f'<strong>Лихачев Василий Николаевич</strong>'
                             f'\n• Имеет 15-ти летний опыт работы'
                             f'\n• Корпоративный трекер: ВкусВилл, Sravni, Агама'
                             f'\n• Трекер/Старший трекер в акселераторах: Сбербанк, ФРИИ, Scalerator, \nСтартех, Агама, Агротех, MUIV.LAB, Астана Хаб, Терриконовая долина, ТУСУР, СВФ, 2innovations.ru, Прорыв, КЛИК'
                             f'\n• Пройдено 30 программ акселерации'
                             f'\n• Заинтересован в проектах на любой стадии развития'
                             f'\n• telegram - @lihachevvasily', parse_mode=ParseMode.HTML, reply_markup=buttons)

    elif message.text == 'Галина Волкова':
        back_button_state='legal_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]])
        await message.answer_photo(photo='https://disk.yandex.ru/i/PEQn8ffAmRHXfA')
        await message.answer(f'<strong>Галина Волкова.</strong>'
                             f'\n•С 1993 по 2004 год являлась бухгалтером Беловского строительного управления,  в последствии работала главным бухгалтером и юристом-консультантом. В настоящее время занимает должность директора компании "ООО ЦБУ «Баланс – Т"»'
                             f'\n• Проекты, в которых эксперт принимает участие: Проведение лекций, консультаций «Создание и сопровождение юридического лица» в качестве эксперта в Проектах «Стартап – Полигон II», «Стартап – Полигон III».'
                             f'\n• Заинтересована в проектах на любом этапе развития.'
                             f'\n• Стаж 30 лет.'
                             f'\n• telegram - @V1902gv.', parse_mode=ParseMode.HTML,
                             reply_markup=buttons)

    elif message.text == 'Роман Кульшин':
        back_button_state='tech_issues_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]])
        await message.answer_photo(
            photo='https://sun9-77.userapi.com/impg/DWovgR65CcTHdtZVYsgc8pn-Bmw9Gn0dwt9TFQ/dXKzXuLj808.jpg?size=2560x1706&quality=96&sign=6eb9a4835c8c52b5e08db6775c65f060&type=album')
        await message.answer(f'<strong>Роман Кульшин</strong>'
                             f'\n• Имеет 10-ти летний опыт в сфере IT и 3-х летный опыт преподавания и наставничества'
                             f'\n• Руководитель комапании по разработке мобильных приложей с 25+ выполненых проектов, \nнаставник 7 студенческих проектных групп в области IT, исскуственного интелекта, нейротехнологий и кибернетики, \nв том числе проектов поддержаных Фондом содействия инновациям'
                             f'\n• Пройдено 3 акселератора, 12 проектов'
                             f'\n• Интересуют проекты без идеи/с идеей, есть mvp'
                             f'\n• telegram - @RomanGramor', parse_mode=ParseMode.HTML, reply_markup=buttons)
    elif message.text == 'Иван Тикшаев':
        back_button_state='tech_issues_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]
        ])
        await message.answer_photo(photo='https://disk.yandex.ru/i/zevsJ0u_l71uAg')
        await message.answer(f'<strong>Иван Тикшаев</strong>'
                             f'\n• Генеральный директор компании DevInside, основатели и руководитель сатртап проекта TenderChad.'
                             f'\n Участник кластера Smart Technologies Tomsk, резидент СБИ "Дружба", преподаватель кафедры АОИ ТУСУР,'
                             f'\n молодой ученый, наставник инновационных проектов, эксперт платформы НТИ.'
                             f'\n• Направления научной деятельности: Искусственный интеллект, нейротехнологии, кибернетика, анализ данных, машинное обучение, предиктивная аналитика.'
                             f'\n• telegram - @Do6riu_KoT', parse_mode=ParseMode.HTML, reply_markup=buttons)
    elif message.text == 'Андрей Ивлев':
        back_button_state='electeonics_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]
        ])
        await message.answer(f'<strong>Андрей Ивлев</strong>'
                             f'\n• telegram - @agivlev', parse_mode=ParseMode.HTML, reply_markup=buttons)
    elif message.text == 'Вера Пудкова':
        back_button_state = 'market_experts_menu_state'
        buttons=types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text='Назад')]
        ])
        await message.answer_photo(
            photo='https://storage.tusur.ru/files/168003/230-324!mn/%D0%A4%D0%BE%D1%82%D0%BE.JPG')
        await message.answer(f'<strong>Пудкова Вера Васильевна</strong>'
                             f'\n• Работает 25 лет в инновационной деятельности'
                             f'\n• Создание и развитие УНИК (Учебно-научно-инновационного комплекса - Инновационного окружения) ТУСУРа. \nСоздание и развитие ОКР ТУСУРа. Создание Межвузовского студенческого бизнес-инкубатора "Дружба". \nСодействие проведению акселерационных программ, тренингов. \nЭкспертиза проектов с точки зрения коммерциализации, в том числе по ПП-218.'
                             f'\n• Приняла участие в 4-ех акселерационных программах. Как эксперт - более 20-ти проектов'
                             f'\n• Заинтересована в проектах на любом жтапе развития'
                             f'\n• WhatsApp - +79138731120', parse_mode=ParseMode.HTML, reply_markup=buttons)
    elif message.text == 'Рынок и маркетинг':
        back_button_state = 'choose_expert_state'
        await message.answer(f'Рынок и маркетинг', reply_markup=market_keyboard)
    elif message.text == 'Интеллектуальная собственность':
        back_button_state='choose_expert_state'
        await message.answer('Интеллектуальная собственность', reply_markup=intellectual_property_keyboard)
    elif message.text == 'Юридические и бухгалтерские вопросы':
        back_button_state='choose_expert_state'
        await message.answer('Юридические и бухгалтерские вопросы', reply_markup=legal_issues_keyboard)
    elif message.text == 'Технические вопросы по IT':
        back_button_state='choose_expert_state'
        await message.answer('Технические вопросы по IT', reply_markup=technical_issues_keyboard)
    elif message.text == 'Экспертиза CustDev':
        back_button_state='choose_expert_state'
        await message.answer('Экспертиза CustDev', reply_markup=cust_expertise_keyboard)
    elif message.text == 'Инвестиции':
        back_button_state='choose_expert_state'
        await message.answer('Инвестиции', reply_markup=investment_keyboard)
    elif message.text == 'Электроника и связь':
        back_button_state='choose_expert_state'
        await message.answer('Электроника и свзяь', reply_markup=electonics_keyboard)
    else:
        await message.answer('Данное сообщение не распознано, обратитесь в тех. поддержку')


####ТЕХ.ПОДДЕРЖКА####
@dp.message(Command('admin'))
async def admin_panel(message: types.Message):
    user_id=message.from_user.id
    if check_moder_status(user_id):
        await message.answer("Ты админ", reply_markup=admin_menu)
    else:
        await message.answer("Ты не админ")


@dp.message(Tech_Support_Admin.req_id)
async def get_req_id(message: types.Message, state: FSMContext):
    request_id=message.text
    cursor=conn.cursor()
    cursor.execute("SELECT req_user_chat_id FROM req_queue WHERE req_id = %s", (request_id,))
    user_chat_id=cursor.fetchone()

    cursor.close()
    await state.set_state(Tech_Support_Admin.answer)
    await state.update_data(answer=int(user_chat_id[0]))
    await message.answer(f'Напишите ответ пользователю')


@dp.message(Tech_Support_Admin.answer)
async def admin_answer(message: types.Message, state: FSMContext):
    answer_data=await state.get_data()
    await state.set_state(menu)
    await bot.send_message(answer_data["answer"],
                           f'Вам ответили на запрос:\n{message.text}\nЕсли данный ответ помог, пожалуйста, напишите "Удалить запрос"')


@dp.message(Tech_Support_Admin.mailing)
async def send_mail(message: types.Message, state: FSMContext):
    cur=conn.cursor()
    cur.execute('SELECT user_chat_id FROM users')
    chat_id_list=cur.fetchall()
    for ids in chat_id_list:
        chat_id=int(ids[0])
        await bot.send_message(chat_id, f'{message.text}')
    await state.set_state(Tech_Support_Admin.menu)


@dp.message(Tech_Support_Admin.menu)
async def menu(message: types, state: FSMContext):
    state.clear_state()
    await message.answer(reply_markup=admin_menu)


def put_message_db(data, user_id):
    cursor=conn.cursor()
    cursor.execute("INSERT INTO req_queue (user_id, req_text, req_user_chat_id) VALUES (%s, %s, %s)",
                   (user_id, data, user_id))
    conn.commit()
    cursor.close()


@dp.message(F.text == "Сделать рассылку")
@dp.message(F.text == "Посмотреть все запросы")
@dp.message(F.text == "Меню")
async def select_reqs(message, state: FSMContext):
    if message.text == 'Меню':
        await message.answer(f'Меню', reply_markup=main_menu)
    elif message.text == 'Сделать рассылку':
        await state.set_state(Tech_Support_Admin.mailing)
        await message.answer('Напишите сообщение, которое хотите разослать пользователям')
    elif message.text == 'Посмотреть все запросы':
        cursor=conn.cursor()
        cursor.execute("SELECT req_text, req_id, user_id, req_user_chat_id FROM req_queue WHERE req_status = false")
        rows=cursor.fetchall()
        conn.commit()
        cursor.close()
        iterator=1

        for row in rows:
            req_text=str(row[0])
            req_id=str(row[1])
            await message.answer(f'Активный запрос №{req_id}, text:{req_text}, ')
            iterator+=1
        await state.set_state(Tech_Support_Admin.req_id)
        await message.answer('Напишите номер запроса, который хотите обработать')


####КОНЕЦ ТЕХ.ПОДДЕРЖКА####

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot is shutting down')
