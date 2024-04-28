from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta

from create_bot import dp, bot, scheduler, os
from db.sql import Psql
from keyboards.user_kb import user_kb, gen_markup
from utils.coinmarketcap import CoinMarketCap


URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
PARAMS = {
    'start': '1', 
    'limit': '10', 
    'convert':'USD', 
}

cmc = CoinMarketCap.connect(URL, PARAMS)
pairs = cmc.get_pairs()
pairs_keys = cmc.get_pairs_keys()

async def start_schedule_jobs():
    start_date = datetime.now() + timedelta(minutes=1)
    interval_trigger = IntervalTrigger(minutes=1)
    date_trigger = DateTrigger(run_date=start_date)
    trigger = AndTrigger([interval_trigger, date_trigger])
    scheduler.add_job(parse_cmc, trigger)
    print(datetime.now())

async def parse_cmc():
    
    cmc = CoinMarketCap.connect(URL, PARAMS)
    pairs = cmc.get_pairs()
    
    db = await Psql.connect()
    all_users_data = await db.get_all_users_data()
    await db.close_pool()
    
    chat_id = os.getenv("CHAT_ID")
    
    for item in all_users_data:
        if item['min1'] > pairs[item['coin1']]:
            await bot.send_message(chat_id, f'{item["coin1"]} упала ниже '
            f'вашего минимального значения, текущая стоимость: {round(pairs[item["coin1"]], 2)}')
        if item['max1'] < pairs[item['coin1']]:
            await bot.send_message(chat_id, f'{item["coin1"]} поднялась '
            f'выше вашего максимального значения, текущая стоимость: {round(pairs[item["coin1"]], 2)}')
        if item['min2'] > pairs[item['coin2']]:
            await bot.send_message(chat_id, f'{item["coin2"]} упала ниже '
            f'вашего минимального значения, текущая стоимость: {round(pairs[item["coin2"]], 2)}')
        if item['max2'] < pairs[item["coin2"]]:
            await bot.send_message(chat_id, f'{item["coin2"]} поднялась '
            f'выше вашего максимального значения, текущая стоимость: {round(pairs[item["coin2"]], 2)}')


class FSMCoins(StatesGroup):
    name = State()
    min = State()
    max = State()


@dp.message(StateFilter('*'), Command('start'))
async def command_start_handler(msg: Message, state: FSMContext) -> None:
    
    if await state.get_state():
        await state.clear()

    user_id = msg.from_user.id

    db = await Psql.connect()
    await db.create_user(user_id, None, None, 0, 0, 0, 0)
    await db.close_pool()
    
    await bot.send_message(user_id, 'Привет!\nЯ Ваш персональный бот '
                           'для отслеживания изменений курсов криптовалют!\n'
                           'На данный момент вы можете отслеживать только две '
                           'монеты.', 
                           reply_markup=user_kb())


@dp.message(StateFilter('*'), F.text == 'Монеты!')
async def get_coins_menu(msg: Message, state: FSMContext):
    
    if await state.get_state():
        await state.clear()
    
    user_id = msg.from_user.id
    
    db = await Psql.connect()
    user_data = await db.get_user_data(user_id)
    await db.close_pool()

    user_coins = [user_data[0]['coin1'], user_data[0]['coin2']]

    coins_total = 0
    coins = []

    for item in user_coins:
        if item is not None and item.strip():
            coins_total += 1
            coins.append(item.strip())
    
    if user_data[0]['min1'] == 0:
        min1_info = ''
    else:
        min1_info = str(user_data[0]['min1'] )+ ', '
        
    if user_data[0]['min2'] == 0:
        min2_info = ''
    else:
        min2_info = str(user_data[0]['min2']) + ', '
        
    if user_data[0]['max1'] == 0:
        max1_info = ''
    else:
        max1_info = user_data[0]['max1']
        
    if user_data[0]['max2'] == 0:
        max2_info = ''
    else:
        max2_info = user_data[0]['max2']

    user_coins_info = f'{coins_total}\n{coins[0] if coins else "" } {min1_info} {max1_info}\n{coins[1] if len(coins)>1 else ""} {min2_info} {max2_info}'

    
    if coins_total == 0:
        keyboard = gen_markup([['Добавить монеты', 'add_coins']])
    elif coins_total == 1:
        keyboard = gen_markup([['Добавить монеты', 'add_coins'], 
                            ['Убрать монеты', 'remove_coins']])
    elif coins_total == 2:
        keyboard = gen_markup([['Убрать монеты', 'remove_coins']])
        
    await bot.send_message(user_id, 'Ты можешь посмотреть какие монеты '
                           'сейчас у тебя подключены, можешь убрать '
                           'подключенные монеты или добавить новые.\n'
                           f'Сейчас подключено {user_coins_info} ',
                           reply_markup=keyboard)


@dp.callback_query(StateFilter('*'), F.data.contains('add_coins'))
async def add_coins(cq: CallbackQuery, state: FSMContext):
    
    if await state.get_state():
        await state.clear()

    await bot.answer_callback_query(cq.id)
    user_id = cq.from_user.id
    
    keyboard = gen_markup([['Отмена', 'cancel']])
    
    await bot.edit_message_text(message_id=cq.message.message_id, chat_id=user_id, 
                                text='Введите название монеты в полном виде, '
                                'например Bitcoin, Ethereum и тд',
                                reply_markup=keyboard)
    
    await state.set_state(FSMCoins.name)


@dp.message(StateFilter(FSMCoins.name), F.content_type.in_({'text'}))
async def add_coin_name(msg: Message, state: FSMContext):
    
    user_id = msg.from_user.id
    if not msg.text in pairs_keys:
        await bot.send_message(user_id, 'Вы ввели некорректное значение, '
                               'введите снова')
        return
    db = await Psql.connect()
    user_data = await db.get_user_data(user_id)
    if user_data[0]['coin1'] == None:
        coin_target = 'coin1'
    elif user_data[0]['coin2'] == None:
        coin_target = 'coin2'
        if user_data[0]['coin2'] == msg.text:
            await bot.send_message(user_id, 'Такая монета у вас уже добавлена, '
                                   'введите другую')
            return

    await db.add_coin(user_id, coin_target, msg.text)
    await db.close_pool()
    
    await bot.send_message(user_id, 'Монета записана, теперь введите '
                           'минимальное пороговое значение')

    await state.set_state(FSMCoins.min)


@dp.message(StateFilter(FSMCoins.min), F.content_type.in_({'text'}))
async def add_min_value(msg: Message, state: FSMContext):
    
    user_id = msg.from_user.id
    
    try:
        min_value = float(msg.text)
    except:
        await bot.send_message(user_id, 'Вы ввели не цифровое значение, '
                               'попробуйте снова')
        return

    db = await Psql.connect()
    user_data = await db.get_user_data(user_id)
    if user_data[0]['min1'] == 0:
        value_target = 'min1'
    elif user_data[0]['min2'] == 0:
        value_target = 'min2'
        
    await db.add_value(user_id, value_target, min_value)
    await db.close_pool()
    
    await bot.send_message(user_id, 'Вы ввели минимальное значение, '
                           'введите максимальное')
    
    await state.set_state(FSMCoins.max)


@dp.message(StateFilter(FSMCoins.max), F.content_type.in_({'text'}))
async def add_max_value(msg: Message, state: FSMContext):
    
    user_id = msg.from_user.id
    
    try:
        max_value = float(msg.text)
    except:
        await bot.send_message(user_id, 'Вы ввели не цифровое значение, '
                               'попробуйте снова')
        return
    
    db = await Psql.connect()
    user_data = await db.get_user_data(user_id)
    
    
    if user_data[0]['max1'] == 0:
        value_target = 'max1'
    elif user_data[0]['max2'] == 0:
        value_target = 'max2'
        
    if msg.text <= user_data[0][f'min{value_target[-1]}']:
        await bot.send_message(user_id, 'Максимальное значение не может '
                               'быть меньше минимального, '
                               'попробуйте снова')
        return
        
    await db.add_value(user_id, value_target, max_value)
    await db.close_pool()
    
    await bot.send_message(user_id, 'Вы ввели максимальное значение. '
                           'Сохранено. Когда курс перейдёт минимальное или '
                           'максимальное значение, я вам сообщу.', 
                           reply_markup=user_kb())
    
    await state.set_state(FSMCoins.max)


@dp.callback_query(StateFilter('*'), F.data.contains('remove_coins'))
async def remove_coins(cq: CallbackQuery, state: FSMContext):
    
    if await state.get_state():
        await state.clear()

    await bot.answer_callback_query(cq.id)
    user_id = cq.from_user.id
    
    db = await Psql.connect()
    user_data = await db.get_user_data(user_id)
    await db.close_pool()
    coin_list = []
    if user_data[0]['coin1']:
        coin1 = user_data[0]['coin1']
        coin_list.append([coin1, 'target_remove_coin1'])
    if user_data[0]['coin2']:
        coin2 = user_data[0]['coin2']
        coin_list.append([coin2, 'target_remove_coin2'])
    
    coin_list.append(['Отмена', 'cancel'])
    keyboard = gen_markup(coin_list)
    
    await bot.send_message(user_id, 'Выберите название монеты, которую хотите убрать',
                           reply_markup=keyboard)
    

@dp.callback_query(StateFilter('*'), F.data.startswith('target_remove_'))
async def remove_coins(cq: CallbackQuery, state: FSMContext):
    if await state.get_state():
        await state.clear()

    await bot.answer_callback_query(cq.id)
    user_id = cq.from_user.id
    target_remove = cq.data.split('_')[-1]
    db = await Psql.connect()
    await db.add_coin(user_id, target_remove, None)
    await db.add_value(user_id, f'min{target_remove[-1]}', 0)
    await db.add_value(user_id, f'max{target_remove[-1]}', 0)
    await db.close_pool()
    await bot.send_message(user_id, 'Монета удалена', reply_markup=user_kb())




@dp.callback_query(StateFilter('*'), F.data.contains('cancel'))
async def cancel_handler(cq: CallbackQuery, state: FSMContext):
    
    if await state.get_state():
        await state.clear()
    
    await bot.answer_callback_query(cq.id)
    user_id = cq.from_user.id

    await bot.send_message(user_id, 'Отмена', reply_markup=user_kb())
