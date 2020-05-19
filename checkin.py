import requests
import json
import sys

from login import login

'''
usage: python checkin.py [username] [password]
or: python checkin.py [cookie:SAAS_U]
'''

username = ""
password = ""
cookie = ""
use_cookie = False

if len(sys.argv) == 2:
    cookie = sys.argv[1]
    use_cookie = True
elif len(sys.argv) == 3:
    username = sys.argv[1]
    password = sys.argv[2]
else:
    print("Usage: python checkin.py [username] [password]")
    print("   or: python checkin.py [cookie:SAAS_U]")
    sys.exit(1)

http_header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/81.0.4044.138 Safari/537.36',
    'Referer': 'https://xmuxg.xmu.edu.cn/xmu/login?app=214'
}

# create session
session = requests.Session()

# login
login(session, username, password, cookie, use_cookie, http_header)

# get form id
now_url = "https://xmuxg.xmu.edu.cn/api/app/214/business/now"
resp = session.get(now_url).text
form_id = str(json.loads(resp)['data'][0]['business']['id'])

# get form instance
form_url = "https://xmuxg.xmu.edu.cn/api/formEngine/business/%s/formRenderData?playerId=owner" % form_id
resp = session.get(form_url, headers=http_header).text
form_components = json.loads(resp)["data"]["components"]

# get owner modification
form_instance_url = "https://xmuxg.xmu.edu.cn/api/formEngine/business/%s/myFormInstance" % form_id
resp = session.get(form_instance_url, headers=http_header).text
form_json = json.loads(resp)["data"]
instance_id = form_json["id"]

print("Logged in as: %s" % form_json["owner"]["name"])

# change form content
value_list = {}
for (k, v) in enumerate(form_json["formData"]):
    name = v['name']
    hide = v['hide']
    title = v['title']
    value = {}

    if "学生本人是否填写" in title:
        value['stringValue'] = '是'
    elif "Can you hereby declare that" in title:
        value['stringValue'] = '是 Yes'
    elif v['value']['dataType'] == 'STRING':
        value['stringValue'] = v['value']['stringValue']
    elif v['value']['dataType'] == 'ADDRESS_VALUE':
        value['addressValue'] = v['value']['addressValue']

    value_list[name] = {
        'hide': hide,
        'title': title,
        'value': value
    }

# prepare post data
post_array = []
for item in form_components:
    name = item['name']
    if name in value_list:
        post_array.append({
            'name': name,
            'hide': True if value_list[name]['hide'] else False,
            'title': value_list[name]['title'],
            'value': value_list[name]['value']
        })
    else:
        post_array.append({
            'name': name,
            'hide': False,
            'title': item['title'],
            'value': {}
        })


# post change
post_modify_url = "https://xmuxg.xmu.edu.cn/api/formEngine/formInstance/" + instance_id
post_json = {
    "formData": post_array,
    "playerId": "owner"
}
post_json_str = json.dumps(post_json, ensure_ascii=False, indent=4)
http_header['Content-Type'] = 'application/json'
http_header['Referer'] = 'https://xmuxg.xmu.edu.cn/index'
resp = session.post(post_modify_url, headers=http_header, data=post_json_str.encode('utf-8'))

print("Automatically checked in successfully!")