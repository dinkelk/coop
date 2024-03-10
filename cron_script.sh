#!/bin/bash -e

#
# To ensure the app starts when the pi is powered on,
# add the following to your crontab by running
# "crontab -e":
#
# @reboot /home/pi/coop/cron_script.sh
#

this_dir=`readlink -f "${BASH_SOURCE[0]}" | xargs dirname`
. $this_dir/venv/bin/activate
log=$this_dir/log/app.log
python $this_dir/src/app.py >>$log 2>>$log
