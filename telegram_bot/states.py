from aiogram.fsm.state import State, StatesGroup


class Reg(StatesGroup):
    waiting_contact = State()
    waiting_name = State()


class Quiz(StatesGroup):
    in_progress = State()
