# This example requires the 'message_content' intent.
import os
from dotenv import load_dotenv
from discord.ext import commands
import discord
import requests
import unicodedata
from google import genai
import random
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
        await ctx.reply(f"Cidade: {cidade}, {estado} com a temperatura de: {temperatura} e {clima}")
    except KeyError as e:
        await ctx.reply("❌ Cidade não encontrada ou erro na resposta da API.")

@client.command()
async def genai_mode(ctx):
    global genai_mode
    genai_mode = not genai_mode

    status = "ativado" if genai_mode else "desativado"
    await ctx.reply(f"🧠 Modo IA {status}")

@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.send(f"Deletando {amount} mensagens...", delete_after=3)
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"{amount} mensagens deletadas por {ctx.author.mention}", delete_after=3)


#Implementar memoria na AI do google
@client.event
async def on_message(message):
    global genai_mode
    str_message = str(message.content)
    content = normalizar_texto(message.content.lower())
    lista_resposta = ["que link legal", "sem graça", "nem ri", "XD"]
    random_string = random.choice(lista_resposta)
    # ignora mensagens do próprio bot
    if message.author.bot:
        return
    elif genai_mode == False:
        #Evento de resposta de palavras
        #Melhorar usando triggers lambda
        if any(word in content for word in ('gorda', 'gordinha')):
            await message.reply(os.getenv("chaves_gif"))

        elif any(word in content for word in ('povo prometido', 'israel')):
            await message.reply(os.getenv("israel_gif"))

        elif any(word in content for word in ('linard', 'linarde')):
            await message.reply(os.getenv("linard_gif"))

        elif any(word in content for word in ('true', 'verdade')):
            await message.reply(os.getenv("true_gif"))

        elif any(word in content for word in ('troll', 'trollando', 'trollface')):
            if message.guild: 
                for emoji in message.guild.emojis:
                    if emoji.name == "trollface":
                        await message.add_reaction(emoji)
                        break
        elif content.startswith("https") or content.startswith("http"):
            await message.reply(random_string)

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
        genai_mode = False
        await message.reply(f"Modo AI Desativado para proteção da API")
        await message.reply(f"Erro na API do Gemini:\n```{e}```")     



client.run(TOKEN)
