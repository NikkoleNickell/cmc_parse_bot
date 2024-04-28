from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def gen_btn(list):
    btn = InlineKeyboardButton(
        text=f'{list[0]}', 
        callback_data=f'{list[1]}')
    return btn


# TODO убрать args ???
def gen_markup(list_of_btns, *args):
    buttons = []
    for i in list_of_btns:
        button = gen_btn(i)
        buttons.append([button])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    return markup


def user_kb():
    btn1 = KeyboardButton(text='Монеты!')
    kb = [[btn1]]
    user_kb = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Выберите действие'
    )

    return user_kb
