import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
import google.generativeai as genai

# API kalitlarni bevosita kodga yozmaymiz, Render muhitidan xavfsiz oqib olamiz
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# AI modelini sozlash (Gemini 1.5 Flash - tez va aniq ishlaydi)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Rasmni yuklab olish va AI ga yuborish funksiyasi
async def process_photo_and_ask_ai(photo: types.PhotoSize, prompt: str):
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    
    # Rasmni vaqtincha xotiraga yuklash
    image_data = await bot.download_file(file_path)
    image_bytes = image_data.read()

    # AI ga ko'rsatma: Aniq fanlar uchun maxsus prompt
    system_instruction = (
        "Sen matematika va fizika fanlari bo'yicha professional o'qituvchisan. "
        "Foydalanuvchi yuborgan rasmdagi misol yoki masalani juda aniq, xatolarsiz va "
        "bosqichma-bosqich (step-by-step) tushuntirib yechib ber. Formulalarni aniq ko'rsat."
    )

    contents = [
        system_instruction,
        prompt,
        {"mime_type": "image/jpeg", "data": image_bytes}
    ]
    
    response = model.generate_content(contents)
    return response.text

# --- HANDLERLAR ---

# 1. Rasm yuborilganda va izohiga /bot deb yozilganda
@dp.message(F.photo, lambda message: message.caption and message.caption.strip().startswith('/bot'))
async def handle_photo_with_caption(message: types.Message):
    await message.reply("📖 Rasmdagi misolni tahlil qilyapman, bir oz kuting...")
    
    photo = message.photo[-1]
    user_prompt = message.caption.replace('/bot', '').strip()
    if not user_prompt: 
        user_prompt = "Ushbu rasmdagi matematik/fizik masalani batafsil yechib ber."

    try:
        answer = await process_photo_and_ask_ai(photo, user_prompt)
        await message.reply(f"📈 **Yechim:**\n\n{answer}", parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"Xatolik yuz berdi: {e}\nKalitlar to'g'ri sozlanganini tekshiring.")

# 2. Guruhda biror rasmga javob (reply) tarzida /bot deb yozilganda
@dp.message(lambda message: message.text and message.text.strip().startswith('/bot'))
async def handle_reply_to_photo(message: types.Message):
    if message.reply_to_message and message.reply_to_message.photo:
        await message.reply("🔍 Asl rasmni tekshiryapman, bir oz kuting...")
        
        photo = message.reply_to_message.photo[-1]
        user_prompt = message.text.replace('/bot', '').strip()
        if not user_prompt: 
            user_prompt = "Ushbu rasmga javob qaytarib, undagi misolni batafsil yechib ber."

        try:
            answer = await process_photo_and_ask_ai(photo, user_prompt)
            await message.reply(f"📈 **Yechim:**\n\n{answer}", parse_mode="Markdown")
        except Exception as e:
            await message.reply(f"Xatolik yuz berdi: {e}")
    else:
        # Shunchaki matnli xabar yozilganda (Ramsiz)
        user_prompt = message.text.replace('/bot', '').strip()
        if user_prompt:
            await message.reply("🧠 Savolingizni o'ylayapman...")
            try:
                response = model.generate_content(user_prompt)
                await message.reply(f"💡 **Javob:**\n\n{response.text}", parse_mode="Markdown")
            except Exception as e:
                await message.reply(f"Xatolik: {e}")

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
