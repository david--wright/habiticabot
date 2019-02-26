import boto3
import json
import os
import requests
from botocore.exceptions import ClientError

def _addGroupUser(user, data):
  status = False
  userData = _getUser(user['id']) 
  if not userData:
    message = "Unable to add User to group. Please have the user register with {:s}.".format(data['botName'])
    status=False
    _kickGroupUser(user, data)
    _sendTelegramMessage(message, data['chat']['id'], data['botId'])
    result = "No matching registered user"
  else: 
    groupData = _getGroup(data['chat']['id'])
    alreadyExists = False
    if groupData:
      if user['id'] not in groupData['members']:
        groupData['members'].add(str(user['id']))
        result = _putGroup(groupData)
      else:
        alreadyExists = True
        result = "User previously registered"
    else:
      groupData = {'id':  str(data['chat']['id']), 'members': {str(user['id'])}}
      result = _putGroup(groupData)
    
    if alreadyExists:
      message = "{:s} is already a member of the group.".format(userData['username'])
    elif 'username' in userData:
      message = "{:s} added to group.".format(userData['username'])
    else:
      message = "{0:s} added to group. {0:s} does not have a username set so detailed status lookups will be unavailable in the group".format(userData['first_name'])
    _sendTelegramMessage(message, data['chat']['id'], data['botId'])
    status = True
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
  if message['chat']['type'] == 'private':
    _getIndividualStatus(message['from']['id'])
  elif options:
    for username in options:
      _getIndividualStatus(username)
  else:
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
  habiticaData=_getHabiticaUserData(user['apiId'], user['apiKey'])
  if 'data' in habiticaData:
    userRegistered = "Registered you as Habatica User {:s}".format(habiticaData['data']['profile']['name']) 
    status = True
  else:
    userRegistered = "Are you sure that you exist? Habatica claims that there is no account that uses those credentials."
    status = False
  _sendTelegramMessage(userRegistered, data['chat']['id'], data['botId'])
  return {'success': status, 'result': habiticaData, 'data': data}

def _getGroup(groupId):
  if os.getenv("AWS_SAM_LOCAL", ""):
    client = boto3.resource('dynamodb',
                          endpoint_url='http://dynamodb:8000')
    DYNAMO_GROUP_TABLE = "telegramGroupUsers"
  else:
    client = boto3.resource('dynamodb')
  groupTable = client.Table(DYNAMO_GROUP_TABLE)
  try:
      response = groupTable.get_item(
      Key={
        'id': str(groupId)
          }
      )
  except ClientError:
    groupData = None
  else:
    if 'Item' in response:
      groupData = response['Item']
    else: 
      groupData = None
  return groupData

def _getGroupStatusSummary(groupId):
  pass

def _getHabiticaUserData(userId, userKey):
  payload = {}
  headers = {'x-api-key':userKey, 'x-api-user':userId}
  r = requests.get("https://habitica.com/api/v3/user",params=payload,headers=headers)
  return r.json()

def _getIndividualStatus(user):
  pass

def _getTaskData(userId, userKey, task_type='dailys'):
  payload = {'type': task_type}
  headers = {'x-api-key':userKey, 'x-api-user':userId}
  r = requests.get("https://habitica.com/api/v3/tasks/user",params=payload,headers=headers)
  return r.json()

def _getUser(userId):
  if os.getenv("AWS_SAM_LOCAL", ""):
    client = boto3.resource('dynamodb',
                          endpoint_url='http://dynamodb:8000')
    DYNAMO_REG_TABLE = "habiticaUsers"
  else:
    client = boto3.resource('dynamodb')
  regTable = client.Table(DYNAMO_REG_TABLE)
  try:
    response = regTable.get_item(
    Key={
      'id': str(userId)
        }
    )
  except ClientError:
    userData = None
  else:
    if 'Item' in response:
      userData = response['Item']
    else: 
      userData = None
  return userData

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

def _putGroup(groupData):
  if os.getenv("AWS_SAM_LOCAL", ""):
    client = boto3.resource('dynamodb',
                          endpoint_url='http://dynamodb:8000')
    DYNAMO_GROUP_TABLE = "telegramGroupUsers"
  else:
    client = boto3.resource('dynamodb')
  groupTable = client.Table(DYNAMO_GROUP_TABLE)
  response = groupTable.put_item(
    Item = groupData
  )
  return response

def _putUser(user):
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
  return response

def _sendTelegramMessage(message, group, botId):
  payload = {'chat_id': group, 'text': message}
  r = requests.post("https://api.telegram.org/{:s}/sendMessage".format(botId),params=payload)
  return r

def botHandler(event, context):
  result = _parseBotCommands(json.loads(event['body'])['message'],event['pathParameters']['botId'], event['pathParameters']['botName'])
  return {"statusCode": 200, 'body': json.dumps(result)}

def habiticaHandler(event, context):
  pass