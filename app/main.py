import discord
from discord.ext import commands
import asyncio
import os
import subprocess

client = discord.Client()
oc_config_folder = "/data/kubeconfigs/"
oc_config_arg = "--config " + oc_config_folder

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    args = message.content.split()
    if args[0] == "!oc":
        if args[1] == "login":
            if isinstance(message.channel, discord.PrivateChannel):
                if len(args) == 3:
                    octoken = args[2]
                    await client.send_message(message.channel, "```" + execute("oc " + oc_config_arg + message.author.id + " login --token " + octoken + " cloud.jtcressy.net") + "```")
                else:
                    await client.send_message(message.channel, "You need to supply a token with ``!oc login <token>`` by requesting one from https://cloud.jtcressy.net/oauth/token/request")
            else:
                await client.send_message(message.author, "You cannot login to OpenShift tools using a public channel. Send me a private message with ``!oc login <token>`` instead.")
                await client.send_message(message.author, "You need to supply a token with ``!oc login <token>`` by requesting one from https://cloud.jtcressy.net/oauth/token/request")
                await client.delete_message(message)
        elif args[1] == "status":
            await client.send_message(message.channel, message.author.mention + "```" + execute("oc " + oc_config_arg + message.author.id + " status") + "```")
        else:
            output = execute("oc " + oc_config_arg + message.author.id + " " + " ".join(args[1:]))
            if len(output) > 1000:
                lines = output.split('\n')
                n = 30 #send 30 lines at a time
                [await client.send_message(message.author, "```" + "\n".join(lines[i:i+n])  + "```") for i in range(0, len(lines), n)]
            else:
                await client.send_message(message.author if isinstance(message.channel, discord.PrivateChannel) else message.channel, message.author.mention + "```" + output + "```")

def execute(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, err = p.communicate()
    return output.decode('utf-8')

client.run(os.environ['DISCORD_API_TOKEN'])