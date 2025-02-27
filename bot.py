import asyncio
import requests
import subprocess
from aiogram import Bot, Dispatcher, executor, types

# Конфигурация
TELEGRAM_TOKEN = "ВАШ_ТОКЕН_ТЕЛЕГРАМ_БОТА"
THREE_X_UI_URL = "http://ВАШ_СЕРВЕР:PORT/api"  # Замените на URL вашей панели
API_KEY = "ВАШ_API_КЛЮЧ_3X_UI"

# Создание экземпляров бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Функция для создания пользователя в 3x-ui
async def create_user(username, password):
    url = f"{THREE_X_UI_URL}/users"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "username": username,
        "password": password,
        "method": "vmess",  # Можно выбрать другой метод (vless, trojan и т.д.)
        "protocol": "tcp",
        "network": "ws",
        "host": "",
        "path": "/",
        "tls": "none"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                return True, await response.json()
            else:
                return False, await response.text()

# Функция для открытия порта в UFW
async def open_port_in_ufw(port):
    try:
        process = await asyncio.create_subprocess_exec(
            "sudo", "ufw", "allow", str(port),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return True, stdout.decode().strip()
        else:
            return False, stderr.decode().strip()
    except Exception as e:
        return False, str(e)

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("Привет! Отправьте команду /create [имя] [пароль], чтобы создать подключение.")

# Обработчик команды /create
@dp.message_handler(commands=["create"])
async def create(message: types.Message):
    args = message.get_args().split()
    if len(args) != 2:
        await message.reply("Использование: /create [имя] [пароль]")
        return

    username, password = args[0], args[1]
    success, result = await create_user(username, password)

    if success:
        port = result.get("port")  # Убедитесь, что ключ "port" существует в ответе
        if not port:
            await message.reply("Ошибка: не удалось получить порт пользователя.")
            return

        ufw_success, ufw_message = await open_port_in_ufw(port)
        if ufw_success:
            await message.reply(f"Подключение успешно создано!\n\nИмя: {username}\nПароль: {password}\nПорт: {port}\n\nПорт открыт в UFW.")
        else:
            await message.reply(f"Подключение создано, но не удалось открыть порт в UFW: {ufw_message}")
    else:
        await message.reply(f"Ошибка при создании подключения: {result}")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)