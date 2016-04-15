#!/usr/bin/env python

from datetime import datetime

import os
import pytz
import shutil
import subprocess


_ROOT = 'gs://mc-project-1199-minecraft-backup/' 
_DEST = '/home/minecraft'
_GSUTIL = '/usr/bin/gsutil'
_WORLD = _DEST + '/world'


def _ConvertTime(date, hour):
  """ Converts date & hour in NY time to UTC.

  Args:
    date: string YYYYMMDD (eg: '20160413')
    hour: string HHMMSS (eg: '025945')
  """
  from_zone = pytz.timezone('America/New_York')
  year = int(date[:4])
  month = int(date[4:6])
  day = int(date[6:])
  hr = int(hour[:2])
  minute = int(hour[2:4])
  secs = int(hour[4:])
  from_date = from_zone.localize(datetime(year, month, day, hr, minute, secs))
  return pytz.utc.normalize(from_date)


def _GetGCSFileName(date, hour):
  utc_time = _ConvertTime(date, hour)
  utc_date = "%04d%02d%02d" % (utc_time.year, utc_time.month, utc_time.day)
  utc_hour = "%02d" % utc_time.hour
  wildcard = _ROOT + utc_date + '-*-world/'
  proc = subprocess.Popen([_GSUTIL, 'ls', wildcard], stdout=subprocess.PIPE)
  (out, err) = proc.communicate()
  result = []
  for path in out.splitlines(): 
    if path[-1:] == ':' and path[-14:-12] == utc_hour:
      return path[:-1]
  return ""


def _DownloadWorld(world_dir):
  """Download from GCS.

  Args:
    world_dir: full path to world (e.g. 'gs://mc-project-1199-minecraft-backup/20160412-010001-world/')
  """
  proc = subprocess.Popen([
      _GSUTIL,
      '-m',
      'cp',
      '-R',
      world_dir,
      _DEST],
      stdout=subprocess.PIPE)
  (out, err) = proc.communicate()


def _ShutDownServer():
  proc = subprocess.Popen([
      'screen',
      '-S',
      'mcs',
      '-X',
      'stuff',
      '/stop\n'],
      stdout=subprocess.PIPE)
  (out, err) = proc.communicate()


def _ReplaceWorld(world_dir):
  """Replace current world with the contents copied from world_dir.

  Args:
    world_dir: full path to world (e.g. 'gs://mc-project-1199-minecraft-backup/20160412-010001-world/')
  """
  backup_dir = world_dir.split('/')[-2]
  
  shutil.rmtree(_WORLD)
  shutil.move(_DEST + '/' + backup_dir, _WORLD)


def _StartServer():
  os.chdir(_DEST)
  proc = subprocess.Popen([
      'screen',
      '-d',
      '-m',
      '-S',
      'mcs',
      'java',
      '-Xms6G',
      '-Xmx6G',
      '-d64',
      '-jar',
      'minecraft_server.1.9.2.jar',
      'nogui'],
      stdout=subprocess.PIPE)
  (out, err) = proc.communicate()


def main():
  world_dir = _GetGCSFileName('20160311', '210103')
  print world_dir
  _DownloadWorld(world_dir)
  print 'Shutting down server'
  _ShutDownServer()
  print 'Resetting world'
  _ReplaceWorld(world_dir)
  print 'Restarting server'
  _StartServer()


if __name__ == "__main__":
  main()
