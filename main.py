import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
import google.generativeai as genai
from aiohttp import web

# API kalitlar - Render Environment Variables orqali o'qiladi
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Google API bilan bog'lanish va modelni to'g'ri formatda sozlash
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name='gemini-1.5-flash')

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# --- RENDER BEPUL REJASI UCHUN KICHIK VEB SERVER ---
async def handle_root(request):
    return web.Response(text="Bot is running smoothly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

# --- AI LOGIKASI ---
async def process_photo_and_ask_ai(photo: types.PhotoSize, prompt: str):
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    image_data = await bot.download_file(file_path)
    image_bytes = image_data.read()

    system_instruction = (
        "Sen matematika va fizika fanlari bo'yicha professional o'qituvchisan. "
        "Foydalanuvchi yuborgan rasmdagi misol yoki masalani juda aniq, xatolarsiz va "
        "bosqichma-bosqich tushuntirib yechib ber. Formulalarni aniq ko'rsat."
    )

    contents = [
        system_instruction,
        prompt,
        {"mime_type": "image/jpeg", "data": image_bytes}
    ]
    response = model.generate_content(contents)
    return response.text

# --- HANDLERLAR ---
@dp.message(F.photo, lambda message: message.caption and message.caption.strip().startswith('/bot'))
async def handle_photo_with_caption(message: types.Message):
    await message.reply("📖 Rasmdagi misolni tahlil qilyapman, bir oz kuting...")
    photo = message.photo[-1]
    user_prompt = message.caption.replace('/bot', '').strip()
    if not user_prompt: user_prompt = "Ushbu rasmdagi masalani batafsil yechib ber."

    try:
        answer = await process_photo_and_ask_ai(photo, user_prompt)
        await message.reply(f"📈 **Yechim:**\n\n{answer}", parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"Xatolik yuz berdi: {e}")

@dp.message(lambda message: message.text and message.text.strip().startswith('/bot'))
async def handle_reply_to_photo(message: types.Message):
    if message.reply_to_message and message.reply_to_message.photo:
        await message.reply("🔍 Asl rasmni tekshiryapman, bir oz kuting...")
        photo = message.reply_to_message.photo[-1]
        user_prompt = message.text.replace('/bot', '').strip()
        if not user_prompt: user_prompt = "Ushbu rasmga javob qaytarib, undagi misolni batafsil yechib ber."

        try:
            answer = await process_photo_and_ask_ai(photo, user_prompt)
            await message.reply(f"📈 **Yechim:**\n\n{answer}", parse_mode="Markdown")
        except Exception as e:
            await message.reply(f"Xatolik yuz berdi: {e}")
    else:
        user_prompt = message.text.replace('/bot', '').strip()
        if user_prompt:
            await message.reply("🧠 Savolingizni o'ylayapman...")
            try:
                response = model.generate_content(user_prompt)
                await message.reply(f"💡 **Javob:**\n\n{response.text}", parse_mode="Markdown")
            except Exception as e:
                await message.reply(f"Xatolik: {e}")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
