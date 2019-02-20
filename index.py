import boto3
import requests

def _addGroupUser(group, user):
  client = boto3.resource('dynamodb')
  regTable = client.Table(DYNAMO_REG_TABLE)
  try:
    response = regTable.get_item(
      Key={
        'user': user
          }
      )
  except ClientError as e:
    return (e.response['Error']['Message'])
  else:
    userData = response['Item']
#TODO: Check if user is registered and if so add them to group. Otherwise
# return instructions for registering

  # table.put_item(Item= {'Group':  group, 'user': group})

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

def _parseBotCommands(message):
  if 'text' in message:
    methodCall = '_command_'+message['text'].split()[0][1:]
  elif 'new_chat_member' in message:
    methodCall = _addGroupUser
  elif 'left_chat_member' in message:
    methodCall = _deleteGroupUser
  return methodCall()

def _sendTelegramMessage(message, group, botId):
  payload = {'chat_id': group, 'text': message}
  r = requests.post("https://api.telegram.org/{:s}/sendMessage".format(botId),params=payload)
  return r

def botHandler(event, context):
  pass

def habiticaHandler(event, context):
  pass