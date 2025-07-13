from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# >>> Inline Keyboard >>>
def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("👤 View Your Profile.", callback_data="menu_view_profile")],
        [InlineKeyboardButton("📝 View Tasks", callback_data="menu_view_tasks"), InlineKeyboardButton("🔔 Set Reminders", callback_data="menu_view_reminders")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"), InlineKeyboardButton("❌ Close Menue", callback_data="menu_close")]
    ]

    return InlineKeyboardMarkup(keyboard)


def profile_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Return to Menu", callback_data="profile_return")]
    ]

    return InlineKeyboardMarkup(keyboard)


def tasks_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ Add", callback_data="tasks_add"), InlineKeyboardButton("➖ Remove", callback_data="tasks_remove")],
        [InlineKeyboardButton("✅ Mark Done", callback_data="tasks_check")],
        [InlineKeyboardButton("🔙 Return to Menu", callback_data="tasks_return")]
    ]

    return InlineKeyboardMarkup(keyboard)


def subtasks_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Return to Tasks", callback_data="subtasks_return")]
    ]

    return InlineKeyboardMarkup(keyboard)


# <<< Inline Keyboard <<<