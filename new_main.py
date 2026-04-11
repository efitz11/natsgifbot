import os
import discord
from discord.ext import commands
from mlb_client import MLBClient
from dotenv import load_dotenv

# Modern Discord bots require explicit Intents
intents = discord.Intents.default()
intents.message_content = True  # Enable if you also want it to read regular messages eventually

class ModernNatsBot(commands.Bot):
    def __init__(self):
        # A command_prefix is still required by the superclass, but we'll be using slash commands
        super().__init__(command_prefix='!', intents=intents)
        self.mlb_client = MLBClient()

    async def setup_hook(self):
        # Load our new modern cog
        await self.load_extension('mlb_slash')
        
        # Sync the slash commands to Discord
        await self.tree.sync()
        print("Slash commands synced globally!")
        
    async def close(self):
        # Cleanly close the aiohttp session when the bot shuts down
        await self.mlb_client.close()
        await super().close()

bot = ModernNatsBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

if __name__ == "__main__":
    # Load environment variables from a .env file if it exists
    load_dotenv()
    
    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token:
        raise ValueError("No DISCORD_TOKEN found in environment variables. Make sure you have a .env file setup!")

    bot.run(discord_token)