import importlib
import subprocess
import sys
import threading
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to install a module
def install_module(module_name):
    try:
        importlib.import_module(module_name)
        logger.info(f"{module_name} is already installed.")
    except ImportError:
        logger.info(f"{module_name} not found. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            except subprocess.CalledProcessError:
                logger.warning(f"Normal install failed, trying with --user for {module_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", module_name])
            logger.info(f"{module_name} installed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {module_name}. Error: {e}")
            logger.error("Try: python -m venv venv; source venv/bin/activate; python app.py")
            sys.exit(1)

# Install required modules
required_modules = ["flask", "discord.py"]
for module in required_modules:
    install_module(module)

# Import modules
from flask import Flask
import discord
from discord.ext import commands

# Set up Flask app
app = Flask(__name__)
bot_running = False

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Bot logged in as {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

def run_bot():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not set. Add it to environment variables.")
        return
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

# Flask routes
@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Discord Bot Control</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 50px;
            }
            button {
                padding: 10px 20px;
                font-size: 16px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>Discord Bot Control</h1>
        <p>Bot Status: {{ bot_status }}</p>
        <button onclick="runBot()">Run Bot</button>
        <script>
            function runBot() {
                fetch('/run_bot', { method: 'POST' })
                    .then(response => response.text())
                    .then(data => {
                        alert(data);
                        location.reload();
                    })
                    .catch(error => console.error('Error:', error));
            }
        </script>
    </body>
    </html>
    """
    return html.replace('{{ bot_status }}', 'Running' if bot_running else 'Stopped')

@app.route('/run_bot', methods=['POST'])
def run_bot_endpoint():
    global bot_running
    if not bot_running:
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        bot_running = True
        return 'Bot started!'
    return 'Bot is already running!'

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        logger.error("Ensure port is not in use.")