#!/usr/bin/python

from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram import Update
import json
import os

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id, "Enter password with: /pw <password>")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id, "Enter password with: /pw <password>\nAfterwards you can send images will appear in my livingroom")

async def pw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id = update.effective_chat.id
    pwResponse = update.message.text.split()

    if id in userConfig["AUTH_USERS"]:
        await context.bot.sendMessage(id, "You are already logged in. If you need futher help try /help")
        return

    if len(pwResponse) != 2:
        context.bot.sendMessage(id, "Enter password with: /pw <password>")
    else:
        if pwResponse[1] != config["PASSWORD"]:
            for user in userConfig["BLOCKED_USERS"]:
                if id in user:
                    if (user[1]-1) > 0:
                        user[1] = user[1]-1
                        await context.bot.sendMessage(id, 'Wrong password. ' + f'{user[1]}' + ' tries remaining')
                    else:
                        user[1] = 0
                        await context.bot.sendMessage(id, "Too many tries. Your account is blocked")
                    with open("./user.json", "w") as outFile:
                        json.dump(userConfig, outFile)
                    return

            userConfig["BLOCKED_USERS"].append([id, config["LOGIN_TRIES"] - 1])
            await context.bot.sendMessage(id, 'Wrong password. ' + f'{config["LOGIN_TRIES"] - 1}' + ' tries remaining')
            with open("./user.json", "w") as outFile:
                json.dump(userConfig, outFile)

        else:
            for user in userConfig["BLOCKED_USERS"]:
                if id in user:
                    if user[1] <= 0:
                        await context.bot.sendMessage(id, "Too many tries. Your account is blocked")
                        return
                    else:
                        userConfig["BLOCKED_USERS"].remove(user)
            userConfig["AUTH_USERS"].append(id)
            await context.bot.sendMessage(id, "Yay")
            with open("./user.json", "w") as outFile:
                json.dump(userConfig, outFile)

async def attachment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id = update.effective_chat.id
    if id not in userConfig["AUTH_USERS"]:
        await context.bot.sendMessage(id, "Enter password with: /pw <password>")
        return

    #Check download path and number of files in it
    if not os.path.exists(config["DEFAULT_PATH"]):
        os.mkdir(config["DEFAULT_PATH"])
    fileName = str(len(os.listdir(config["DEFAULT_PATH"])))

    attachment = update.message.effective_attachment
    if isinstance(attachment, list):
        #compressed photo/as a list
        newFile = await attachment[-1].get_file()
        await newFile.download(config["DEFAULT_PATH"] + '/' + fileName + '.jpeg')
        await context.bot.sendMessage(id, "Thank you <3")
    else:
        #"normal" document
        if hasattr(attachment, "emoji"):
            await context.bot.sendMessage(id, "Only send images please!")
            return
        if hasattr(attachment, "mime_type"):
            mimetype = getattr(attachment, "mime_type")
            if "image" in mimetype:
                newFile = await attachment.get_file()
                await newFile.download(config["DEFAULT_PATH"] + '/' + fileName + '.jpeg')
                await context.bot.sendMessage(id, "Thank you <3")
            else:
                await context.bot.sendMessage(id, "Only send images please!")

async def messagehandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.sendMessage(update.effective_chat.id, "Please only send images or try /help")

if not os.path.exists('./user.json'):
    f = open("user.json", "w")
    jsonString = '{\n\t"AUTH_USERS": [],\n\t"BLOCKED_USERS": []\n}'
    f.write(jsonString)
    f.close()

if not os.path.exists('./config.json'):
    f = open("config.json", "w")
    jsonString = '{\n\t"API_TOKEN": "COPY_YOUR_API_KEY_HERE",\n\t"PASSWORD": "CHOOSE_YOUR_PASSWORD",\n\t"DEFAULT_PATH": "./download",\n\t"LOGIN_TRIES": 3\n}'
    f.write(jsonString)
    f.close()
    print("Files created, edit your config file and start script again")
    exit()

with open("./config.json", "r") as inFile:
    config = json.load(inFile)

with open("./user.json", "r") as inFile:
    userConfig = json.load(inFile)

if __name__ == '__main__':
    application = ApplicationBuilder().token(config["API_TOKEN"]).build()

    start_handler = CommandHandler('start', start)
    pw_handler = CommandHandler('pw', pw)
    help_handler = CommandHandler('help', help)
    application.add_handler(start_handler)
    application.add_handler(pw_handler)
    application.add_handler(help_handler)

    attachment_handler = MessageHandler(filters.ATTACHMENT, attachment)
    application.add_handler(attachment_handler)

    message_handler = MessageHandler(filters.ALL, messagehandler)
    application.add_handler(message_handler)

    application.run_polling()