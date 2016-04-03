#!/usr/bin/env python

from collections import defaultdict
from datetime import datetime

import gzip
import os
import pytz
import re


_LOG_DIR = '/home/minecraft/logs'

_HEADER = """
<html>
  <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {'packages':['timeline']});
      google.charts.setOnLoadCallback(drawChart);
      function drawChart() {
        var container = document.getElementById('timeline');
        var chart = new google.visualization.Timeline(container);
        var dataTable = new google.visualization.DataTable();

        dataTable.addColumn({ type: 'string', id: 'User' });
        dataTable.addColumn({ type: 'date', id: 'Start' });
        dataTable.addColumn({ type: 'date', id: 'End' });
        dataTable.addRows([
"""


_FOOTER = """
        ]);

        chart.draw(dataTable);
      }
    </script>
  </head>
  <body>
    <div id="timeline" style="height: 1000px;"></div>
  </body>
</html>
"""


def ConvertTime(date, line):
  from_zone = pytz.timezone('UTC')
  to_zone = pytz.timezone('America/New_York')
  if date.startswith('latest'):
    date = str(datetime.now().date())
  utc = datetime.strptime(date + ' ' + line[1:9], '%Y-%m-%d %H:%M:%S')
  return utc.replace(tzinfo=from_zone).astimezone(to_zone)


def ToRows(results):
  rows = []
  for user in results:
    for pair in results[user]:
      row = ['          [ \'']
      row.append(user)
      row.append('\', new Date(')
      row.append(str(pair[0].year))
      row.append(', ')
      row.append(str(pair[0].month - 1))
      row.append(', ')
      row.append(str(pair[0].day))
      row.append(', ')
      row.append(str(pair[0].hour))
      row.append(', ')
      row.append(str(pair[0].minute))
      row.append(', ')
      row.append(str(pair[0].second))
      row.append('), new Date(')
      row.append(str(pair[1].year))
      row.append(', ')
      row.append(str(pair[1].month - 1))
      row.append(', ')
      row.append(str(pair[1].day))
      row.append(', ')
      row.append(str(pair[1].hour))
      row.append(', ')
      row.append(str(pair[1].minute))
      row.append(', ')
      row.append(str(pair[1].second))
      row.append(') ],')
      rows.append(''.join(row))
  return '\n'.join(rows)

      
class LogAnalyzer(object):
  def __init__(self, log_dir=None, start=None, end=None):
    """Initialize Analyzer.
    
    Args:
      log_dir: fully qualified location of the logs.
      start: datetime.datetime (None => include earliest)
      end: datetime.datetime (None => include latest)
    """
    
    if log_dir:
      self.log_dir = log_dir
    else:
      self.log_dir = _LOG_DIR
    self._start_times = defaultdict(set)
    self._end_times = defaultdict(set)
    self._result = defaultdict(list)
    self._server_stop_times = []
    self._start = start
    self._end = end
    
  def _analyzeLine(self, line, date, data):
    """Grabs the time and user_name from a log line.

    Assumes a very rigid structure of the log line.

    Args:
      line: string (e.g. "[19:36:55] [Server thread/INFO]: GoodGuyPapa joined the
                         game")
      date: string (e.g. "2016-03-28" taken from a filename like
                    2016-03-28-1.log.gz)
      data: dict where to put the result (e.g. self._start_times) 
    """
    user = re.search(': (.*)', line).group().split()[1]
    data[user].add(ConvertTime(date, line))

  def _analyzeFile(self, filename):
    """Iterate over each line in a given log file.

    TODO(creich): Add error checking for file open problems.

    Args:
      filename: fully qualifed filename (e.g.
                '/home/minecraft/logs/2016-03-28-1.log.gz')
    """
    date = os.path.basename(filename)[:10]
    if filename.endswith('gz'):
      f = gzip.open(filename)
    else:
      f = open(filename)
    lines = f.read().splitlines()
    for line in lines:
      if re.search('joined the game', line):
        self._analyzeLine(line, date, self._start_times)
      elif re.search('left the game', line) or re.search('lost connection',
          line):
        self._analyzeLine(line, date, self._end_times)
      elif re.search('Stopping server', line):
        self._server_stop_times.append(ConvertTime(date, line))

  def _analyzeLogs(self):
    files = os.listdir(self.log_dir)

    for f in files:
      self._analyzeFile(os.path.join(self.log_dir, f))

  def _adjustRange(self, start, end):
    """Return a (start, end) pair in range, or (None, None)."""
    adjusted_start = start
    if self._start:
      if end < self._start:
        return None
      adjusted_start = max(self._start, start)
      
    adjusted_end = end
    if self._end:
      if self._end < start:
        return None
      adjusted_end = min(self._end, end)
      
    return (adjusted_start, adjusted_end)
    
  def _zipTimes(self, user):
    """Match all start and end times for a given user.
    
    Assumes more starts than ends.
    
    Args:
      user: string (e.g. GoodGuyPapa)

    Returns:
      list of pairs [(start_time, end_time), ...]
    """
    starts = sorted(self._start_times[user])
    ends = sorted(self._end_times[user])
    result = []
    if len(starts) == len(ends):
      for i in xrange(len(starts)):
        interval = self._adjustRange(starts[i], ends[i])
        if interval:
          result.append(interval)
      return result

    start_idx = 0
    end_idx = 0
    while end_idx < len(ends):
      interval = self._adjustRange(starts[start_idx], ends[end_idx])
      if start_idx == len(starts) - 1:
        if interval:
          result.append(interval)
        break
      else:
        if interval:
          result.append(interval)
        if end_idx == len(ends) - 1:
          break
        while starts[start_idx + 1] < ends[end_idx]:
          start_idx += 1
        start_idx += 1
        end_idx += 1
          
    return result  

  def Analyze(self):
    """Iterates over logs and retains login/logoff times within start/end."""
    
    self._analyzeLogs()
    for user in self._start_times:
      self._result[user] = self._zipTimes(user)


def GenerateChart():
  logAnalyzer = LogAnalyzer()
  logAnalyzer.Analyze()
  return ''.join([_HEADER, ToRows(logAnalyzer._result), _FOOTER])
  
  
def main():
  print GenerateChart()


if __name__ == "__main__":
  main()
