import os
from twitchio.ext import commands
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
from playsound import playsound

# Load environment variables from .env file
load_dotenv('api.env')

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Load bad words list from badwords.txt
with open('badwords.txt', 'r') as file:
    bad_words = file.read().splitlines()

# Load usuals list from usuals.txt
with open('usuals.txt', 'r') as file:
    usuals = set(file.read().splitlines())

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=os.getenv('TMI_TOKEN'), prefix='!',
                         initial_channels=[os.getenv('CHANNEL_NAME')])
        self.first_time_chatters = set()

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        if message.echo:
            return

        # Greet usuals if they type for the first time
        if message.author.name in usuals and message.author.name not in self.first_time_chatters:
            self.first_time_chatters.add(message.author.name)
            await message.channel.send(f"Hey {message.author.name}, welcome back to the chat!")

        await self.handle_commands(message)

    def contains_bad_word(self, text):
        words = set(text.lower().split())
        return any(bad_word.lower() in words for bad_word in bad_words)

    @commands.command(name='buddy')
    async def ask(self, ctx):
        # Check if user is a subscriber
        if not ctx.author.is_subscriber:
            await ctx.send("Sorry, this command is only available to subscribers.")
            return

        user_input = ctx.message.content[len('!buddy '):].strip()

        # Check for bad words
        if self.contains_bad_word(user_input):
            await ctx.send("Sorry, I can't comment on that.")
            return

        if not user_input:
            await ctx.send("Please provide some input after the command.")
            return

        try:
            print("Generating response...")
            response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[{"role": "user", "content": user_input}]
            )
            response_text = response.choices[0].message.content.strip()
            print(f"Response text: {response_text}")

            print("Generating speech...")
            tts = gTTS(response_text, lang='en')
            audio_file = "response.mp3"
            tts.save(audio_file)

            await ctx.send(f"AI Response: {response_text}")
            print("Playing speech...")
            playsound(audio_file)

        except Exception as e:
            print(f"Error: {e}")
            await ctx.send("Sorry, there was an error processing your request.")

# Instantiate Bot with your Twitch credentials
bot = Bot()
bot.run()
