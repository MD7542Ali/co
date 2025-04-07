# fullbot.py
import logging, stripe, random, re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ========== CONFIG ==========
OWNER_ID = 930577300
BOT_TOKEN = "7964928255:AAFOsLr9zDbLQXoZMxrhFzd54uJEzgd33QE"
STRIPE_API_KEY = "sk_test_51RB9omPrntIzgnG70QJ0bIqdGMGU7rOWsKlTrTUCJxYrS7j8BN1kUA3fhcbjEEDVa5xUTnyKpk7gbfLRhmCowBqH00uVirKqX6"

stripe.api_key = STRIPE_API_KEY
approved_users = set([OWNER_ID])
redeem_keys = {}

# ========== LOGGING ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ACCESS UTILS ==========
def is_owner(uid): return uid == OWNER_ID
def is_approved(uid): return uid in approved_users

# ========== COMMANDS ==========

def start(update: Update, context: CallbackContext):
    update.message.reply_text("PYSCHO — Use /help to see all commands.")

def help_command(update: Update, context: CallbackContext):
    help_text = """❓ Help - Command List ❓

🌟 General Commands 🌟
🚀 /start - Greet me and get started!
✅ /check <card> - Check a single card
🔍 /mcheck <cards> - Check multiple cards (max 1000)
💳 /s1 <card> - Check a single card (Stripe $1)
💳 /ms1 <cards> - Check multiple cards (Stripe $1)
🎲 /gen <BIN> or <BIN>|<MM>|<YY>|<CVV> - Generate credit cards
ℹ️ /bin <BIN> - Get BIN information
🏠 /address <countrycode> - Generate a random address
🔑 /redeem <code> - Redeem a code for access
💰 /plan - View pricing plans
❓ /help - Show this command list
📤 Send .txt - Check cards from file

🔒 Admin Only 🔒
👥 /userlist - List approved users
🎟️ /generate - Generate a redeem code
✅ /approve <userid> - Approve a user
❌ /remove <userid> - Remove a user
📢 /broadcast <message> - Broadcast to all users
🔐 /keylist - Show active keys
🗑️ /rmkey <key> - Remove redeem key
"""
    update.message.reply_text(help_text)

def redeem(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not context.args: return update.message.reply_text("Usage: /redeem <code>")
    code = context.args[0]
    if code in redeem_keys:
        approved_users.add(user_id)
        del redeem_keys[code]
        update.message.reply_text("✅ Access granted.")
    else:
        update.message.reply_text("❌ Invalid code.")

# ========== STRIPE CHARGE ==========
def s1(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    if not is_approved(uid): return update.message.reply_text("❌ Access denied.")
    if not context.args: return update.message.reply_text("Usage: /s1 <cc|mm|yy|cvv>")

    cc = context.args[0]
    parts = cc.split('|')
    if len(parts) != 4: return update.message.reply_text("❌ Invalid format. Use cc|mm|yy|cvv")
    number, mm, yy, cvv = parts

    try:
        token = stripe.Token.create(card={
            "number": number,
            "exp_month": int(mm),
            "exp_year": int(yy),
            "cvc": cvv,
        })
        charge = stripe.Charge.create(
            amount=100,
            currency="usd",
            source=token.id,
            description="PYSCHO - Stripe $1 Auth",
            capture=False
        )
        msg = f"{cc} - ✅ Approved (Status: {charge['status']})" if charge['status'] == 'succeeded' else f"{cc} - ❌ Declined (Status: {charge['status']})"
        update.message.reply_text(msg)
    except stripe.error.CardError as e:
        update.message.reply_text(f"{cc} - ❌ Declined: {e.user_message}")
    except Exception as e:
        update.message.reply_text(f"{cc} - ❌ Error: {str(e)}")

def ms1(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    if not is_approved(uid): return update.message.reply_text("❌ Access denied.")
    if not context.args: return update.message.reply_text("Usage: /ms1 <ccs>")

    cards = ' '.join(context.args).split()
    responses = []
    for cc in cards[:1000]:
        try:
            number, mm, yy, cvv = cc.split('|')
            token = stripe.Token.create(card={
                "number": number,
                "exp_month": int(mm),
                "exp_year": int(yy),
                "cvc": cvv,
            })
            charge = stripe.Charge.create(
                amount=100,
                currency="usd",
                source=token.id,
                description="PYSCHO - Stripe $1 Auth",
                capture=False
            )
            status = charge['status']
            msg = f"{cc} - ✅ Approved" if status == 'succeeded' else f"{cc} - ❌ Declined"
        except stripe.error.CardError as e:
            msg = f"{cc} - ❌ {e.user_message}"
        except Exception as e:
            msg = f"{cc} - ❌ Error"
        responses.append(msg)

    # Telegram message limit: 40 lines
    for i in range(0, len(responses), 40):
        update.message.reply_text("\n".join(responses[i:i+40]))

# ========== ADMIN COMMANDS ==========
def generate(update: Update, context: CallbackContext):
    if not is_owner(update.effective_user.id): return
    key = ''.join(random.choices('ABCDEFGH0123456789', k=10))
    redeem_keys[key] = True
    update.message.reply_text(f"🎟️ Code: `{key}`", parse_mode='Markdown')

def approve(update: Update, context: CallbackContext):
    if not is_owner(update.effective_user.id): return
    if not context.args: return update.message.reply_text("Usage: /approve <user_id>")
    uid = int(context.args[0])
    approved_users.add(uid)
    update.message.reply_text(f"✅ User {uid} approved.")

def remove(update: Update, context: CallbackContext):
    if not is_owner(update.effective_user.id): return
    if not context.args: return update.message.reply_text("Usage: /remove <user_id>")
    uid = int(context.args[0])
    approved_users.discard(uid)
    update.message.reply_text(f"❌ User {uid} removed.")

def userlist(update: Update, context: CallbackContext):
    if not is_owner(update.effective_user.id): return
    update.message.reply_text("Approved Users:\n" + "\n".join(str(u) for u in approved_users))

def keylist(update: Update, context: CallbackContext):
    if not is_owner(update.effective_user.id): return
    if not redeem_keys:
        update.message.reply_text("No active keys.")
    else:
        update.message.reply_text("Active Keys:\n" + "\n".join(redeem_keys.keys()))

def rmkey(update: Update, context: CallbackContext):
    if not is_owner(update.effective_user.id): return
    if not context.args: return update.message.reply_text("Usage: /rmkey <key>")
    key = context.args[0]
    if key in redeem_keys:
        del redeem_keys[key]
        update.message.reply_text("Key removed.")
    else:
        update.message.reply_text("Key not found.")

def broadcast(update: Update, context: CallbackContext):
    if not is_owner(update.effective_user.id): return
    msg = " ".join(context.args)
    for uid in approved_users:
        try:
            context.bot.send_message(chat_id=uid, text=f"[Broadcast] {msg}")
        except: pass
    update.message.reply_text("Broadcast sent.")

# ========== MAIN ==========
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("redeem", redeem))
    dp.add_handler(CommandHandler("s1", s1))
    dp.add_handler(CommandHandler("ms1", ms1))
    dp.add_handler(CommandHandler("generate", generate))
    dp.add_handler(CommandHandler("approve", approve))
    dp.add_handler(CommandHandler("remove", remove))
    dp.add_handler(CommandHandler("userlist", userlist))
    dp.add_handler(CommandHandler("keylist", keylist))
    dp.add_handler(CommandHandler("rmkey", rmkey))
    dp.add_handler(CommandHandler("broadcast", broadcast))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()