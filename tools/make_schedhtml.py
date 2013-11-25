#!/usr/bin/python
import argparse
import sys
import datetime
import string
from radar_modes import *
import calendar

# This program steals a bunch from Jef Spaleta's python script to take the schedule file
# given to the Scheduling Working Group and convert it to a schedule file that can be used
# by the radars.  Here though the schedule file to the SWG is converted into a html table
# that can be posted on the web and easily viewed.  This has not been extensively tested
# but it seems to be mostly working for now.
#
# -KTS 12Feb2013

#Set Sunday as the first day in the week
calendar.setfirstweekday(6)
default_radar='kod'
radar='htmlscd'

#We'll use the alphabet for the notes section
alphabet=string.uppercase
alpha=0
months=['January','February','March','April','May','June','July','August','September','October','November','December']
month=None
year=None
has_default_priority=False
has_default_duration=False


# Don't need some of this parsing here, but do want to keep the schedule_file readin!
parser = argparse.ArgumentParser(description='Process schedule file')
parser.add_argument('-m', '--month',type=int,choices=range(1,13))
parser.add_argument('-o', '--output',default=None)
parser.add_argument('-v', '--verbose',default=False,action='store_true')
parser.add_argument('-y', '--year',type=int)
#parser.add_argument('-d', '--dsched',default=None,help="Discretionary schedule file")
#parser.add_argument('-x', '--ext',default="scd",help="File extention default: scd")
#parser.add_argument('-r', '--radar',default=default_radar,help="Radarname default: bks")
parser.add_argument('schedule_file', type=argparse.FileType('r'),help="SuperDARN input schedule text files")
opts=parser.parse_args()
#if opts.radar not in radars:
# print "Radar: \"%s\" not found in radar configuration please check radar_modes.py file" % (opts.radar)
# sys.exit(-1)
#stid=opts.radar[0:3]
#print "STID:",stid.upper()
stid='kod'

if opts.verbose:
  print "\n"
  print "Selected Radar STID: %s" %(opts.radar)
  print "  Understood Modes:"
  for mode in radars[opts.radar]["modes"].keys():
    print "  %s :: %s" % (mode,radars[opts.radar]["modes"][mode])
  print "\n"
#print opts
date_string=opts.schedule_file.readline().strip().split()
print date_string
try:
  if date_string[0] in months:
    month=months.index(date_string[0])+1
except: pass
try:
  if int(date_string[1]) >= datetime.datetime.now().year :
    year=int(date_string[1])
except: pass
#Here month gets set to a number
if opts.month is not None: month=opts.month
if opts.year is not None: year=opts.year
begin=datetime.datetime(year=year,month=month,day=1,hour=0,minute=0)
if month < 12:
  end=datetime.datetime(year=year,month=month+1,day=1,hour=0,minute=0)
else:
  end=datetime.datetime(year=year+1,month=1,day=1,hour=0,minute=0)
tdiff=end-begin
month_minutes=(int(tdiff.days*24*60) + int(tdiff.seconds/60.))

if opts.output is None:
#  filename="%s_%s-%04d.%s" % (opts.radar,months[month-1],year,opts.ext)
  filename="%s_%s-%04d.%s" % (radar,months[month-1],year,"html")
else:
  filename=opts.output
notes=0
f = open(filename, 'w')

#Writing header. Usual business although month and year changes
header="""<center>
<p>

<font size=5 color=#660000><b>{0} {1}</b></font>
<table border="3" bordercolor=#660000 width="95%">
<tr>
    <td width="14.2%"><b>Sunday</td>
    <td width="14.2%"><b>Monday</td>
    <td width="14.2%"><b>Tuesday</td>
    <td width="14.2%"><b>Wednesday</td>
    <td width="14.2%"><b>Thursday</td>
    <td width="14.2%"><b>Friday</td>
    <td width="14.2%"><b>Saturday</td>
</tr>"""

headerwrite=header.format(months[month-1],year)
f.write(headerwrite)

# Dates becomes an array of the days of the month where the rows are the
# weeks and the days of the week of the columns.
dates=calendar.monthcalendar(year, month)
#dates=calendar.HTMLCalendar(calendar.SUNDAY)
print "dates array is: %s" % dates

opts.schedule_file.seek(0)
#print "Finding Notes Section:"
#has_notes=False
lines=opts.schedule_file.readlines()

scd_minutes=0
opts.schedule_file.seek(0)
mode=""
firstnote=""
fontcolor=""
notelist=[None] * 50

# Hold over day number to try to match to, we shouldn't ever have 200 days in a month...right?
holdoverdy=200
holdovercp=''
holdoverft=''
h=0
newrow=True
cprunover=False
cp=''
#firstcp=False
# cycle through rows
for a in range(len(dates)):
  # cycle through columns
  for b in range(len(dates[0])):
    # Set date found to True later to mark that we found a schedule line for that date
    datefound=False
#    firstcp=True
#    print dates[a][b]
    # will match the leading zero at the beginning of dates
    if b is 0 and dates[a][b] is 0 and cprunover is False:
      htmlline="<tr>\n"
      htmlline+="<td height=100></td>\n"
      datefound=True
    # else if its not the first day of the week but it is a blank day then
    # put a blank entry for the cell
    elif b is not 0 and dates[a][b] is 0:
      htmlline="<td height=100></td>\n"
      datefound=True
    else:
      if b is 0 and cprunover is False:
        htmlline="<tr>\n"
      # Add in date as well as font size and starting bold.  Here the zfill makes the leading
      # zero appear for the date.
      if cprunover is False:
        htmlline+="<td height=100>%s<p style=\"font-size:10px;\"><b>" % (str(dates[a][b]).zfill(2))
#       print fontcolor
#       print cp
#       print holdoverft
#       print holdovercp
        if str(holdoverdy) in str(dates[a][b]).zfill(2):
#         print "got it!!!"
          htmlline+="%s0000-%s00 %s<br>" % (holdoverft, holdoverhr, holdovercp)
          holdoverdy=200
     # cycle through schedule file to try to find a match to dates[a][b]
#      print htmlline
      cprunover=False
      for i in range(len(lines)):
        line=lines[i]
        encoded_line=False
        if "# Notes" in line:
          break
        l=line.strip()
        # Look for actual lines as well as none comment lines
        if len(l) and (l[0] is not '#'):
          s=l.split()
          # Only look for lines not containing the special information
          if l[0] is not "[":
            # If s has 3 or more items
            if len(s) >= 3:
              # Setup font color for each type of control program, we'll use this later...maybe
              if s[2] in "Special":
                fontcolor="<font color=#FF0000>"
              elif s[2] in "Discretionary":
                fontcolor="<font color=#000000>"
              elif s[2] in "Common":
                fontcolor="<font color=#FF6600>"
              else:
                fontcolor="<font color=#660000>"
              start=s[0]
              startdy=start[0:2]
              starthr=start[3:5]
              end=s[1]
              enddy=end[0:2]
              endhr=end[3:5]
              cp=' '.join(s[2:5])
              # if the date in the box calendar is equal to the start day, zfill makes
              # the leading zero appear for the single digit days.
              if str(dates[a][b]).zfill(2) == startdy:
                datefound=True
                if str(starthr) in "00":
#                 print "first"
#                 print starthr
                  firstcp=True
                if s[2] in "Special":
                  specialAlpha= alphabet[alpha]
                  alpha+= 1
                if startdy in enddy and firstcp is True:
                  if s[2] in "Special":
                    htmlline+="%s0000-%s00 %s *(%s)*<br>" % (fontcolor, endhr, cp, specialAlpha)
                  else:
                    htmlline+="%s0000-%s00 %s<br>" % (fontcolor, endhr, cp)
                  firstcp=False
                elif startdy in enddy and firstcp is False:
                  if s[2] in "Special":
                    htmlline+="%s%s00-%s00 %s *(%s)*<br>" % (fontcolor, starthr, endhr, cp, specialAlpha)
                  else:
                    htmlline+="%s%s00-%s00 %s<br>" % (fontcolor, starthr, endhr, cp)
                # Odd case here since day ends are represented by the next day at 0000 utc.
                # Basically the cp runs to the end of the day, but does not overlap into the
                # next day.
                elif startdy is not enddy and endhr in "00":
                  if s[2] in "Special":
                    htmlline+="%s%s00-2400 %s *(%s)*</td>\n" % (fontcolor, starthr, cp, specialAlpha)
                  else:
                    htmlline+="%s%s00-2400 %s</td>\n" % (fontcolor, starthr, cp)
                  # Old line
#                 htmlline+="%s%s00-2400 %s</td>\n" % (fontcolor, starthr, cp)
#                 print "Start day: %s and end day: %s" % (startdy, enddy)
                elif startdy is not enddy and endhr not in "00":
                  cprunover=True
                  nextdy=int(startdy)+1
                  if str(nextdy).zfill(2) in enddy:
#                   print "Next day: %s" % (nextdy)
#                   print "End day: %s" % (enddy)
                    htmlline+="%s%s00-2400 %s</td>\n" % (fontcolor, starthr, cp)
                    nextdy=dates[a][b]+1
                    if b is 6:
                      htmlline+="</tr>\n<tr>\n"
                    htmlline+="<td height=100>%s<p style=\"font-size:10px;\"><b>%s0000-%s00 %s<br>" %(enddy, fontcolor, endhr, cp)
                  #else if the cprunover is more than a day long, just go ahead and do the next day
                  elif str(nextdy).zfill(2) not in enddy:
#                   print runoverdy
#                   print runoverhr
                    htmlline+="%s%s00-2400 %s</td>\n" % (fontcolor, starthr, cp)
                    if b is 6:
                      htmlline+="</tr>\n<tr>\n"
                    htmlline+="<td height=100>%s<p style=\"font-size:10px;\"><b>%s0000-2400 %s" %(nextdy, fontcolor, cp)
                    htmlline+="</td>\n"
                    holdoverdy=enddy
                    holdoverhr=endhr
                    holdoverft=fontcolor
                    holdovercp=cp
                    nextdaydone=True
#                 print "Start day: %s and end day: %s" % (startdy, enddy)
#                 print "Start hour: %s and end hour: %s" % (starthr, endhr)
#                 print "cp is: %s" % cp
#                 print "\n"

    # if we never found a date matched, go back to the last entry
      if datefound is False:
        print "Didn't find a date for: %s " % dates[a][b]
        for i in range(len(lines)):
          line=lines[i]
          encoded_line=False
          if "# Notes" in line:
            break
          l=line.strip()
          # Look for actual lines as well as none comment lines
          if len(l) and (l[0] is not '#'):
            s=l.split()
            # Only look for lines not containing the special information
            if l[0] is not "[":
              # If s has 3 or more items
              if len(s) >= 3:
                # Setup font color for each type of control program, we'll use this later...maybe
                start=s[0]
                startdy=start[0:2]
                # looping until we find the first line with a start date after current dates value
                if startdy > str(dates[a][b]).zfill(2):
#                 print "Startdy: %s" % startdy
#                 print "dates[a][b]: %s" %dates[a][b]
                  #read in the previous line here
                  line=lines[i-1]
                  l=line.strip()
                  s=l.split()
                  cp=' '.join(s[2:5])
                  if s[2] in "Special":
                    fontcolor="<font color=#FF0000>"
                  elif s[2] in "Discretionary":
                    fontcolor="<font color=#000000>"
                  elif s[2] in "Common":
                    fontcolor="<font color=#FF6600>"
                  else:
                    fontcolor="<font color=#660000>"
                  if nextdaydone is False:
#                   print htmlline
                    htmlline+="%s0000-2400 %s</td>\n" % (fontcolor, cp)
                  else:
#                   print "Found nextdaydone is True"
                    nextdaydone=False
                  break
    if b is 6 and cprunover is False:
      htmlline+="</tr>\n"

    f.write(htmlline)
    # clear out the htmlline
    htmlline=""


# Put this at the end to collect notes information
for i in range(len(lines)):
  line=lines[i]
  encoded_line=False
  write_line=False
  #Hardcoded note section capture...maybe need to make this more complex.
  if "# Notes" in line:
    print "Notes section found; printing to file"
    firstnote='''\n<br>
<br>
Notes:<br>
<br>\n'''
    firstnote+=lines[i+2]+"<br>"
    firstnote+=lines[i+3]+"<br>"
    firstnote+=lines[i+4]+"<br><br>"
    break
  l=line.strip()
  if len(l)  and (l[0] is not '#'):
    s=l.split()
    comment=""
    if l[0]=="[":
      write_line=True
      encoded_line=True
      ustid=stid.upper()
      ul=l.upper()
      c=ul.split('[',1)
      radlist=""
      if(len(c)==2) :
       radlist=c[1].split(']',1)[0]
       preradlist="[note %s]" % alphabet[h]
       notelist[h]=preradlist+radlist+"<br>"
       h +=1

    if encoded_line is False:
     if len(s) >= 3:
        start=s[0]
        startdy=start[0:2]
        starthr=start[3:5]
#        starttime=datetime.datetime(year=year,month=month,day=int(start[0:2]),hour=int(start[3:5]))
#       print starttime
        end=s[1]
        enddy=end[0:2]
        endhr=end[3:5]


# closes table and centering after table loop is finished
closer="\n</table></center>"
f.write(closer)

f.write(firstnote)
f.writelines( '%s\n' % item for item in notelist if item is not None )

f.close()

print "Output file at: %s" % filename
sys.exit()
