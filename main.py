import re
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# تنظیمات اولیه
TOKEN = "7958499921:AAGkIgzDpjxGZUCYCn65HZmPVRPnUOWvV80"  # توکن رباتت
DEFAULT_LINK = "@NinjaMovieee⛩"  # لینک کانالت
PASSWORD = "Mehrshad01A"  # رمز ورود به ربات
ADMIN_ID = 7484975104  # آیدی ادمین

# تنظیم لاگ برای ثبت فعالیت‌ها
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# الگوی استیکر و لینک
STICKER_PATTERN = r'[\U0001F300-\U0001F9FF\U0001F000-\U0001F0FF\U00002600-\U000026FF\U00002700-\U000027BF]'
EXCEPTED_STICKERS = {"⛩"}  # استیکرهای مجاز
CHANNEL_PATTERN = r'(@\w+)'  # الگوی شناسایی لینک‌های کانال

# ذخیره و بارگذاری داده‌ها
def save_data(context):
    data = {
        "authorized_users": list(context.bot_data.get('authorized_users', set())),
        "banned_users": list(context.bot_data.get('banned_users', set())),
    }
    try:
        with open("bot_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def load_data(context):
    try:
        with open("bot_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            context.bot_data['authorized_users'] = set(map(int, data.get('authorized_users', [])))
            context.bot_data['banned_users'] = set(map(int, data.get('banned_users', [])))
    except FileNotFoundError:
        context.bot_data['authorized_users'] = set()
        context.bot_data['banned_users'] = set()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        context.bot_data['authorized_users'] = set()
        context.bot_data['banned_users'] = set()

# دستور شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    logger.info(f"User {user_id} started the bot.")
    
    # بارگذاری داده‌ها
    load_data(context)
    
    # چک کردن بن شدن
    if user_id in context.bot_data.get('banned_users', set()):
        await update.message.reply_text("🚫 شما بن شدید و نمی‌تونید از ربات استفاده کنید!")
        return
    
    # دکمه‌های تعاملی
    keyboard = [
        [InlineKeyboardButton("📩 فوروارد پیام", callback_data="forward_message")],
        [InlineKeyboardButton("🌟 کانالم", url="https://t.me/NinjaMovieee")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # چک کردن دسترسی
    if user_id not in context.bot_data.get('authorized_users', set()):
        await update.message.reply_text(
            "🔒 لطفاً رمز ورود رو وارد کن:\n💡 رمز رو فقط یه بار باید وارد کنی!",
            reply_markup=reply_markup
        )
        context.user_data['awaiting_password'] = True
        return
    
    await update.message.reply_text(
        f"🎬✨ سلام {user_name} عزیز! به ربات نینجا مووی خوش اومدی! 🚀\n📩 لطفاً پیام خود را فوروارد کنید تا پردازش شود!",
        reply_markup=reply_markup
    )

# مدیریت دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "forward_message":
        await query.message.reply_text("📩 لطفاً پیام خود را فوروارد کنید تا پردازش شود!")

# مدیریت رمز ورود
async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if context.user_data.get('awaiting_password', False):
        if update.message.text == PASSWORD:
            context.bot_data.setdefault('authorized_users', set()).add(user_id)
            context.user_data['awaiting_password'] = False
            save_data(context)
            logger.info(f"User {user_id} authorized successfully.")
            await update.message.reply_text("✅ رمز درست بود! حالا می‌تونی از ربات استفاده کنی! 🎉")
            keyboard = [
                [InlineKeyboardButton("📩 فوروارد پیام", callback_data="forward_message")],
                [InlineKeyboardButton("🌟 کانالم", url="https://t.me/NinjaMovieee")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "📩 لطفاً پیام خود را فوروارد کنید تا پردازش شود!",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ رمز اشتباهه! دوباره امتحان کن: 🔒")
    else:
        await process_message(update, context)

# تابع برای جایگزینی لینک‌های کانال و حفظ استیکرهای مجاز
def clean_caption(caption, link):
    if not caption:
        return caption
    
    lines = caption.split('\n')
    new_lines = []
    
    for line in lines:
        if re.search(CHANNEL_PATTERN, line):
            pattern = rf'({STICKER_PATTERN}*)\s*(@\w+)({ "|".join(map(re.escape, EXCEPTED_STICKERS)) if EXCEPTED_STICKERS else ""})?\s*({STICKER_PATTERN}*)'
            match = re.search(pattern, line)
            if match:
                excepted_sticker = match.group(3)
                if excepted_sticker:
                    new_line = f"{link}{excepted_sticker}"
                else:
                    new_line = link
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            if re.match(rf'^{STICKER_PATTERN}+\s*$', line) and not any(sticker in line for sticker in EXCEPTED_STICKERS):
                continue
            new_lines.append(line)
    
    return '\n'.join(new_lines) if new_lines else caption

# تابع برای تبدیل entities به فرمت HTML
def entities_to_html(text, entities):
    if not text or not entities:
        return text
    
    offsets = []
    for entity in entities:
        start = entity.offset
        end = start + entity.length
        if start >= len(text) or end > len(text):
            continue
        if entity.type == MessageEntity.TEXT_LINK:
            offsets.append((start, f'<a href="{entity.url}">'))
            offsets.append((end, '</a>'))
        elif entity.type == MessageEntity.BOLD:
            offsets.append((start, '<b>'))
            offsets.append((end, '</b>'))
        elif entity.type == MessageEntity.ITALIC:
            offsets.append((start, '<i>'))
            offsets.append((end, '</i>'))
    
    offsets.sort(key=lambda x: (x[0], -1 if x[1].startswith('</') else 1))
    
    result = []
    last_pos = 0
    for offset, tag in offsets:
        if offset > len(text):
            continue
        result.append(text[last_pos:offset])
        result.append(tag)
        last_pos = offset
    result.append(text[last_pos:])
    
    return ''.join(result)

# پردازش پیام‌ها
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id in context.bot_data.get('banned_users', set()):
        await update.message.reply_text("🚫 شما بن شدید و نمی‌تونید از ربات استفاده کنید!")
        return
    
    if user_id not in context.bot_data.get('authorized_users', set()):
        await update.message.reply_text("🔒 لطفاً رمز ورود رو وارد کن:\n💡 رمز رو فقط یه بار باید وارد کنی!")
        context.user_data['awaiting_password'] = True
        return
    
    message = update.message
    if not message.text and not message.caption and not message.photo and not message.video and not message.document:
        await update.message.reply_text("⚠️ پیامت محتوا نداره! یه پیام دیگه فوروارد کن.")
        return
    
    caption = message.caption if message.caption else message.text if message.text else ""
    entities = message.caption_entities if message.caption else message.entities if message.text else []
    
    cleaned_caption = clean_caption(caption, DEFAULT_LINK)
    
    try:
        html_caption = entities_to_html(cleaned_caption, entities)
        parse_mode = ParseMode.HTML
        final_caption = html_caption
    except Exception as e:
        logger.error(f"Error in entities_to_html: {e}")
        parse_mode = None
        final_caption = cleaned_caption
    
    # دکمه‌های تعاملی
    keyboard = [
        [InlineKeyboardButton("🌟 برو به کانالم", url="https://t.me/NinjaMovieee")],
        [InlineKeyboardButton("📩 اشتراک‌گذاری", switch_inline_query=final_caption)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if message.photo:
            await update.message.reply_photo(
                photo=message.photo[-1].file_id,
                caption=final_caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        elif message.video:
            await update.message.reply_video(
                video=message.video.file_id,
                caption=final_caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        elif message.document:
            await update.message.reply_document(
                document=message.document.file_id,
                caption=final_caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                final_caption,
                parse_mode=parse_mode,
                disable_web_page_preview=False,
                reply_markup=reply_markup
            )
        await update.message.reply_text(
            f"🎉✨ پیامت با موفقیت اصلاح شد! 🚀\nحتماً به کانالم سر بزن: {DEFAULT_LINK} 🌟"
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        if message.photo:
            await update.message.reply_photo(
                photo=message.photo[-1].file_id,
                caption=cleaned_caption,
                reply_markup=reply_markup
            )
        elif message.video:
            await update.message.reply_video(
                video=message.video.file_id,
                caption=cleaned_caption,
                reply_markup=reply_markup
            )
        elif message.document:
            await update.message.reply_document(
                document=message.document.file_id,
                caption=cleaned_caption,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                cleaned_caption,
                disable_web_page_preview=False,
                reply_markup=reply_markup
            )
        await update.message.reply_text(
            f"🎉✨ پیامت با موفقیت اصلاح شد! 🚀\nحتماً به کانالم سر بزن: {DEFAULT_LINK} 🌟"
        )

# دستور بن کردن کاربر (فقط برای ادمین)
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 شما ادمین نیستید!")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ لطفاً آیدی کاربر رو وارد کن!\nمثال: /ban 123456789")
        return
    
    try:
        target_id = int(context.args[0])
        context.bot_data.setdefault('banned_users', set()).add(target_id)
        save_data(context)
        await update.message.reply_text(f"🚫 کاربر {target_id} بن شد!")
    except ValueError:
        await update.message.reply_text("⚠️ آیدی نامعتبره! یه عدد وارد کن.")

# تابع اصلی
def main():
    try:
        application = Application.builder().token(TOKEN).build()
        
        # دستورات
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("ban", ban))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # پردازش پیام‌ها
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_password))
        
        # شروع ربات
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"Error starting bot: {e}")

if __name__ == '__main__':
    main()
