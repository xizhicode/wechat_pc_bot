import requests
# data = {'dialog_name': 'Python开发_通知专用', 'message': 'hello机器人'}
data = {'dialog_name': "文件传输助手", 'message': 'hell11o'}
res = requests.post('http://192.168.8.140:99/send_message', data=data)
print(res.json())