import os
import discord
import datetime
import asyncio
from urllib.request import urlopen, Request
from subprocess import Popen, PIPE

client = discord.Client()
try:
    discord_api_token = os.environ['DISCORD_API_TOKEN']
except KeyError as err:
    print("ERROR: API token required for Discord API via env var: DISCORD_API_TOKEN \n Details: \n")
    print(err)

USER_ROLE_PERMS = discord.Permissions.text()
USER_ROLE_NAME = "kubectl-admin"
CMD_PREFIX = "!kubectl"
KUBE_CONFIG_FOLDER = "/data/kubeconfigs"
KUBE_TEMP_FOLDER = "/tmp/kube"

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message: discord.Message):
    args = message.content.split()
    role_exists = False
    user_role = discord.Role()
    for role in message.server.role_heirarchy:
        if role.name == USER_ROLE_NAME:
            role_exists = True
            user_role = role
            break
    if not role_exists:
        try:
            user_role = await client.create_role(
                message.server,
                name = USER_ROLE_NAME,
                permissions = USER_ROLE_PERMS,
                colour = discord.Color.blue(),
                hoist = False,
                mentionable = False
            )
            await client.send_message(
                message.channel,
                content="""
                I had to setup the {} role, try that again after adding yourself to the role.
                """.format(user_role.mention)
            )
        except discord.Forbidden:
            await client.send_message(
                message.channel,
                content="I don't have permission to manage roles! Therefore I cant authenticate you"
            )
    else:
        if user_role in message.author.roles:
            """Main command interpreter"""
            await parse_command(message, args)
        else:
            await client.send_message(
                message.channel,
                content="{}, You need to be a member of {} to use this command".format(
                    message.author.mention,
                    user_role.mention
                )
            )


async def parse_command(message: discord.Message, args):
    """Parses command with given args and replies to original message sender"""
    tail: bool = message.content.endswith("tail")
        # !kubectl <args> tail outputs only the tail end of the whole output
    kubeconfigpath = os.path.join(KUBE_CONFIG_FOLDER, message.server.id)
        # Kube configs are server wide and server specific
    if args[0] == CMD_PREFIX:
        if args[1] == "config":
            if args[2] == "upload" or len(message.attachments) > 0:
                if len(message.attachments) > 1:
                    await reply(message, "I can only take one config file", isEmbed=False)
                elif len(message.attachments) < 1:
                    await reply(message, "Attach a kubectl config file to upload", isEmbed=False)
                else:
                    await reply(message, "This will overwrite any existing config file! Confirm [!y/!N]:", isEmbed=False)
                    msg = await client.wait_for_message(author=message.author, timeout=60.0, check=lambda msg: msg.content.upper() == "!Y")
                    if isinstance(msg, discord.Message):
                        """Take the file"""
                        os.makedirs(os.path.dirname(kubeconfigpath), exist_ok=True)
                        with open(kubeconfigpath, 'ab') as f:
                            req = Request(message.attachments[0]['url'], headers={'User-Agent': 'Mozilla/5.0'})
                            with urlopen(req) as url:
                                f.write(url.read())
                    else:
                        reply(message, "Config upload cancelled", isEmbed=False)
            elif args[2] == "download":
                try:
                    with open(kubeconfigpath, "rb") as file:
                        await client.send_file(message.channel, file, filename="config", content="{}, Here is the kubectl config file!".format(message.author.mention))
                except FileNotFoundError:
                    await reply(message, "Your kubectl config file was not found or does not exist.", isEmbed=False)
            else:
                output = execute(
                    "kubectl --config={config} {args}".format(args=args[1:-1], config=kubeconfigpath)
                )
                if tail:
                    await reply(message, execute("echo \"{}\" | tail".format(output), shell=True))
                else:
                    await reply(message, output)
        elif message.content.contains("-o yaml"):
            await reply(message, "yaml output not implemented yet", isEmbed=False)
        elif message.content.contains("-o json"):
            await reply(message, "json output not implemented yet", isEmbed=False)
        else:
            await reply(message, "Commands not fully implemented yet", isEmbed=False)

async def reply(message, output, isEmbed: bool = True):
    """Sends output to private channel of user who sent the message if output is too long"""
    if isEmbed:
        backtick = "```"
    else:
        backtick = ""
    if len(output) > 1000:
        n = 1000  # send 1000 characters at a time
        for i in range(0, len(output), n):
            await client.send_message(
                message.author,
                "{backtick}{}{backtick}".format(output[i:i+n]),
                backtick=backtick
            )
    else:
        await client.send_message(
            message.channel,
            "{1}{backtick}{0}{backtick}".format(
                output,
                "" if isinstance(message.channel, discord.PrivateChannel) else message.author.mention,
                backtick=backtick
            )
        )


def execute(command: str, shell: bool = False) -> str:
    p = Popen(command, shell=shell, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    output, err = p.communicate()
    return output.decode('utf-8')


def main():
    client.run(discord_api_token)
