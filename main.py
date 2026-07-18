import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
import google.generativeai as genai
from aiohttp import web
from concurrent.futures import ThreadPoolExecutor

# API kalitlar - Render Environment Variables orqali o'qiladi
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Kalitlarni tekshirish
if not TELEGRAM_BOT_TOKEN or not GOOGLE_API_KEY:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN yoki GOOGLE_API_KEY sozlangan emas!")

# API sozlash
genai.configure(api_key=GOOGLE_API_KEY)

# MUHIM: Eng yangi va tezkor modelga o'tamiz
model = genai.GenerativeModel('gemini-2.0-flash')
executor = ThreadPoolExecutor(max_workers=3)

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

# --- HANDLERLAR ---
@dp.message(lambda message: message.text and message.text.strip().startswith('/bot'))
async def handle_group_text(message: types.Message):
    user_prompt = message.text.replace('/bot', '').strip()
    
    if not user_prompt:
        await message.reply("💡 Salom! Matematika yoki fizikaga oid savolingizni `/bot [savol]` ko'rinishida yozing.")
        return

    await message.reply("🧠 Savolingizni o'ylayapman, bir oz kuting...")
    
    try:
        # Blocking amaliyotni async qilish
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            executor,
            lambda: model.generate_content(
                f"Sen matematika va fizika fanlari o'qituvchisan. Quyidagi savolga aniq va bosqichma-bosqich javob ber: {user_prompt}"
            )
        )
        
        # Uzun javoblarni bo'limlash (Telegram 4096 belgi chegarasi)
        response_text = response.text
        if len(response_text) > 4096:
            for i in range(0, len(response_text), 4096):
                await message.reply(f"💡 **Javob ({i//4096 + 1}):**\n\n{response_text[i:i+4096]}")
        else:
            await message.reply(f"💡 **Javob:**\n\n{response_text}")
            
    except Exception as e:
        await message.reply(f"❌ Xatolik yuz berdi:\n`{str(e)}`")

# Rasm bilan ishlaydigan handler
@dp.message(F.photo)
async def handle_photo_info(message: types.Message):
    if message.caption and message.caption.strip().startswith('/bot'):
        await message.reply("⚠️ Hozircha modelni matn rejimiga o'tkazdik. Iltimos, savolingizni rasmda emas, matn ko'rinishida yo'zib ko'ring.")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
