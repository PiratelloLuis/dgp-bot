# This example requires the 'message_content' intent.
import os
from dotenv import load_dotenv
from discord.ext import commands
import discord
import json
import requests
import unicodedata
from google import genai

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
genai_mode = False

class MyClient(commands.Bot):
    
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        global genai_mode
        genai_mode = False

    def get_channel(self, id):
        return super().get_channel(id)
   

client = MyClient(command_prefix='$', intents=intents)

def normalizar_texto(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


#Arrumar o estado que não é considerado na busca usando >>partes = message.split()<< 
# >>cidade = " ".join(partes[:-1])<< >>estado = partes[-1].upper()<< e >>query = f"{cidade}, {estado}, BR"<<
@client.command()
async def clima(ctx, *, message):
    normalized_message = normalizar_texto(message)
    API_KEY = os.getenv('CLIMA_API_KEY')
    params = {
        "key": API_KEY,
        "q": normalized_message,
        "lang": "pt"
    }
    url = "http://api.weatherapi.com/v1/current.json"
    response = requests.get(url, params=params)
    data = response.json()
    try:
        cidade = data["location"]["name"]
        clima = data["current"]["condition"]["text"]
        estado = data["location"]["region"]
        temperatura = data["current"]["temp_c"]
        await ctx.send(f"Cidade: {cidade}, {estado} com a temperatura de: {temperatura} e {clima}")
    except KeyError as e:
        await ctx.send("❌ Cidade não encontrada ou erro na resposta da API.")
        

@client.command()
async def genai_mode(ctx):
    global genai_mode
    genai_mode = not genai_mode

    status = "ativado" if genai_mode else "desativado"
    await ctx.reply(f"🧠 Modo IA {status}")

#Implementar memoria na AI do google
@client.event
async def on_message(message):
    global genai_mode
    str_message = str(message.content)
    # ignora mensagens do próprio bot
    if message.author.bot:
        return

    # permite comandos funcionarem
    await client.process_commands(message)

    if not genai_mode:
        return
    
    API_KEY = os.getenv("GENAI_API")
    if not API_KEY:
        await message.reply("API KEY não configurada.")
        return

    clientAI = genai.Client(api_key=API_KEY)

    try:
        
        response = clientAI.models.generate_content(
            model="gemini-2.5-flash",
            contents=message.content
        )
        
        text = response.text
        if len(text) > 2000:
            text = text[:1990] + "..."
        if str_message.startswith('$'):
            return
        print("Gerando Reposta.......")
        await message.reply(text)

    except Exception as e:
        await message.reply(f"Erro na API do Gemini:\n```{e}```")     


client.run(TOKEN)
