import logging
import os
import base64
import json
from dotenv import load_dotenv 
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackContext,CallbackQueryHandler
import firebase_admin
from firebase_admin import credentials, firestore
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
service_account_json = base64.b64decode(os.getenv("FIREBASE_CRED")).decode("utf-8")

cred_dict = json.loads(service_account_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)


db = firestore.client()

jobs = {
    "የቤት አያያዝ": ["ተመላላሽ ሰራተኛ", "ሞግዚት","አስጠኚ", "ልብስ አጣቢ", "ምግብ አብሳይ"],
    "የጥገና ባለሙያ": ["የፍሪጅ ጥገና", "የTV እና ኤሌክትሮኒክስ ጥገና", "የምጣድ እና ምድጃ ጥገና","የዲሽ ተከላ እና ጥገና"],
    "የቤት እድሳት": ["ቀለም ቀቢ", "ጂብሰም ስራ", "የቧንቧ ሰራተኛ", "የኤሌክትሪክ ሰራተኛ", "አናጺ","ግንበኛ","አልሙኒየም ሰራተኛ", "ታይል ንጣፍ"],
    "ሌሎች ሙያዎች": ["ካሸሪ", "ሼፍ", "ፅዳት", "ዲሊቨሪ", "ፀሐፊ", "የሒሳብ ሰራተኛ"] }

user_selected_jobs = {}

sex_keyboard = [["ወንድ", "ሴት"]]
major_areas = {
    "አባገዳ": ["ዴጋጋ", "በዳቱ", "ኦዳ", "ቡታ"],
    "ሉጎ": ["ሚጊራ","ዲሬ ናጋ","በሬቻ"],
    "ቦሌ": ["ጎሮ", "ደዴቻ አራራ", "ደካ አዲ"],
    "ቦኩ": ["ሀሮሬቲ", "ቶርቦ አቦ", "መልካሳ"],
    "ዳቤ": ["ጫፌ", "ሀንጋቱ", "ሰሎቄ ደንጎሬ"],
    "ደምበላ": ["ኢሬቻ", "ወንጂ", "መልካ አዳማ"]
}
reply_markup_sex = ReplyKeyboardMarkup(sex_keyboard, one_time_keyboard=True, resize_keyboard=True)  
ASK_Name, ASK_SEX, ASK_PHONE, ASK_PLACE, ASK_SPECIFIC_AREA, HANDLE_PLACE, SAVE_LOCATION, ASK_JOB, SELECTED_JOBS = range(9)

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("👋በድጋሚ እንኳን ደህና መጡ። ሙሉ ስም አስገቡ?(በፈለጉት ቋንቋ አስገቡ።)")
    return ASK_SEX

async def ask_name(update: Update, context: CallbackContext)-> int:
    await update.message.reply_text("ሙሉ ስም አስገቡ?(በፈለጉት ቋንቋ አስገቡ።)")
    return ASK_SEX

async def ask_sex_handle_name(update: Update, context: CallbackContext)-> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("ፆታ?",reply_markup=reply_markup_sex)
    return ASK_PHONE

async def ask_phone_handle_sex(update: Update, context: CallbackContext)-> int:
    text = update.message.text
    if text == "ወንድ":
        await update.message.reply_text("የምትጠቀሙበትን ስልክ ቁጥር አስገቡ፡")
        context.user_data["sex"] = "ወንድ"
        return ASK_PLACE
    elif text == "ሴት":
        await update.message.reply_text("የምትጠቀሙበትን ስልክ ቁጥር አስገቡ፡")
        context.user_data["sex"] = "ሴት"
        return ASK_PLACE
    else:
        await update.message.reply_text("✋ከታች ከተቀመጡት ይምረጡ፡", reply_markup=reply_markup_sex)
        return ASK_SEX 

async def ask_place_handle_phone(update: Update, context: CallbackContext)-> int:
    context.user_data["ስልክ"] = update.message.text
    keyboard = [[area] for area in major_areas.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("የምትኖሩበትን ክፍለ ከተማ ምረጡ:", reply_markup=reply_markup)
    return ASK_SPECIFIC_AREA

async def ask_specific_area(update: Update, context: CallbackContext) -> int:
    selected_major_area = update.message.text
    if selected_major_area not in major_areas:
        await update.message.reply_text("✋ከተዘረዘሩት ውስጥ ይምረጡ፡")
        keyboard = [[area] for area in major_areas.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("የምትኖሩበትን ክፍለ ከተማ ምረጡ:", reply_markup=reply_markup)
        return ASK_SPECIFIC_AREA
    else:
        context.user_data["sub_city"] = selected_major_area  

        keyboard = [[area] for area in major_areas[selected_major_area]]
        keyboard.append(["✏️ከተዘረዘረው ውጪ", "Back"])  
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text("የምትኖሩበትን ሰፈር ምረጡ:", reply_markup=reply_markup)
        return HANDLE_PLACE


async def handle_place(update: Update, context: CallbackContext) -> int:
    chosen_place = update.message.text
    
    if chosen_place == "Back":
        keyboard = [[area] for area in major_areas.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("የምትኖሩበትን ክፍለ ከተማ ምረጡ:", reply_markup=reply_markup)
        return ASK_SPECIFIC_AREA  

    if chosen_place == "✏️ከተዘረዘረው ውጪ":
        await update.message.reply_text("የሰፈራችሁን ስም አስገቡ:")
        return SAVE_LOCATION  
    
    
    if chosen_place not in major_areas.get(context.user_data["sub_city"], []):
        await update.message.reply_text("✋ከተዘረዘሩት ውስጥ ይምረጡ፡")
        keyboard = [[area] for area in major_areas[context.user_data["sub_city"]]]
        keyboard.append(["✏️ከተዘረዘረው ውጪ", "Back"])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("የምትኖሩበትን ሰፈር ምረጡ:", reply_markup=reply_markup)
        return HANDLE_PLACE
    else:
        context.user_data["specific_area"] = chosen_place
        keyboard = [[InlineKeyboardButton(category, callback_data=f"cat_{category}")] for category in jobs.keys()]
        keyboard.append([InlineKeyboardButton("⬅️Back", callback_data="backtoplace")])
        await update.message.reply_text("የሙያ ዘርፍ ምረጡ:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ASK_JOB
    
async def back_to_place(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    await query.message.delete()

    keyboard = [[area] for area in major_areas.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await context.bot.send_message(chat_id=chat_id,text="የምትኖሩበትን ክፍለ ከተማ ምረጡ:", reply_markup=reply_markup)
    ##await query.edit_message_text("የምትኖሩበትን ክፍለ ከተማ ምረጡ:", reply_markup=reply_markup)
    return ASK_SPECIFIC_AREA  
    
async def save_location(update: Update, context: CallbackContext) -> int:
    context.user_data["specific_area"] = update.message.text 
    keyboard = [[InlineKeyboardButton(category, callback_data=f"cat_{category}")] for category in jobs.keys()]
    keyboard.append([InlineKeyboardButton("⬅️Back", callback_data="backtoplace")])
    await update.message.reply_text("የሙያ ዘርፍ ምረጡ:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_JOB

async def ask_jobs(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_selected_jobs[query.from_user.id] = []
    selected_category = query.data.split("_")[1]
    user_selected_jobs.setdefault(user_id, [])
    context.user_data["selected_category"] = selected_category
    await query.edit_message_text(
        text=f"በ {selected_category} ዘርፍ ውስጥ እስከ 3 የስራ አይነቶችን ይምረጡ:",
        reply_markup=generate_job_keyboard(selected_category, []))
    return SELECTED_JOBS
def generate_job_keyboard(category, selected_jobs):
    job_list = jobs[category]  
    keyboard = []
    for job in job_list:
        if job in selected_jobs:
            index = selected_jobs.index(job) + 1
            text = f"{index}. {job}" 
        else:
            text = job 
        keyboard.append([InlineKeyboardButton(text, callback_data=f"job_{job}")])
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

async def select_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    selected_job = query.data.split("_")[1]
    user_selected_jobs.setdefault(user_id, [])
    if selected_job in user_selected_jobs[user_id]:
        user_selected_jobs[user_id].remove(selected_job)  # Uncheck
    else:
        if len(user_selected_jobs[user_id]) < 3:
            user_selected_jobs[user_id].append(selected_job)  # Check
        else:
            await query.answer("You can only select up to 3 jobs.", show_alert=True)
            return SELECTED_JOBS 
    await query.edit_message_reply_markup(
        reply_markup=generate_job_keyboard(context.user_data["selected_category"], user_selected_jobs[user_id]))
    return SELECTED_JOBS

async def confirm_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    user_selected_jobs.setdefault(user_id, [])

    if not user_selected_jobs[user_id]:
        await query.answer("You must select at least one job.", show_alert=True)
        return SELECTED_JOBS
    selected_jobs = user_selected_jobs.get(user_id,[])
    job_list_str = "\n".join(f"🔹 {job}" for job in selected_jobs)
    user_data = {
        "name": context.user_data["name"],
        "sex": context.user_data["sex"],
        "phone": context.user_data["ስልክ"],
        "sub_city": context.user_data["sub_city"],
        "specific_area": context.user_data["specific_area"],
        "selected_category": context.user_data["selected_category"],
        "jobs": job_list_str,
        }
    db.collection("Workers").document(user_id).set(user_data)  # Save to Firebase

    # Send confirmation message
    confirm = (f"✅ ምዝገባው ተጠናቋል!\n" 
    f"📌 ስም: {user_data['name']}\n" 
    f"📌 ፆታ: {user_data['sex']}\n" 
    f"📌 ስልክ: {user_data['phone']}\n" 
    f"📌 ክፍለ_ከተማ?: {user_data['sub_city']}\n" 
    f"📌 ሰፈር: {user_data['specific_area']}\n"
    f"📌 የስራ_ዘርፍ?: {user_data['selected_category']}\n"
    f"📌 የሙያ_አይነቶች?: {job_list_str}\n")
    
    await query.message.reply_text(confirm, reply_markup=ReplyKeyboardRemove())
    await query.edit_message_reply_markup(reply_markup=None)
    await context.bot.send_message(chat_id=user_id, text = "⚠️የተሳሳተ መረጃ ከሞሉ እንደ አዲስ /start የሚለውን በመጫን ይሙሉ።\n\n"
    "⏰በሚፈለጉ ሰዓት ደውለን እናስቀጥሮታለን።")
    user_selected_jobs[user_id] = []

    return ConversationHandler.END

async def back_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    user_selected_jobs[user_id] = []
    keyboard = [[InlineKeyboardButton(category, callback_data=f"cat_{category}")] for category in jobs.keys()]
    keyboard.append([InlineKeyboardButton("⬅️Back", callback_data="backtoplace")])
    await query.edit_message_text("የሙያ ዘርፍ ምረጡ:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    return ASK_JOB

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END



def main():
    app = Application.builder().token(TOKEN).build()

    handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
             ASK_Name: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
             ASK_SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sex_handle_name)],
             ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone_handle_sex)],
             ASK_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_place_handle_phone)],
             ASK_SPECIFIC_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_specific_area)],
             HANDLE_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_place)],
             SAVE_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_location)],
            ASK_JOB: [
                    CallbackQueryHandler(ask_jobs, pattern="^cat_"),
                    CallbackQueryHandler(back_to_place, pattern="^backtoplace$")],
            SELECTED_JOBS: [ 
                    CallbackQueryHandler(select_job, pattern="^job_"),
                    CallbackQueryHandler(confirm_selection, pattern="^done$"),
                    CallbackQueryHandler(back_selection, pattern="^back$")
            ],


            }, fallbacks=[CommandHandler("cancel", cancel)],)
    app.add_handler(handler)
    
    app.run_polling()

    logging.info("Bot is running...")

if __name__ == '__main__':
    main()
    