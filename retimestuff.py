# coding=utf-8
__author__ = 'nen'


import datetime
from datetime import timedelta as delta

# ENTER IMPACT TIME/DATE HERE!!!
impact = datetime.datetime(year=2013, month=10, day=28, hour = 16, minute = 17, second = 36)

# ENTER HIS RUNNINGTIME HERE!
running_time = delta(hours=2, minutes= 30)

troop_return = impact + running_time

# ENTER RUNNINGTIME FOR VARIOUS TROOPS:
axe_running = delta(hours=1, minutes = 30)
sword_running = delta(hours = 1, minutes = 50)
light_running = delta(minutes = 50)


print "Impact time:                ", impact
print "His troops will be home at: ", troop_return
print ""
print "Time for sword retime: ", troop_return - sword_running
print "Time for axe retime:   ", troop_return - axe_running
print "Time for light retime: ", troop_return - light_running
