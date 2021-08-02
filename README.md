# hysen2pfc

Support for Hysen 2 Pipe Fan Coil Controller. 

Hysen HY03AC-1-Wifi device and derivative.

Home Assistant config:

```
climate:
  - platform: hysenheating
    name: Living
    host: 192.168.100.150
    mac: '78:0f:77:ea:72:2d'
    timeout: 10
    sync_clock: false
    sync_hour: 4
```

timeout, sync_clock and sync_hour are optional.

