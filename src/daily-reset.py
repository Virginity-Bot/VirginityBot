import os
import asyncio
import http.client
import json
import logging

from dotenv import load_dotenv
from pony.orm import *

import logger
from database import start_orm, get_biggest_virgin, Guild

logger = logging.getLogger('virginity-bot')


load_dotenv()
TOKEN = str(os.getenv('DISCORD_TOKEN'))

HOSTNAME = 'discordapp.com'
API_PATH = f'https://{HOSTNAME}/api'


async def award_omega_virgin_roles():
  con = http.client.HTTPSConnection(HOSTNAME)
  headers = {
      'Content-Type': 'application/json',
      'Content-Length': '0',
      'Authorization': f'Bot {TOKEN}'
  }

  with db_session:
    guilds = Guild.select()
    for guild in guilds:
      if guild.biggest_virgin_role_id == None:
        continue
      else:
        omega_virgin = get_biggest_virgin(guild.id)
        logger.info(f'{omega_virgin.name} is {guild.name}\'s biggest virgin')

        con.request(
            'DELETE', f'{API_PATH}/guilds/{guild.id}/roles/{guild.biggest_virgin_role_id}', headers=headers)
        res = con.getresponse()
        if res.getcode() == 204:
          logger.info('Deleted old role')
        con.close()

        body = json.dumps({
            'name': 'Chonkiest Virgin the World has Ever Seen',
            'color': '12911440',
            'hoist': True,
            'mentionable': True
        })
        headers['Content-Length'] = len(body)
        con.request(
            'POST', f'{API_PATH}/guilds/{guild.id}/roles', headers=headers, body=body)
        res = con.getresponse()
        bod = res.read()
        new_role = json.loads(bod.decode())
        con.close()
        if res.getcode() == 200:
          guild.biggest_virgin_role_id = new_role['id']
          commit()
          logger.info('Created new role')
        else:
          logger.error('Failed to create role')
          raise Exception('Failed to create role')

        headers['Content-Length'] = '0'
        con.request(
            'PUT', f'{API_PATH}/guilds/{guild.id}/members/{omega_virgin.id}/roles/{guild.biggest_virgin_role_id}', headers=headers)
        res = con.getresponse()
        con.close()
        if res.getcode() == 204:
          logger.info('Added role to biggest virgin')


async def main():
  logger.info('Running daily reset')
  start_orm()
  await award_omega_virgin_roles()


if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())
