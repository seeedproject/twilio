#!/usr/bin/python
# coding:utf-8
# import Speech SDK

'''
	文件名 : speach.py
	
'''

from evdev import InputDevice,categorize,ecodes
from pypinyin import pinyin, lazy_pinyin
from ctypes import *
from pixel_ring import pixel_ring
from respeaker.bing_speech_api import BingSpeechAPI,RequestError
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from voice_engine.kws import KWS
from voice_engine.ns import NS
from voice_engine.source import Source
from voice_engine.channel_picker import ChannelPicker

from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError

from voice_engine.element import Element
	
import mraa
import logging
import ConfigParser
import threading,signal
import time
import sys,stat
import os
import re
import json
import copy

if sys.version_info[0] < 3:
    import Queue as queue
else:
    import queue

is_pressed  	= False
is_record		= False
is_music		= False
is_noteinfo 	= False
led_ring		= False
parse_flags 	= False
starttime 		= 0
lasttime  		= 0
recvok			= False

stringcopy = ''

'''
Twilio key
'''
ACCOUNTSID = 'AC126c5beb95795762e545c22121d61d24'
AUTHTOKEN = '4d036c85d72c9de3005fd757d1d8663a'

'''
Bing key

'''
BING_KEY = 'ccac906bc35345f0abd7b57db29d8123'

'''
tencent api
'''
appid = 1400102718
appkey = "214b971761479e894e5fd27227d4e936"


'''
file path select (en,cn),EN == True 时为中文，否则为英文
'''
ENPATH = "/home/respeaker/twilio/username_en.txt"
CNPATH = "/home/respeaker/twilio/username.txt"
ALLNAME = "/home/respeaker/twilio/allname.txt"

EN = False


'''
 宏开关
'''
TREAD_ON 	= 1
ON			= 0

'''
TENCENT_TWILIO = True 时为Twolio 
TENCENT_TWILIO = False 时为Tencent
'''
TENCENT_TWILIO = False



'''
bing 语音转文本解析
'''
class Bing(Element):
    def __init__(self, key):
        super(Bing, self).__init__()

        self.key = key

        self.queue = queue.Queue()
        self.listening = False
        self.done = False
        self.event = threading.Event()

        self.bing = BingSpeechAPI(BING_KEY)

    def put(self, data):
        if self.listening:
            self.queue.put(data)

    def start(self):
        self.done = False
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.done = True

    def listen(self):
        self.listening = True
        self.event.set()

    def run(self):
		while not self.done:
			self.event.wait()

			def gen():
				count = 0
				while count < 16000 * 6:
					data = self.queue.get()
					if not data:
						break

					yield data
					count += len(data) / 2

			#recognize speech using Microsoft Bing Voice Recognition
			try:
				# text = bing.recognize(gen(), language='zh-CN')
				text = self.bing.recognize(gen())
				global stringcopy
				print('Bing:{}'.format(text).encode('utf-8'))
				stringcopy = format(text).encode('utf-8')
				
			except ValueError:
				print('Not recognized')
				global is_music
				is_music = False
					
				time.sleep(1)
				#play_music('mpg123 /home/respeaker/twilio/notfind.mp3')
				play_music('mpg123 /home/respeaker/twilio/not_clear.mp3')
			except RequestError as e:
				print('Network error {}'.format(e))
				time.sleep(1)
				play_music('mpg123 /home/respeaker/twilio/net_error.mp3')

			self.listening = False
			self.event.clear()
			self.queue.queue.clear()
			global recvok,is_record
			recvok = True
			is_record = True
			
'''
文本解析
'''			
class text_parse(object):		
	def __init__(self,_text):
		self.text 	= _text
		
	def parse_array(self,text):
		array =[]
		array = text.lower().split(' ')
		return 	array

	def parse_array_noneuplow(self,text):
		array =[]
		array = text.split(' ')
		return 	array
		
	'''
	 list
	'''
	def convert_to_list(self,text):
		result=[]
		fd = file(text, "r")
		
		for line in fd.readlines():
			result.append(''.join(list(line.lower().rstrip().split(','))))
		
		
		'''
		for item in result:
			for it in item :
				print(it)
		'''
		fd.close()
		
		return result
		
		
'''
 speech 服务调度
'''
class speech_server_scheduler(object):
	
	def __init__(self,_path,_format):
		self.path 	= _path
		self.format = _format
		'''	
		read file 
		'''
	def get_file_content(self):
		with open(self.path, 'rb') as fp:
			return fp.read()
			
	def bing__parse_speech(self):
		global is_music,is_find,count,stringcopy
		try:                      
			bing.listen()
			text = recv_string()
			stringcopy = ''
			'''
			 在给username_en.txt或者allname.txt 加入用户名时，在终端运行些程序，可以看解析后的用户信息，这样可以有效的做用户名匹配
			'''
			print('Recognized text %s' % text)
			textparse = text_parse(text)
			
			if text:           
				print('Recognized %s' % text)
				is_find = False
				array = textparse.parse_array(text)
				
				print("---------------------------\n")
				
				convert_lis = textparse.convert_to_list(ALLNAME)
				'''
				for strd in convert_lis:
					print(strd)
					print("\n")
				'''
				# start parse voice 
				for i in array:
					for employee in convert_lis:
						if i == employee :
						#do what you want to do
							print(employee)
							print("\n")
							is_find = True
							is_music = False
							'''
							Thank you. What is your name?
							'''
							play_music("mpg123 /home/respeaker/twilio/Thanks.mp3")
							count=2
							
							while(count):
								
								bing.listen()
								time.sleep(0.1)
								
								gestName = recv_string()
								stringcopy = ''
								is_music = True

								is_music = False
								getGestName = ''
								
								if gestName:
									result = []
									str_list = textparse.parse_array_noneuplow(gestName)
									print(len(str_list))
									list_len = len(str_list)
									
									
									if list_len == 1:
										getGestName = str_list[list_len-1]
									elif list_len == 2:
										getGestName = str_list[0]+'.'+str_list[1]
									elif list_len >= 3:
										getGestName = str_list[list_len-2]+'.'+str_list[list_len-1]
										
									print(getGestName)
									
									time.sleep(0.1)
									
									'''
									Thank you. I will send them a message
									'''
									play_music("mpg123 /home/respeaker/twilio/message.mp3")
									time.sleep(0.1)
									employeeNumber = search_user(''.join(employee).lower(),ENPATH,EN)
									print(employeeNumber)
									if employeeNumber == 0:
										print("Phone number error\n")
										return 0
									
									if TENCENT_TWILIO == True :
										TwilioSendMessage(employee,getGestName,employeeNumber)
									else:
										tencentSendMesaage(employee,getGestName,employeeNumber)
										
									print("********Bing_English****************")
									
									count = 0
									
									return 0
									
								else:
									count = count -1
									
							if 	count == 0 :
									return 0
									
								
				if is_find == False:
					
					#Oh, sorry, I didn't find it.
					
					is_music = False
				
					play_music('mpg123 /home/respeaker/twilio/notfind.mp3')
				

				
			else:
				return -1
				
		except Exception as e:               
			print(e.message)  
			

'''
Twilio,no used
'''			
def TwilioSendMessage(employee,gestName,employeeNumber):
	"""
	Some example usage of different twilio resources.
	"""
	client = Client(ACCOUNTSID, AUTHTOKEN)

	# Get all messages
	all_messages = client.messages.list()
	print('There are {} messages in your account.'.format(len(all_messages)))

	# Get only last 10 messages...
	some_messages = client.messages.list(limit=10)
	print('Here are the last 10 messages in your account:')
	for m in some_messages:
		print(m)

	# Get messages in smaller pages...
	all_messages = client.messages.list(page_size=10)
	print('There are {} messages in your account.'.format(len(all_messages)))
	print('Sending a message...')
	print('+86'+employeeNumber)
	print('Hello,'+employee+'.'+gestName+' is here to see you. Please meet them at the door.')
	#Hello, <employee>. <guest>  is here to see you. Please meet them at the door.
	new_message = client.messages.create(to='+86'+employeeNumber, from_='+15109014046', body='Hello,'+employee+'.'+gestName+' is here to see you. Please meet them at the door.')


def tencentSendMesaage(employee,gestName,employeeNumber):
	## Enum{0: 普通短信, 1: 营销短信}
	sms_type = 0
	template_id = 151036
	params = []
	params.append(employee)
	params.append(employeeNumber)
	
	ssender = SmsSingleSender(appid, appkey)
	try:
		
		
		sendStr = "Hello, "+employee+". "+gestName+" is here to see you. Please meet them at the door."
		print(sendStr)
		print(employeeNumber)
		result = ssender.send(sms_type, 86, employeeNumber,sendStr)
		#result = ssender.send(sms_type, 86, employeeNumber,"Hello,search.jcr is here to see you. Please meet them at the door.")
		# 签名参数未提供或者为空时，会使用默认签名发送短信
		#result = ssender.send_with_param(86, employeeNumber,template_id, params)  
		
	except HTTPError as e:
		print(e)
	except Exception as e:
		print(e)
	
	print('tencnet:{}'.format(result).decode('unicode_escape'))
	

def led_pixel_ring():
	
	pixel_ring.set_brightness(20)
	
	
	while led_ring :
		try:
			pixel_ring.wakeup()
			time.sleep(0.1)
			pixel_ring.off()
			time.sleep(0.1)
			pixel_ring.off()
		except KeyboardInterrupt:
			break

	pixel_ring.off()
	

'''
bing log
'''
def bing_api_call():
	logging.basicConfig(level=logging.DEBUG)
	
def recv_string():
	global recvok 
	while recvok != True:
		time.sleep(0.1)
	
	recvok = False
	print(stringcopy)
	return stringcopy	
		
'''
 parse local file
'''
def search_user(user,path,encn):
	print(len(user))
	print(user)
	print(path)
	print(encn)
	
	'''
	'''
	cf = ConfigParser.ConfigParser()
	cf.read(path)
	
	if True == encn :
		is_ = cf.has_option("db", user[0:len(user)-3])
	else:
		is_ = cf.has_option("db", user)
	
	print(is_)
	
	if is_ :
		if True == encn :
			db_phone = cf.get("db", user[0:len(user)-3])
		else:
			db_phone = cf.get("db", user)
			
		print(db_phone)
		
		if db_phone.isdigit() :
			return db_phone
		else:
			return 0;
	else:
		return 0;


		
def bing_init(self):
	text = ""
	bing = BingSpeechAPI(key=BING_KEY)
	try:                      
		fd = open(self.path)
		conect = fd.read(-1)
		text = bing.recognize(conect)
		fd.close()
		return text
	except Exception as e:               
			print(e.message)
			return text
			


		
	
'''
 call 调用
'''
def pre_play(v):
    global is_pressed,is_music,is_record,is_noteinfo,led_ring,parse_flags
	
	
    while True:
        if is_pressed  == True:
			'''
			Welcome to x.factory. Who are you here to see?
			'''
			
			os.system("mpg123 /home/respeaker/twilio/welcome.mp3") 
			
				
			is_pressed	= False
			
						
			try:
				
				'''
				数据解析及电话连线使能
				'''
				#global is_music
				
				is_music	= True
				
				par = speech_server_scheduler('/home/respeaker/twilio/test.wav', 'wav')
				
				'''
				bing api call
				'''
				
				if par.bing__parse_speech() == 0 :
					is_music	= False	
					parse_flags = False
				else:
					parse_flags = True
						
				is_music	= False
					
			except Exception,e:
				is_music 	= False
				is_noteinfo = False
				print e.message
			led_ring 	= False
	time.sleep(0.1)


'''
访客按键处理
'''		
def key_hander(v):
	global is_pressed,is_noteinfo,led_ring,starttime,lasttime

	
	key = InputDevice("/dev/input/event0")
	for event in key.read_loop():
		
		if event.type == ecodes.EV_KEY:
			#print(categorize(event)) 
			
			
			'''
			hold time
			'''
			if event.value == 2 :
				lasttime = event.sec
				sp_time = lasttime - starttime 
				'''
				down
				'''
			elif event.value == 1 :
				starttime = event.sec
				'''
				up
				'''
			else:
				led_ring 	= True
				is_pressed 	= True
				is_noteinfo = True
				starttime = 0
				lasttime  = 0
				
			
			
		

				

		
				
def play_music(strInfo):
		os.system(strInfo)

				

	
'''
 CTRL + C
'''
def CtrlC(signum, frame):
	os.kill(os.getpid(),signal.SIGKILL)

	
'''
 main  start ...
'''
if __name__ == "__main__":
	try:
		src = Source(channels=8)
		ch0 = ChannelPicker(channels=src.channels, pick=0)
		ns = NS()
		
		bing = Bing(BING_KEY)
		
		src.pipeline(ch0, ns, bing)
		
		bing_api_call()
		
		'''
		调试时CTRL + C 处理
		'''
		signal.signal(signal.SIGINT, CtrlC)
		signal.signal(signal.SIGTERM, CtrlC)

		thread_key  	= threading.Thread(target=key_hander,args=(1,))
		thread_play 	= threading.Thread(target=pre_play, args=(1,))
		
		
		thread_key.setDaemon(True)
		thread_play.setDaemon(True)
		
		
		thread_key.start()
		thread_play.start()
			
		
		src.recursive_start()
		
		if TREAD_ON == ON :
			thread_key.join()
			thread_play.join()
			
			
			
		else :
			while True:
				led_pixel_ring()
				time.sleep(1)
				pass
			
		'''
		异常处理
		'''	
	except Exception,exc:
		print exc
	
	
