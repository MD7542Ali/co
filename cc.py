import telebot
import stripe
import random

# === CONFIGURATION ===
stripe.api_key = 'sk_test_51RB9omPrntIzgnG70QJ0bIqdGMGU7rOWsKlTrTUCJxYrS7j8BN1kUA3fhcbjEEDVa5xUTnyKpk7gbfLRhmCowBqH00uVirKqX6'  # Replace this
bot = telebot.TeleBot('7964928255:AAFOsLr9zDbLQXoZMxrhFzd54uJEzgd33QE')  # Replace this
OWNER_ID = 930577300  # Your Telegram user ID

# === DATA ===
us_states = [
    ("New York", "NY", "10001"),
    ("Los Angeles", "CA", "90001"),
    ("Houston", "TX", "77001"),
    ("Chicago", "IL", "60601"),
    ("Phoenix", "AZ", "85001"),
    ("Miami", "FL", "33101"),
    ("Denver", "CO", "80201"),
    ("Seattle", "WA", "98101")
]

first_names = ["John", "Mike", "Anna", "Emily", "Chris", "Sarah", "David", "Laura"]
last_names = ["Smith", "Johnson", "Brown", "Garcia", "Martinez", "Miller", "Davis"]

# === FUNCTIONS ===
def generate_address():
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    street = f"{random.randint(100,9999)} {random.choice(['Main St', '2nd St', 'Maple Ave', 'Broadway'])}"
    city, state, zip_code = random.choice(us_states)
    return f"{name}\n{street}\n{city}, {state} {zip_code}\nUnited States"

def generate_cc(bin_format, amount):
    cards = []
    for _ in range(int(amount)):
        cc = ""
        for char in bin_format:
            cc += str(random.randint(0, 9)) if char == "x" else char
        mm = str(random.randint(1, 12)).zfill(2)
        yy = str(random.randint(26, 29))
        cvv = str(random.randint(100, 999))
        cards.append(f"{cc}|{mm}|20{yy}|{cvv}")
    return cards

def check_cc(card):
    try:
        cc, mm, yy, cvv = card.strip().split("|")
        pm = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": cc,
                "exp_month": int(mm),
                "exp_year": int(yy),
                "cvc": cvv,
            },
        )
        customer = stripe.Customer.create(payment_method=pm.id)
        stripe.PaymentIntent.create(
            amount=100,
            currency='usd',
            customer=customer.id,
            payment_method=pm.id,
            off_session=True,
            confirm=True,
        )
        return f"✅ Approved | {cc}|{mm}|{yy}|{cvv}"
    except stripe.error.CardError:
        return f"❌ Declined | {cc}|{mm}|{yy}|{cvv}"
    except Exception:
        return f"❌ Declined | {cc}|{mm}|{yy}|{cvv}"

# === BOT COMMANDS ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, (
        "Welcome to Real CC Checker Bot.\n\n"
        "Commands:\n"
        "/chk <cc>\n"
        "/mchk\n"
        "/ch <cc>\n"
        "/gen <bin> <amount>\n"
        "/genaddress"
    ))

@bot.message_handler(commands=['chk'])
def single_check(message):
    try:
        card = message.text.split(" ", 1)[1]
        result = check_cc(card)
        bot.reply_to(message, result)
    except:
        bot.reply_to(message, "Format: /chk 4242424242424242|12|2025|123")

@bot.message_handler(commands=['mchk'])
def multi_check(message):
    try:
        cards = message.text.split("\n")[1:]
        for cc in cards:
            result = check_cc(cc)
            bot.send_message(message.chat.id, result)
    except:
        bot.reply_to(message, "Usage:\n/mchk\ncard1|mm|yy|cvv\ncard2|mm|yy|cvv")

@bot.message_handler(commands=['ch'])
def charge_card(message):
    if message.from_user.id != OWNER_ID:
        return bot.reply_to(message, "Unauthorized.")
    try:
        card = message.text.split(" ", 1)[1]
        result = check_cc(card)
        bot.reply_to(message, result)
    except:
        bot.reply_to(message, "Format: /ch 4242424242424242|12|2025|123")

@bot.message_handler(commands=['gen'])
def generate_bins(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            return bot.reply_to(message, "Usage: /gen <bin> <amount>\nExample: /gen 440644xxxxxxxxxx 5")
        bin_pattern = args[1]
        quantity = args[2]
        cards = generate_cc(bin_pattern, quantity)
        bot.reply_to(message, "\n".join(cards[:20]))
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['genaddress'])
def send_address(message):
    addr = generate_address()
    bot.reply_to(message, f"Random Billing Address:\n\n{addr}")

# === START BOT ===
bot.infinity_polling()