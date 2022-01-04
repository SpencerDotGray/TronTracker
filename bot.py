
from discord.ext import commands
import discord
from datetime import datetime, time, timedelta
import asyncio
import requests
import json
import os

client = discord.Client()
jontron_url = 'https://www.youtube.com/user/JonTronShow/videos'

try:
    with open('./auth_tokens.json', 'r') as filein:
        token = json.load(filein)['token'] 
except FileNotFoundError:
    token = os.environ.get('token')

bot = commands.Bot(command_prefix="&")
WHEN = time(16, 00, 00)  # 12:00 PM
channel_id = 290915716255711232 # Put your channel id here
date_mapper = {
    'Jan': 'January',
    'Feb': 'February',
    'Mar': 'March',
    'Apr': 'April',
    'May': 'May',
    'Jun': 'June',
    'Jul': 'July',
    'Aug': 'August',
    'Sep': 'September',
    'Oct': 'October',
    'Nov': 'November',
    'Dec': 'December'
}


def get_jontron_video_title(content):

    try:
        focused_content = content[ content.index('gridVideoRenderer'): ]
        focused_content = focused_content[ focused_content.index('"text":') + len('"text":'): ]
        left = focused_content.index('"')+1
        right = focused_content[ focused_content.index('"')+1: ].index('"')+1
        title_name = focused_content[ left:right ]
        return title_name
    except ValueError:
        print('ERROR: could not get jontron video title\nSubstring did not work')


def get_jontron_video_image_url(content):

    try:
        focused_content = content[ content.index('gridVideoRenderer'): ]
        focused_content = focused_content[ focused_content.index('"url":') + len('"url":'): ]
        left = focused_content.index('"')+1
        right = focused_content[ focused_content.index('"')+1: ].index('"')+1
        picture_url = focused_content [ left:right ]
        return picture_url
    except ValueError:
        print('ERROR: could not get jontron video image\nSubstring did not work')


def get_jontron_video_date(content):

    try:
        focused_content = content[ content.index('gridVideoRenderer'): ]
        focused_content = focused_content[ focused_content.index('"text":') + len('"text":'): ]
        left = focused_content.index('"')+1
        right = focused_content[ focused_content.index('"')+1: ].index('"')+1
        title_name = focused_content[ left:right ]
        focused_content = focused_content[ focused_content.index('"url":') + len('"url":'): ]
        left = focused_content.index('"')+1
        right = focused_content[ focused_content.index('"')+1: ].index('"')+1
        watch_url = f'https://www.youtube.com{focused_content [ left:right ]}'

        results = requests.get(watch_url)
        content = results.text
        focused_content = content[ content.index('"dateText":{"simpleText":') + len('"dateText":{"simpleText":'): ]
        left = focused_content.index('"')+1
        right = focused_content[ focused_content.index('"')+1: ].index('"')+1
        video_date = focused_content[ left:right ]

        month = date_mapper[video_date.split(' ')[0]]
        date = video_date.replace(video_date.split(' ')[0], month)
        date = datetime.strptime(date,"%B %d, %Y")
        return date
    except ValueError:
        print('ERROR: could not get jontron video date\nSubstring did not work')


def get_jontron_watch_url(content):

    try:
        focused_content = content[ content.index('gridVideoRenderer'): ]
        focused_content = focused_content[ focused_content.index('"text":') + len('"text":'): ]
        left = focused_content.index('"')+1
        right = focused_content[ focused_content.index('"')+1: ].index('"')+1
        title_name = focused_content[ left:right ]
        focused_content = focused_content[ focused_content.index('"url":') + len('"url":'): ]
        left = focused_content.index('"')+1
        right = focused_content[ focused_content.index('"')+1: ].index('"')+1
        watch_url = f'https://www.youtube.com{focused_content [ left:right ]}'
        return watch_url
    except ValueError:
        print('ERROR: could not get jontron video url\nSubstring did not work')

def get_jontron():
    content = requests.get(jontron_url).text
    return {
        "title": get_jontron_video_title(content),
        "image": get_jontron_video_image_url(content),
        "date": get_jontron_video_date(content),
        "url": get_jontron_watch_url(content)
    }


async def called_once_a_day():  # Fired every day
    await bot.wait_until_ready()  # Make sure your guild cache is ready so the channel can be found via get_channel
    channel = bot.get_channel(channel_id) # Note: It's more efficient to do bot.get_guild(guild_id).get_channel(channel_id) as there's less looping involved, but just get_channel still works fine
    jontron = get_jontron()
    video_em = discord.Embed()
    video_em.set_image(url=jontron['image'])
    await channel.send(f'Good Afternoon!\nIt\'s been {(datetime.now() - jontron["date"]).days} days since JonTron uploaded "{jontron["title"]}"', embed=video_em)


async def upload_check_background_task():

    while True:
        if datetime.now().hour > 7 and datetime.now().hour < 21:
            jontron = get_jontron()
            if (os.environ.get('current_title') != jontron['title']):
                await bot.wait_until_ready()  # Make sure your guild cache is ready so the channel can be found via get_channel
                channel = bot.get_channel(channel_id)
                video_em = discord.Embed()
                video_em.set_image(url=jontron['image'])
                await channel.send(f'JONTRON HAS UPLOADED\nTHIS IS NOT A DRILL!!!\n:rotating_light::rotating_light::rotating_light::rotating_light::rotating_light::rotating_light::rotating_light::rotating_light::rotating_light::rotating_light::rotating_light::rotating_light:\n{jontron["url"]}', embed=video_em)
                os.environ['current_title'] = jontron['title']
            else:
                print('No JonTron Upload :(')
        else:
            print(f'Not within checking time')

        await asyncio.sleep(3600)


async def morning_upload_background_task():
    now = datetime.utcnow()
    if now.time() > WHEN:  # Make sure loop doesn't start after {WHEN} as then it will send immediately the first time as negative seconds will make the sleep yield instantly
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)
        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start 
    while True:
        
        now = datetime.utcnow() # You can do now() or a specific timezone if that matters, but I'll leave it with utcnow
        target_time = datetime.combine(now.date(), WHEN)  # 6:00 PM today (In UTC)
        seconds_until_target = (target_time - now).total_seconds()
        if datetime.now().hour > 7 and datetime.now().hour < 10:
            await asyncio.sleep(seconds_until_target)  # Sleep until we hit the target time
            await called_once_a_day()  # Call the helper function that sends the message
        tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
        seconds = (tomorrow - now).total_seconds()  # Seconds until tomorrow (midnight)

        await asyncio.sleep(seconds)   # Sleep until tomorrow and then the loop will start a new iteration


@bot.command()
async def JontronPlz(ctx):
    jontron = get_jontron()
    video_em = discord.Embed()
    video_em.set_image(url=jontron['image'])
    await ctx.channel.send(f'It\'s been {(datetime.now() - jontron["date"]).days} days since JonTron uploaded "{jontron["title"]}"', embed=video_em)


if __name__ == "__main__":
    print(f'Back up and running.\nLatest Video: {os.environ.get("current_title")}')
    print(f'Running message at: {WHEN.hour}:{WHEN.minute}:{WHEN.second}\nCurrent Time: {datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}')
    bot.loop.create_task(morning_upload_background_task())
    bot.loop.create_task(upload_check_background_task())
    bot.run(token)