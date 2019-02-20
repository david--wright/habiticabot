import boto3
import requests

def _addGroupUser(group, user):
  client = boto3.resource('dynamodb')
  regTable = client.Table(DYNAMO_REG_TABLE)
  groupTable = client.Table(DYNAMO_GROUP_TABLE)
  botTable = client.Table(DYNAMO_BOT_TABLE)
  status=False
  try:
    response = botTable.get_item(
      Key={
        'name': 'id'
          }
      )
    botId=response['Item']
  except ClientError as e:
    return (status, e.response['Error']['Message'])
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
    result = groupTable.put_item(Item= {'group':  group, 'user': user})

    status = True
  else:
    message = "Unable to add User to group. Please have the user register with the bot."
    status=False
    _kickGroupUser(group, user)
  _sendTelegramMessage(message, group, botId)
  return (status, result)

def _command_start(message):
  pass

def _command_status(message):
  pass

def _command_register(message):
  pass

def _deleteGroupUser(group, user):
  pass

def _getTaskData(userId, userKey, task_type='dailys'):
  payload = {'type': task_type}
  headers = {'x-api-key':userKey, 'x-api-user':userId}
  r = requests.get("https://habitica.com/api/v3/tasks/user",params=payload,headers=headers)
  return r

def _kickGroupUser(group, user):
  pass

def _parseBotCommands(message):
  if 'text' in message:
    if len(message['text']) > 1:
      spiltCommand = message['text'].split()
      command = splitCommand[0][1:]
      options = splitCommand[1:]
    else:
      command = message['text'][1:]
      options = []
    methodResult = getattr(self, '_command_'+command)(options)
  elif 'new_chat_member' in message:
    methodResult = _addGroupUser
  elif 'left_chat_member' in message:
    methodCall = _deleteGroupUser
  return methodResult

def _sendTelegramMessage(message, group, botId):
  payload = {'chat_id': group, 'text': message}
  r = requests.post("https://api.telegram.org/{:s}/sendMessage".format(botId),params=payload)
  return r

def botHandler(event, context):
  pass

def habiticaHandler(event, context):
  pass