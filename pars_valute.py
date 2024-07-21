import redis.asyncio as redis
import xml.etree.ElementTree as ElementTree

import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiohttp import ClientSession, web


redis_client = redis.from_url("redis://redis:6379/0")

async def fetch_xml():
    url = "https://cbr.ru/scripts/XML_daily.asp"
    async with ClientSession() as session:
        async with session.get(url) as response:
            xmlstr = await response.read()
            return xmlstr

async def update_redis_data():
    while True:
        xmlstr = await fetch_xml()
        
        root = ElementTree.XML(xmlstr) 
        currency_data_dict = {}
             
        for valute in root.findall('Valute'):
            currency_data = {
                'ID': valute.get('ID'),
                'NumCode': valute.find('NumCode').text,
                'CharCode': valute.find('CharCode').text,
                'Nominal': valute.find('Nominal').text,
                'Name': valute.find('Name').text,
                'Value': valute.find('Value').text,
                'VunitRate': valute.find('VunitRate').text,
            }
            json_data = json.dumps(currency_data)
            currency_data_dict[currency_data['CharCode']] = json_data
            await redis_client.mset(currency_data_dict)
        rus_current = {
            'ID': '1',
            'NumCode': '1',
            'CharCode': 'RUB',
            'Nominal': '1',
            'Name': 'Росийскийских рублей',
            'Value': '1',
            'VunitRate': '1,0',
        }
        json_data = json.dumps(rus_current)
        await redis_client.set(rus_current['CharCode'], json_data)
        # redis_client.close()
        # await redis_client.wait_closed() 

async def on_startup(app):
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(hour='0', minute='0')  # Например, каждый час в начале часа
    scheduler.add_job(update_redis_data, trigger)
    scheduler.start()
    app['scheduler'] = scheduler
    
    # Немедленно забрать данные при запуске приложения
    await update_redis_data()

async def on_cleanup(app):
    scheduler = app['scheduler']
    scheduler.shutdown()

app = web.Application()
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)
