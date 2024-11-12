import logging
import sqlite3
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Стан діалогу
CAR_BRAND, CAR_MODEL, CAR_PRICE, CAR_YEAR, CAR_DESCRIPTION, CAR_PHONE, CAR_PHOTO, DELETE_ID = range(8)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Вітаємо! Використайте команду /add для додавання оголошення або /delete для видалення оголошення.")
    return ConversationHandler.END

def add_car(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Введіть марку автомобіля:")
    return CAR_BRAND

def receive_brand(update: Update, context: CallbackContext) -> int:
    context.user_data['brand'] = update.message.text
    update.message.reply_text("Введіть модель автомобіля:")
    return CAR_MODEL

def receive_model(update: Update, context: CallbackContext) -> int:
    context.user_data['model'] = update.message.text
    update.message.reply_text("Введіть ціну автомобіля:")
    return CAR_PRICE

def receive_price(update: Update, context: CallbackContext) -> int:
    context.user_data['price'] = update.message.text
    update.message.reply_text("Введіть рік випуску автомобіля:")
    return CAR_YEAR

def receive_year(update: Update, context: CallbackContext) -> int:
    context.user_data['year'] = update.message.text
    update.message.reply_text("Додайте короткий опис:")
    return CAR_DESCRIPTION

def receive_description(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text
    update.message.reply_text("Введіть номер телефону:")
    return CAR_PHONE

def receive_phone(update: Update, context: CallbackContext) -> int:
    context.user_data['phone'] = update.message.text
    update.message.reply_text("Надішліть фото автомобіля або надішліть /skip, щоб пропустити.")
    return CAR_PHOTO

def receive_photo(update: Update, context: CallbackContext) -> int:
    context.user_data['photo'] = update.message.photo[-1].file_id  # Отримуємо ID фото
    save_car_to_db(context)
    update.message.reply_text("Оголошення успішно створено!")
    return ConversationHandler.END

def skip_photo(update: Update, context: CallbackContext) -> int:
    save_car_to_db(context)
    update.message.reply_text("Оголошення успішно створено!")
    return ConversationHandler.END

def save_car_to_db(context: CallbackContext):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    
    # Збереження даних автомобіля
    cursor.execute("INSERT INTO cars (brand, model, price, year, description, phone, photo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (context.user_data['brand'],
                    context.user_data['model'],
                    context.user_data['price'],
                    context.user_data['year'],
                    context.user_data['description'],
                    context.user_data['phone'],
                    context.user_data.get('photo')))  # Використовуємо get, щоб уникнути KeyError
    conn.commit()
    conn.close()

def list_cars(update: Update, context: CallbackContext) -> None:
    logger.info("Отримую список автомобілів...")
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, brand, model, price, year, description, phone, photo FROM cars")  # Додаємо поле photo
    
    cars = cursor.fetchall()
    conn.close()

    if not cars:
        update.message.reply_text("Оголошень немає.")
        logger.info("Оголошень немає.")
        return

    for car in cars:
        rowid, brand, model, price, year, description, phone, photo_id = car
        message = (f"ID: {rowid}\nМарка: {brand}, Модель: {model}, Ціна: {price}, "
                   f"Рік: {year}, Опис: {description}, Телефон: {phone}\n")
        update.message.reply_text(message)
        if photo_id:  # Якщо є фото, відправляємо його
            update.message.reply_photo(photo_id)

    logger.info("Список автомобілів успішно надіслано.")

def delete_car(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Введіть ID оголошення, яке ви хочете видалити:")
    return DELETE_ID

def confirm_delete(update: Update, context: CallbackContext) -> int:
    car_id = update.message.text
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM cars WHERE rowid=?", (car_id,))
    conn.commit()
    
    if cursor.rowcount > 0:
        update.message.reply_text(f"Оголошення з ID {car_id} успішно видалено.")
    else:
        update.message.reply_text(f"Оголошення з ID {car_id} не знайдено.")

    conn.close()
    return ConversationHandler.END

def main() -> None:
    # Запускаємо бота
    updater = Updater("7920334981:AAHZJONiHGhn5rpa9eicwEufq13NYOc5D0I")

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_car), CommandHandler('delete', delete_car)],
        states={
            CAR_BRAND: [MessageHandler(Filters.text & ~Filters.command, receive_brand)],
            CAR_MODEL: [MessageHandler(Filters.text & ~Filters.command, receive_model)],
            CAR_PRICE: [MessageHandler(Filters.text & ~Filters.command, receive_price)],
            CAR_YEAR: [MessageHandler(Filters.text & ~Filters.command, receive_year)],
            CAR_DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, receive_description)],
            CAR_PHONE: [MessageHandler(Filters.text & ~Filters.command, receive_phone)],
            CAR_PHOTO: [
                MessageHandler(Filters.photo, receive_photo),
                CommandHandler('skip', skip_photo)  # Можливість пропустити фото
            ],
            DELETE_ID: [MessageHandler(Filters.text & ~Filters.command, confirm_delete)],
        },
        fallbacks=[CommandHandler('list', list_cars)],  # Додайте обробник для команди /list
    )

    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('list', list_cars))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()