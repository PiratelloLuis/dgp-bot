# This example requires the 'message_content' intent.
import os
from dotenv import load_dotenv
from discord.ext import commands
import discord
import requests
import unicodedata
from google import genai
import random
import emoji

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
    await ctx.send(f"{amount} mensagens deletadas por {ctx.author.mention}", delete_after=10)


#Implementar memoria na AI do google
@client.event
async def on_message(message):
    global genai_mode
    str_message = str(message.content)
    content = normalizar_texto(message.content.lower())
    #lista_resposta = ["que link legal", "sem graça", "nem ri", "XD", "que link bosta morre", "gostei desse link", "não achei graça", "rídiculo", ":v", "cuzão se vc n quer emoção só segue sua vida mano entendeu corolla 2008 xei automático prata NOSSA que maravilha hein irmão pega sua mina aniversário de namoro já leva ela no outback né ribs on the barbie ooo mano q diferente hein tá ligado já porra passa no shopping no cinema vai ver o que? Filme da marvel vê um filme da marvel viado sai do filme da marvel já passa na centauro cuzão pega o que? Um tênis mizuno de corrida preto de 300 reais igual a TODOS os outros que é a sua cara cuzão já saí passa na Renner pega uma camisa branca com um coqueiro escrito OKLAHOMA tá ligado é isso essa é sua vida mano entendeu curte a sua vida mano vc é assim viado é isso mesmo viado já pega seu tênis mizuno preto genérico sua camisa branca com coqueiro escrito Oklahoma genérica entendeu a sua namorada entendeu q é a Larissa q cursa odontologia entendeu na UNIP pega ela tb já vai pro show do coldplay curte o show do coldplay oooo e na saída vc vai pegar o seu corolla xei 2008 prata automático sem tesão sem tesão nenhum entra liga e vai pra casa chegando em casa vc dorme e pensa pensa o quanto vc é sem graça é isso porra" ]
    #random_string = random.choice(lista_resposta)

    TRIGGERS_REPLY = {
    ("gorda", "gordinha"): "chaves_gif",
    ("povo prometido", "israel", "me prometeram", "prometeu", "me foi prometido"): "israel_gif",
    ("linard", "linarde"): "linard_gif",
    ("true", "verdade"): "true_gif",
}


    # ignora mensagens do próprio bot
    if message.author.bot or genai_mode:
        return
    
    #Trigger replys
    for palavras, env_key in TRIGGERS_REPLY.items():
        if any(p in content for p in palavras):
            await message.reply(os.getenv(env_key))
            return
        
    # Trollface
    if any(w in content for w in ("troll", "trollando", "trollface")):
        if message.guild:
            troll = next(
                (e for e in message.guild.emojis if e.name == "trollface"),
                None
            )
            if troll:
                await message.add_reaction(troll)
        return

    # Links
    #if content.startswith(("http://", "https://")):
        #await message.reply(random_string)
        #return

    # Apenas emoji
    if (
        emoji.emoji_count(content) > 0
        and content.strip().replace(" ", "") in emoji.EMOJI_DATA
        and message.guild
        and message.guild.emojis
    ):
        await message.reply(str(random.choice(message.guild.emojis)))



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
