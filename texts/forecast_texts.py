# texts/forecast_texts.py (Localized version - English only for now)

FORECAST_TEXTS = {
    "feature_locked": "🚫 This feature is available for premium users only.",
    "choose_period": "📅 Select forecast period:",
    "enter_income_change": "💶 Enter expected monthly income change (e.g. +200 or -150):",
    "enter_fixed_change": "🏠 Enter expected change in fixed expenses (e.g. +100 or -50):",
    "enter_savings_goal": "💰 Enter your desired monthly savings goal:",
    "enter_extra_expenses": (
        "🛫 Enter additional planned expenses in format:\n"
        "`Trip to Spain, 800, 1`\n\n"
        "(name, amount, month offset)\n"
        "Send `done` when finished."
    ),
    "invalid_format": "❌ Invalid format. Try: `Trip to Spain, 800, 1`",
    "added_expense": "✔️ Added. Enter another or send `done`.",
    "no_forecast": "❌ No forecast data available. Please run /forecast first.",
    "ask_save": "💾 Would you like to save this scenario?\nSend /save_scenario followed by a name.",
    "save_success": "✅ Scenario '{name}' saved successfully!",
    "delete_success": "🗑 Scenario {id} deleted.",
    "delete_failed": "❌ Could not delete scenario.",
    "no_scenarios": "📭 You have no saved scenarios.",
    "scenario_not_found": "❌ Scenario not found.",
    "forecast_result": "📊 *Forecast Summary:*\n\n",
    "forecast_help": (
        "🧮 *Forecast Planning Help*\n\n"
        "/forecast — start new planning session\n"
        "/my_scenarios — list your saved scenarios\n"
        "/save_scenario <name> — save your current forecast\n"
        "/delete_scenario <id> — delete a saved scenario\n\n"
        "Forecasting is available only to premium users."
    )
}