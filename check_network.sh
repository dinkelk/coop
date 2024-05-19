#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <IP_Address_To_Ping>"
    exit 1
fi

PING_IP="$1"                     # Can use 8.8.8.8 for Google DNS
CONNECTIVITY_CHECK_INTERVAL=30   # Check every 30 seconds
MAX_DOWN_TIME_RESTART_WIFI=120   # Restart WiFi after 2 minutes
MAX_DOWN_TIME_REBOOT=600         # Reboot system after 10 minutes

RECONNECT_CMD="/sbin/ifconfig wlan0 down && sleep 5 && /sbin/ifconfig wlan0 up"
REBOOT_CMD="/sbin/reboot"

THIS_DIR=`readlink -f "${BASH_SOURCE[0]}" | xargs dirname`
LOG_FILE=$THIS_DIR/log/check_network.log

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >>$LOG_FILE 2>>$LOG_FILE
}

log "Starting up. Checking network via $PING_IP."
disconnect_time=0
while true; do
  if ping -c 1 $PING_IP >/dev/null; then
    log "Network is up."
    disconnect_time=0
  else
    ((disconnect_time=disconnect_time+CONNECTIVITY_CHECK_INTERVAL))
    log "Network has been down for $disconnect_time seconds."
    
    if ((disconnect_time>=MAX_DOWN_TIME_REBOOT)); then
      log "Rebooting..."
      $REBOOT_CMD
    elif ((disconnect_time>=MAX_DOWN_TIME_RESTART_WIFI)); then
      log "Restarting Wi-Fi connection..."
      $RECONNECT_CMD
      disconnect_time=0
    fi
  fi
  sleep $CONNECTIVITY_CHECK_INTERVAL
done
