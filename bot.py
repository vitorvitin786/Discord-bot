import importlib
import subprocess
import sys
import threading
import os

# Function to install a module with error handling
def install_module(module_name):
    try:
        importlib.import_module(module_name)
        print(f"{module_name} is already installed.")
    except ImportError:
        print(f"{module_name} not found. Attempting to install...")
        try:
            # Ensure pip is up-to-date
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
            # Try normal install (virtualenv)
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            except subprocess.CalledProcessError:
                # Fallback to --user
                print(f"Normal install failed, trying with --user for {module_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", module_name])
            print(f"{module_name} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {module_name}. Error: {e}")
            print("Possible fixes:")
            print("- Use a virtual environment: python -m venv venv; source venv/bin/activate")
            print("- Ensure internet connection.")
            print("- Check permissions or use --user: pip install --user {module_name}")
            sys.exit(1)

# Install required modules
required_modules = ["flask", "discord.py"]
# python-dotenv is optional, only install if needed
if not os.getenv('DISCORD_TOKEN'):
    required_modules.append("python-dotenv")

for module in required_modules:
    install_module(module)

# Import modules
from flask import Flask
import discord
from discord.ext import commands

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("No python-dotenv, relying on environment variable DISCORD_TOKEN.")

# Set up Flask app
app = Flask(__name__)
bot_running = False

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

def run_bot():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not set. Set it as an environment variable or in .env for local use.")
        return
    try:
        bot.run(token)
    except Exception as e:
        print(f"Failed to start bot: {e}")

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
        app.run(debug=True)
    except Exception as e:
        print(f"Failed to start Flask server: {e}")
        print("Ensure port 5000 is not in use.")