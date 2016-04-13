#!/usr/bin/env python

from datetime import datetime

import pytz
import subprocess

_ROOT = 'gs://mc-project-1199-minecraft-backup/' 


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
  result = pytz.utc.normalize(from_date)
  #import pdb; pdb.set_trace()
  return result


def _GetGCSFileName(date, hour):
  utc_time = _ConvertTime(date, hour)
  utc_date = "%04d%02d%02d" % (utc_time.year, utc_time.month, utc_time.day)
  utc_hour = "%02d" % utc_time.hour
  wildcard = _ROOT + utc_date + '-*-world/'
  proc = subprocess.Popen(['/usr/bin/gsutil', 'ls', wildcard], stdout=subprocess.PIPE)
  (out, err) = proc.communicate()
  result = []
  for path in out.splitlines(): 
    if path[-1:] == ':' and path[-14:-12] == utc_hour:
      return path[:-1]
  return ""


def main():
  result = _GetGCSFileName('20160411', '210103')
  print result


if __name__ == "__main__":
  main()
