import boto3
import json
import os
import requests
from botocore.exceptions import ClientError

def _addGroupUser(user, data):
  client = boto3.resource('dynamodb')
  regTable = client.Table(DYNAMO_REG_TABLE)
  groupTable = client.Table(DYNAMO_GROUP_TABLE)
  status = False
  try:
    response = regTable.get_item(
      Key={
        'user': user
          }
      )
  except ClientError:
    userData = None
  else:
    if 'Item' in response:
      userData = response['Item']
    else: 
      userData = None
  if userData:
    result = groupTable.put_item(Item= {'group':  data['chat']['id'], 'user': user})
    message = "{:s} added to group.".format(userData['username'])
    status = True
  else:
    message = "Unable to add User to group. Please have the user register with the bot."
    status=False
    _kickGroupUser(user, data)
  _sendTelegramMessage(message, data['chat']['id'], data['botId'])
  return (status, result)

def _command_start(options, message, data):
  welcomeMessage = """
   Hi! I am fairly young so I might not work the way you want all the time. Just fair warning! If you still want to talk to me you can use the following commands:
   
   In a private chat with me:
   /start                  
          show this message.
   /register
          set your habatica api info.
   /status
          list what tasks you have left today.
   
   In a group chat with me:
   /start                  
          show this message.
   /status
          show group task status.
   /status <username>
          list tasks the user has left.
  """

  _sendTelegramMessage(welcomeMessage, data['chat']['id'], data['botId'])
  return {'success': True, 'result':"Welcome Message Sent"}

def _command_status(options, message):
  pass

def _command_register(options, message, data):
  if message['chat']['type'] != 'private':
    privateChatOnly = "/register is only available in private chats. \
Please contact {:s} in a private chat to register".format(data['botName']) 
    _sendTelegramMessage(privateChatOnly, data['chat']['id'], data['botId'])
    return {'status': False, 'result': privateChatOnly} 
  if len(options) < 2:
    moreOptionsNeeded = """/register requires that you send both your habitica api ID \
and your habitica api key. This should look like:
 /register this-is-my-api-id this-is-the-api-key"""
    _sendTelegramMessage(moreOptionsNeeded, data['chat']['id'], data['botId'])
    return {'status': False, 'result': moreOptionsNeeded} 
  user = message['from']
  user['id'] = str(user['id'])
  user['apiId'] = options[0]
  user['apiKey'] = options[1]
  user['privateChatId'] = data['chat']['id']
  if os.getenv("AWS_SAM_LOCAL", ""):
    client = boto3.resource('dynamodb',
                         endpoint_url='http://dynamodb:8000')
    DYNAMO_REG_TABLE = "habiticaUsers"
  else:
    client = boto3.resource('dynamodb')
  regTable = client.Table(DYNAMO_REG_TABLE)
  response = regTable.put_item(
    Item = user
  )
  habaticaData=_getHabiticaUserData(user['apiId'], user['apiKey'])
  userRegistered = "Registered you as Habatica User {:s}".format(habaticaData['data']['profile']['name']) 
  _sendTelegramMessage(userRegistered, data['chat']['id'], data['botId'])
  return {'success': True, 'result': response, 'data': data}
 
def _getTaskData(userId, userKey, task_type='dailys'):
  payload = {'type': task_type}
  headers = {'x-api-key':userKey, 'x-api-user':userId}
  r = requests.get("https://habitica.com/api/v3/tasks/user",params=payload,headers=headers)
  return r.json()

def _getHabiticaUserData(userId, userKey):
  payload = {}
  headers = {'x-api-key':userKey, 'x-api-user':userId}
  r = requests.get("https://habitica.com/api/v3/user",params=payload,headers=headers)
  return r.json()

def _kickGroupUser(user, data):
  pass

def _parseBotCommands(message, botId, botName):
  data = {"botId": botId, 'botName': botName}
  data['orig_user'] = message['from']
  data['chat'] = message['chat']
  if 'text' in message and message['text'][0] == '/':
    splitCommand = message['text'].split()
    if len(splitCommand) > 1:
      command = splitCommand[0][1:]
      options = splitCommand[1:]
    else:
      command = message['text'][1:]
      options = []
    methodResult = globals()['_command_'+command](options, message, data)
  elif 'new_chat_member' in message:
    user = message['new_chat_member']
    methodResult = globals()['_addGroupUser'](user, data)
  elif 'left_chat_member' in message:
    methodResult = globals()['_kickGroupUser'](user, data)
  return methodResult

def _sendTelegramMessage(message, group, botId):
  payload = {'chat_id': group, 'text': message}
  r = requests.post("https://api.telegram.org/{:s}/sendMessage".format(botId),params=payload)
  return r

def botHandler(event, context):
  result = _parseBotCommands(json.loads(event['body'])['message'],event['pathParameters']['botId'], event['pathParameters']['botName'])
  return {"statusCode": 200, 'body': json.dumps(result)}

def habiticaHandler(event, context):
  pass