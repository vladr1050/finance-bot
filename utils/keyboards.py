from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📒 History", callback_data="menu_history")],
        [InlineKeyboardButton(text="📊 Category Report", callback_data="menu_category_report")],
        [InlineKeyboardButton(text="🛠 Adjust Budget", callback_data="menu_adjust")],
        [InlineKeyboardButton(text="📈 Forecast", callback_data="menu_forecast")],
        [InlineKeyboardButton(text="➕ Add Expense", callback_data="menu_add_expense")]
    ])

def success_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
        [InlineKeyboardButton(text="📋 View Data", callback_data="view_last_action")],
        [InlineKeyboardButton(text="➕ Do Similar Again", callback_data="repeat_last_action")]
    ])

def fixed_expense_item_kb(fixed_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_fixed:{fixed_id}"),
            InlineKeyboardButton(text="❌ Delete", callback_data=f"delete_fixed:{fixed_id}")
        ]
    ])

def confirm_delete_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes, delete", callback_data="confirm_delete"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_delete")
        ]
    ])
