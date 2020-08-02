import util
import aiohttp
import asyncio
import discord
import re
import logging
import traceback
import time
import re
import json
from urllib.parse import urljoin
import dateutil.parser
import datetime
from contextlib import asynccontextmanager
import random
from datetime import datetime

webhook = "https://discordapp.com/api/webhooks/738909876025032766/OBljydpBdUuc9_cuaerzyyKKopVhiZIxahccA08GunfdpbNNq34ORSfOfzyaYZ7oah9X"


screen_logger = logging.getLogger('screen_logger')
screen_logger.setLevel(logging.INFO)

streamFormatter = logging.StreamHandler()

streamFormatter.setFormatter(logging.Formatter('%(asctime)s %(message)s'))

fileFormatter = logging.FileHandler("asphalt.logs")

fileFormatter.setFormatter(logging.Formatter('%(asctime)s %(message)s'))

screen_logger.addHandler(streamFormatter)
screen_logger.addHandler(fileFormatter)


class invalid_status_code(Exception):
	"""exception if status code is not 200 or 404"""









def raise_for_status(response, skip = ()):
	if not (response.status == 200 or response.status == 404 or response.status in skip):
		raise invalid_status_code('{} -> {}'.format(response.url, response.status))
	
def log_based_on_response(id, response):
	screen_logger.info("{} > {} -> {}  " .format(id, str(response.url), response.status ))
	#print(response.headers['server-timing'])

def log_exception(id, ex, *, traceback = True):
	if traceback:
		screen_logger.debug("{} > {}".format(id, traceback.print_tb(ex.__traceback__)))
	screen_logger.info("{} > {}". format(id, str(ex)))



def get_title(obj):
	return obj['data'][0]['attributes']['name']
    
def get_price(obj):
	return 	 obj['data'][0]['attributes']['price']


class Monitor:
	def __init__(self, id, *, urlQueue, proxyBuffer, stock_info, session):
		self.urlQueue = urlQueue
		self.proxyBuffer = proxyBuffer
		self.stock_info = stock_info
		self.session = session
		self.first = True
		self.live = False
		self.postData = {}
		self.variants= {}

		self.id = id
		self.embed_sender = discord.embedSender(webhook)
	
	@asynccontextmanager
	async def load_url(self, *, wait):
		url = await self.urlQueue.get()
		try:
			yield url
		finally:
			self.urlQueue.put_nowait(url)
			await asyncio.sleep(wait)
	
	
	async def process_url(self, url, proxy):
		restocked = False
		sizes=[]
		current_stock_info = {}
		
		
		if self.first or not self.live :
			path = url[39:-1]
			urlts = 'https://d16xzy77usko0.cloudfront.net/api/product/?criteria=url_path%3A'+ path 
			#print (urlts)
			async with self.session.get(urlts , proxy = proxy) as response:
				response.text_content = await response.text()
			
			obj = json.loads(response.text_content)
			log_based_on_response(self.id, response)
			raise_for_status(response)

			if len(obj['data'])==0:
				print("API ERROR")
				self.Error = True
		
			elif self.live == False:
				if 'ag_release_date' in  obj['data'][0]['attributes']:
					now = datetime.now()
					now = dateutil.parser.parse(now.strftime("%Y-%m-%d %H:%M"))
					releaseDate = obj['data'][0]['attributes']['ag_release_date']
					releaseDate = releaseDate.replace('T',' ')
					releaseDate = dateutil.parser.parse(releaseDate)
					if(now<releaseDate):
						print('NOT LIVE')
					else:
						print('LIVE')
						self.live = True
				else:
					print('LIVE')
					self.live = True
			
			if self.first == True:
				postData = []
				for variant in obj['data'][0]['associated_products']:
					#print(variant['attributes']['is_in_stock'])
					postData.append(variant['attributes']['ean'])
					self.variants[variant['attributes']['ean']] = variant['attributes']['shoe_size'] 
				self.postData['eans']= postData 
				current_stock_info['title'] = get_title(obj)
				print(current_stock_info['title'])
				current_stock_info['url'] = url
				async with self.session.get(url , proxy = proxy) as response2:
					response2.text_content = await response2.text()
				#print(response2.text_content)
				linkimage = re.search('og:image"(.*?)>',response2.text_content).group(1)
				linkimage = re.search('content="(.*?)"',linkimage).group(1)
				#print(linkimage)
				if linkimage!='':
					current_stock_info['imgUrl'] = linkimage
				current_stock_info['price'] = get_price(obj)
				#print(current_stock_info['price'])
			
			#print(variants)

		if self.live == True:
			if self.first==True:
				headers = {
				'authority': 'api.asphaltgold.com',
				'method': 'POST',
				'scheme': 'https',
				'accept': ' application/json, text/plain, */*',
				'accept-encoding': ' gzip, deflate, br',
				'accept-language': ' es,ca;q=0.9,en;q=0.8,de;q=0.7',
				'content-type': ' application/json',
				'origin': ' https://www.asphaltgold.com',
				'referer': url,
				'user-agent': ' Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
				}
					
				timeout = aiohttp.ClientTimeout(total = 8)
				session2 = aiohttp.ClientSession(headers = headers, timeout = timeout, cookie_jar = aiohttp.DummyCookieJar() )
				self.session = session2
				
			stockUrl = "https://api.asphaltgold.com/V1/stock//available"
			
			#print(self.postData)

			async with self.session.post(stockUrl , proxy = proxy, json = self.postData ) as responseSizes:
				responseSizes.text_content = await responseSizes.text()
				obj2 = json.loads(responseSizes.text_content)
			log_based_on_response(self.id, responseSizes)
			raise_for_status(responseSizes)

			for variant in obj2:
				print(variant)
				sizes.append(self.variants[variant])
			
			#print(sizes)

			current_stock_info['sizes'] = sizes

			if(not self.first):
				print(len(self.stock_info.get('sizes')))
				if self.stock_info.get('sizes') != current_stock_info.get('sizes') and len(self.stock_info.get('sizes'))<=len(current_stock_info.get('sizes')):
						restocked = True

				current_stock_info['title'] =self.stock_info['title']
				current_stock_info['url'] = self.stock_info['url']
				current_stock_info['imgUrl'] = self.stock_info['imgUrl']
				current_stock_info['price'] = self.stock_info['price']
			
			if restocked:
				screen_logger.info("{} > {} Restocked Sizes".format(self.id, url))
				embed = discord.make_embed(current_stock_info)

				if await self.embed_sender.send(embed):
					screen_logger.info("{} > **Discord Notification Sent for {}**".format(self.id, url))
				else:
					screen_logger.info("{} > **Discord Notification Failed for {}**".format(self.id, url))

			self.stock_info = current_stock_info	
			self.first = False
			
	
	async def start(self, wait):
		proxy = await self.proxyBuffer.get_and_inc()
		
		screen_logger.info('{} > Using Proxy {}'.format(self.id, proxy))
		
		while True:
			async with self.load_url(wait = wait) as url:
				#screen_logger.info(f"{self.id} > Checking {url}")
				for i in range(2):
					try:
						await self.process_url(url, proxy)
						break
					except Exception as e:
						log_exception(self.id, e, traceback = False)
						
						if i == 1:
							proxy = await self.proxyBuffer.get_and_inc()
							screen_logger.info('{} > Changing Proxy to {}'.format(self.id, proxy))






async def main(urls, proxies, workers, wait_time):
	#queries = [{'url': link, 'previousStockedSizes': []} for link in queries]
	
	proxyBuffer = util.readOnlyAsyncCircularBuffer(proxies)
	
	urlQueue = asyncio.Queue()
	
	for url in urls:
		urlQueue.put_nowait(url)

	headers = {
		'authority': 'd16xzy77usko0.cloudfront.net',
		'scheme': 'https',
		'accept': ' application/vnd.lizards-and-pumpkins.product.v1+json',
		'accept-encoding': ' gzip, deflate, br',
		'accept-language': ' es,ca;q=0.9,en;q=0.8,de;q=0.7',
		'origin': ' https://www.asphaltgold.com',
		'user-agent': ' Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
		'Cache-Control': 'no-cache',
	}
		
	timeout = aiohttp.ClientTimeout(total = 8)
	
	stock_info = {}

	session = aiohttp.ClientSession(headers = headers, timeout = timeout, cookie_jar = aiohttp.DummyCookieJar() )
	
	monitors = [Monitor(f'worker-{i}', stock_info = stock_info, session = session, urlQueue = urlQueue, proxyBuffer = proxyBuffer) for i in range(workers)]
	
	coros = [monitor.start(wait = wait_time) for monitor in monitors]
	
	await asyncio.gather(*coros)
	
	await session.close()
		
if __name__ == "__main__":
	
	url_file = 'urls.txt'
	proxy_file = 'proxies.txt'
	
	urls = util.nonblank_lines(url_file)
	
	proxies = util.load_proxies_from_file(proxy_file, shuffle = True)

	workers = len(urls)
	
	wait_time = 1

	policy = asyncio.WindowsSelectorEventLoopPolicy()
	asyncio.set_event_loop_policy(policy)

	asyncio.run(main(urls, proxies, workers, wait_time))
