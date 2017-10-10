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

p_pwd = Popen("pwd", shell=False, stdout=PIPE, stderr=PIPE, stdin=PIPE)
pwd, err_pwd = p_pwd.communicate()

try:
    KUBE_CONFIG_FOLDER = os.environ['KUBE_CONFIG_FOLDER']
except KeyError:
    KUBE_CONFIG_FOLDER = "/data/kubeconfigs"
    pass

USER_ROLE_PERMS = discord.Permissions.text()
USER_ROLE_NAME = "kubectl-admin"
CMD_PREFIX = "!kubectl"
KUBE_TEMP_FOLDER = "/tmp/kube"

KUBECTL_EXEC_PATH = pwd.decode('utf-8').strip() + "/kubectl"

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message: discord.Message):
    args = message.content.split()
    if args[0] == CMD_PREFIX:
        role_exists = False
        for role in message.server.roles:
            if role.name == USER_ROLE_NAME:
                role_exists = True
                user_role = role
                break
        if not role_exists:
            try:
                user_role = await client.create_role(
                    message.server,
                    name=USER_ROLE_NAME,
                    permissions=USER_ROLE_PERMS,
                    colour=discord.Color.blue(),
                    hoist=False,
                    mentionable=False
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
                try:
                    await parse_command(message)
                except FileNotFoundError as e:
                    await reply(message, "No kubeconfig seems to exist on this server. Upload one with !kubectl config upload and attach a config file", isEmbed=False)
            else:
                await client.send_message(
                    message.channel,
                    content="{}, You need to be a member of {} to use this command".format(
                        message.author.mention,
                        user_role.mention
                    )
                )


async def parse_command(message: discord.Message):
    """Parses command with given args and replies to original message sender"""
    args = message.content.split()
    tail: bool = (args[-1] == "tail")  # last argument is tail
        # !kubectl <args> tail outputs only the tail end of the whole output
    kubeconfigpath = os.path.join(KUBE_CONFIG_FOLDER, message.server.id)
        # Kube configs are server wide and server specific
    test = execute("pwd")
    if args[0] == CMD_PREFIX:
        if len(args) > 1:
            if "-n" in args:
                namespace = args[args.index('-n') + 1]
            else:
                try:
                    namespace = execute("{cmd_path} --kubeconfig='{config}' config current-context".format(cmd_path=KUBECTL_EXEC_PATH,
                                                                                                 config=kubeconfigpath), shell=True).split('/')[0]
                except FileNotFoundError as e:
                    pass
            if args[1] == "config":
                if args[2] == "upload" or len(message.attachments) > 0:
                    if len(message.attachments) > 1:
                        await reply(message, "I can only take one config file", isEmbed=False)
                    elif len(message.attachments) < 1:
                        await reply(message, "Attach a kubectl config file to upload", isEmbed=False)
                    else:
                        await reply(message, "This will overwrite any existing config file! Confirm [!y/!N]:", isEmbed=False)
                        msg = await client.wait_for_message(author=message.author, timeout=60.0, check=lambda nmsg: nmsg.content.upper() == "!Y")
                        if isinstance(msg, discord.Message):
                            """Take the file"""
                            os.makedirs(os.path.dirname(kubeconfigpath), exist_ok=True)
                            with open(kubeconfigpath, 'ab') as f:
                                req = Request(message.attachments[0]['url'], headers={'User-Agent': 'Mozilla/5.0'})
                                with urlopen(req) as url:
                                    f.write(url.read())
                                    await reply(msg, "Config saved", isEmbed=False)
                        else:
                            await reply(message, "Config upload cancelled", isEmbed=False)
                elif args[2] == "download":
                    try:
                        with open(kubeconfigpath, "rb") as file:
                            await client.send_file(message.channel, file, filename="config", content="{}, Here is the kubectl config file!".format(message.author.mention))
                    except FileNotFoundError:
                        await reply(message, "Your kubectl config file was not found or does not exist.", isEmbed=False)
                else:
                    output = execute(
                        "{cmd_path} --kubeconfig={config} {args}".format(args=" ".join(args[1:]), config=kubeconfigpath, cmd_path=KUBECTL_EXEC_PATH)
                    )
                    if tail:
                        await reply(message, execute("echo \"{}\" | tail".format(output), shell=True))
                    else:
                        await reply(message, output)
            elif args[1] == "create" or args[1] == "apply":
                output = ""
                tmp = await client.send_message(
                    message.channel,
                    "Creating Resources..." if isinstance(message.channel, discord.PrivateChannel) else message.author.mention + "Creating Resources..."
                )
                if len(message.attachments) > 0:
                    for attachment in message.attachments:
                        if attachment['filename'].find('.yaml') >= 0 or attachment['filename'].find('.json') >= 0:
                            file_ext = ".yaml" if attachment['filename'].find('.yaml') else ".json"
                            filepath = KUBE_TEMP_FOLDER + "/" + message.author.id + "/" + attachment['id'] + file_ext
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            with open(filepath, 'ab') as f:
                                req = Request(attachment['url'], headers={'User-Agent': 'Mozilla/5.0'})
                                with urlopen(req) as url:
                                    f.write(url.read())
                            output += execute(
                                "{cmd_path} --kubeconfig={config} {cmd} -f {file} -n {namespace}".format(
                                    cmd_path=KUBECTL_EXEC_PATH,
                                    config=kubeconfigpath,
                                    cmd=args[1],
                                    file=filepath,
                                    namespace=namespace
                                )
                            )
                urls = [x for x in args if args[args.index(x) - 1] == "-f"]
                for url in urls:
                    output += execute(
                        "{cmd_path} --kubeconfig={config} {cmd} -f {url} -n {namespace}".format(
                            cmd_path=KUBECTL_EXEC_PATH,
                            config=kubeconfigpath,
                            cmd=args[1],
                            url=url,
                            namespace=namespace
                        )
                    )
                if len(message.attachments) > 0 or len(urls) > 0:
                    await reply(tmp, output, edit=True)
                else:
                    await client.delete_message(tmp)
                    await reply(message, "ERROR: Could not understand input.")
            elif args[1] == "get" and message.content.find('-o') >= 0:
                filename = ""
                rtype = args[2]
                rname = args[3]
                filetype = ""
                if message.content.contains("-o yaml"):
                    filetype = ".yaml"
                elif message.content.contains("-o json"):
                    filetype = ".json"
                else:
                    await reply(message, execute(
                        "{cmd_path} --kubeconfig={config} {cmd}".format(
                            cmd_path=KUBECTL_EXEC_PATH,
                            config=kubeconfigpath,
                            cmd=" ".join(args[1:]),
                        )
                    ))
                    return
                filename = rname + "-" + rtype + filetype
                exportfilepath = os.path.join(KUBE_TEMP_FOLDER, message.author.id + filename)
                os.makedirs(os.path.dirname(exportfilepath), exist_ok=True)
                execute(
                    "{cmd_path} --kubeconfig={config} {cmd} > {outfile}".format(
                        cmd_path=KUBECTL_EXEC_PATH,
                        config=kubeconfigpath,
                        cmd=" ".join(args[1:]),
                        outfile=exportfilepath
                    )
                )
                with open(exportfilepath, 'r') as f:
                    await client.send_file(
                        message.channel,
                        f,
                        filename=filename,
                        content="Here are your exported resources!"
                    )
            else:
                await reply(message, execute(
                    "{cmd_path} --kubeconfig={config} {cmd}".format(
                        cmd_path=KUBECTL_EXEC_PATH,
                        config=kubeconfigpath,
                        cmd=" ".join(args[1:])
                    )
                ))
        else:
            await reply(message, execute(
                "{cmd_path} --kubeconfig={config} {cmd}".format(
                    cmd_path=KUBECTL_EXEC_PATH,
                    config=kubeconfigpath,
                    cmd=" ".join(args[1:])
                )
            ))


async def reply(message, output, isEmbed: bool = True, edit: bool = False):
    """Sends output to private channel of user who sent the message if output is too long"""
    if isEmbed:
        backtick = "```"
    else:
        backtick = ""
    if edit:
        action = client.edit_message
    else:
        action = client.send_message
    if len(output) > 1000:
        n = 1000  # send 1000 characters at a time
        for i in range(0, len(output), n):
            await action(
                message if edit else message.author,
                "{backtick}{output}{backtick}".format(output=output[i:i+n], backtick=backtick),
            )
    else:
        await action(
            message if edit else message.channel,
            "{1} {backtick}{0}{backtick}".format(
                output,
                "" if isinstance(message.channel, discord.PrivateChannel) else message.author.mention,
                backtick=backtick
            )
        )


def execute(command: str, shell: bool = True) -> str:
    p = Popen(command, shell=shell, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    output, err = p.communicate()
    return output.decode('utf-8') + err.decode('utf-8')


def main():
    client.run(discord_api_token)
