from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Expense", callback_data="daily_expense")],
        [InlineKeyboardButton(text="📊 Report", callback_data="report")],
        [InlineKeyboardButton(text="📅 History", callback_data="view_history")],
        [InlineKeyboardButton(text="💰 Savings", callback_data="view_savings")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")]
    ])

def settings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Edit Income", callback_data="edit_income")],
        [InlineKeyboardButton(text="📋 Edit Fixed Expenses", callback_data="edit_expense")],
        [InlineKeyboardButton(text="💰 Set Savings", callback_data="set_savings")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
    ])
def after_expense_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Another", callback_data="daily_expense")],
        [InlineKeyboardButton(text="🏠 Back to Menu", callback_data="back_to_menu")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
    )

def skip_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip", callback_data="skip")]
        ]
    )

def skip_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip", callback_data="skip")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
    )

def back_keyboard(callback_data="main_menu"):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back", callback_data=callback_data)]
        ]
    )
def savings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="add_savings")],
        [InlineKeyboardButton(text="➖ Withdraw", callback_data="withdraw_savings")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
    ])
