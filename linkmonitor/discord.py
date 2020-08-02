import aiohttp
from datetime import datetime
import asyncio
import json
import util

def make_embed(details):
		
	separator='\n'
	sizes = separator.join(details['sizes'])
	"""quicktasks = []
	orbitUrl = 'http://localhost:5060/quicktask?site=kickz&method=url&input=' + details['url']
	t3kUrl = 'https://api.t3k.industries/qt/?module=kickz&input=' + details['url']
	
	orbit = "[{}]({}) ".format( "ORBIT", orbitUrl)	
	t3k = "[{}]({}) ".format( "T3K", t3kUrl)	
	quicktasks.append({
		'name': 'QT',
		'value': orbit + t3k
	})
	"""
	return [{
				
				'title': "{}\n".format(details['title']),
				'url': details['url'],
				'color': 0x8c7656,
				'thumbnail': {
					'url': details['imgUrl']
					},
				'fields': [
							{
								"name": "Price",
								"value": details['price']
,
							},
							{
								"name": "Sizes",
								"value": sizes
,
							},
							#*quicktasks
							],
			'footer': {
				'icon_url': 'https://i.imgur.com/jTYyIYX.png',
				'text': 'Asphaltgold monitor by easycopeu'
				}
			}]

class embedSender:
	def __init__(self, webhook, wait_time_on_error = 4):
		self.webhook = webhook
		self.session = aiohttp.ClientSession(cookie_jar = aiohttp.DummyCookieJar())
		self.wait_time_on_error = wait_time_on_error
		
	async def send(self, embed):
		
		data = {
			'username' : 'ASPHALTGOLD',
			'avatar_url': 'https://lh3.googleusercontent.com/Z21yoTRnINZ4EBMecgQ2K7OpQ9ACRWWez-bA1lpdKAqe0k0nVF44ECIzSyPJB2L1O49y',
			'embeds': embed
		}
		for _ in range(2):
			async with self.session.post(self.webhook, json = data) as resp:
				if resp.status == 204:
					break
			
			await asyncio.sleep(self.wait_time_on_error)
		return resp.status == 204
