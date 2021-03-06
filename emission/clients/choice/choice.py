# Standard imports
import logging
import math
import json
from uuid import UUID
from datetime import datetime, timedelta
import time

# Our imports
from emission.core.get_database import get_trip_db, get_section_db
import emission.analysis.result.carbon as carbon
import emission.core.common as common
import emission.net.api.stats as stats
from emission.core.wrapper.user import User
from emission.clients.leaderboard import leaderboard
from emission.clients.gamified import gamified
from emission.clients.recommendation import recommendation
from emission.clients.commontrips import commontrips
from emission.clients.data import data

# TODO: Consider subclassing to provide client specific user functions
def setCurrView(uuid, newView):
  user = User.fromUUID(uuid)
  user.setClientSpecificProfileFields({'curr_view': newView})
  stats.storeResultEntry(uuid, stats.STAT_VIEW_CHOICE, time.time(), newView)

def getCurrView(uuid):
  user = User.fromUUID(uuid)
  profile = user.getProfile()
  if profile is None:
    logging.debug("profile is None, returning data")
    return "data"
  logging.debug("profile.get('curr_view', 'dummy') is %s" % profile.get("curr_view", "data"))
  return profile.get("curr_view", "data")

def switchResultDisplay(params):
  logging.debug("params = %s" % (params))
  print "params = %s" % (params['uuid'])
  try:
    uuid = UUID(params['uuid'])
  except:
    uuid = "temp" ## For testing purposes 
  newView = params['new_view']
  logging.debug("Changing choice for user %s to %s" % (uuid, newView))
  setCurrView(uuid, newView)
  # TODO: Add stats about the switch as part of the final stats-adding pass
  return {'curr_view': newView }

def getResult(user_uuid):
  # This is in here, as opposed to the top level as recommended by the PEP
  # because then we don't have to worry about loading bottle in the unit tests
  from bottle import template
  import base64
  from dao.user import User
  from dao.client import Client

  user = User.fromUUID(user_uuid)

  renderedTemplate = template("clients/choice/result_template.html",
                          variables = json.dumps({'curr_view': getCurrView(user_uuid),
                                       'uuid': str(user_uuid),
                                       'client_key': Client("choice").getClientKey()}),
                          gameResult = base64.b64encode(gamified.getResult(user_uuid)),
                          leaderboardResult = base64.b64encode(leaderboard.getResult(user_uuid)),
                          dataResult = base64.b64encode(data.getResult(user_uuid)), 
                          commonTripsResult = base64.b64encode(commontrips.getResult(user_uuid)),
                          recommendationResult = base64.b64encode(recommendation.getResult(user_uuid)))

  return renderedTemplate

# These are copy/pasted from our first client, the carshare study
def getSectionFilter(uuid):
  # We are not planning to do any filtering for this study. Bring on the worst!
  return []

def clientSpecificSetters(uuid, sectionId, predictedModeMap):
  return None

def getClientConfirmedModeField():
  return None

# TODO: Simplify this. runBackgroundTasks are currently only invoked from the
# result precomputation code. We could change that code to pass in the day, and
# remove this interface. Extra credit: should we pass in the day, or a date
# range?  Passing in the date range could make it possible for us to run the
# scripts more than once a day...
def runBackgroundTasks(uuid):
  today = datetime.now().date()
  runBackgroundTasksForDay(uuid, today)

def runBackgroundTasksForDay(uuid, today):
  leaderboard.runBackgroundTasksForDay(uuid, today)
  gamified.runBackgroundTasksForDay(uuid, today)
  data.runBackgroundTasksForDay(uuid, today)
