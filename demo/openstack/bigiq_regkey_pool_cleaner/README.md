# bigiq_regkey_pool_cleaner
### Python Application To Remove Allocated License on Non Active OpenStack Ports ###

Often TMOS virtual editions instances, with an allocated license from a BIG-IQ license pool, can be deleted without first revoking the license. In such cases, BIG-IQ will never be able to communicate properly with the BIG-IP to revoke the license.

This repository containes a python script application which will query a specific BIG-IQ RegKey license pool by name for active licenses. An attempt to match the active licenses associated MAC address with a OpenStack Neutorn port will be made. If the OpenStack Neutron port is not ACTIVE, a revoke request will be made to the BIG-IQ for that allocated license. Provided tha the IP address assoicated with the license can not be reeached from BIG-IQ the license will be revoked and returned to the pool.

The script can also log all polled interactions. It creates simple ON or OFF log records for each pool. Any record specified as OFF will attempt to be revoked. The log format is as follows:

```
ON|OFF, machineId,                            created timestamp,        poll timestamp,           macAddress,        management IP:port
OFF,    b8e62faa-01d5-4474-9630-e41067146658, 2019-06-27T19:51:13.470Z, 2019-06-27T19:52:33.097Z, FA:16:3E:2B:7A:F5, 192.168.245.104:443
OFF,    88670c09-6c08-4466-be91-17565501d149, 2019-06-27T19:51:42.004Z, 2019-06-27T19:52:33.097Z, FA:16:3E:1B:9B:78, 192.168.245.116:443
ON,     cff0b45d-4643-4abb-a049-c875024095de, 2019-06-27T19:49:06.094Z, 2019-06-27T19:52:33.097Z, FA:16:3E:28:61:B9, 192.168.245.111:8443
```

The log can be directed to a file.

Control arguments for the python application script can be enumerated by using the `-h` (help) argument.

```
$ ./bigiq_regkey_pool_cleaner.py -h
usage: bigiq_regkey_pool_cleaner.py [-h]
                                    [-l {DEBUG,INFO,WARN,ERROR,CRITICAL,FATAL}]
                                    [-d] [-p POLL_CYCLE] [-r REPORT_FILE]
                                    [--bigiqhost BIGIQHOST]
                                    [--bigiqusername BIGIQUSERNAME]
                                    [--bigiqpassword BIGIQPASSWORD]
                                    [--licensepool LICENSEPOOL]
                                    [--os-project-name OS_PROJECT_NAME]
                                    [--os-project-domain-name OS_PROJECT_DOMAIN_NAME]
                                    [--os-username OS_USERNAME]
                                    [--os-user-domain-name OS_USER_DOMAIN_NAME]
                                    [--os-auth-url OS_AUTH_URL]
                                    [--os-password OS_PASSWORD]
                                    [--os-interface OS_INTERFACE]

optional arguments:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARN,ERROR,CRITICAL,FATAL}, --log-level {DEBUG,INFO,WARN,ERROR,CRITICAL,FATAL}
                        set logging level
  -d, --daemon          Run in deamon mode
  -p POLL_CYCLE, --poll-cycle POLL_CYCLE
                        How often to report and revoke, default 5 minutes
  -r REPORT_FILE, --report-file REPORT_FILE
                        the report log file
  --bigiqhost BIGIQHOST
                        BIG-IQ hostname or IP address
  --bigiqusername BIGIQUSERNAME
                        BIG-IQ username
  --bigiqpassword BIGIQPASSWORD
                        BIG-IQ password
  --licensepool LICENSEPOOL
                        BIG-IQ license pool name
  --os-project-name OS_PROJECT_NAME
                        OpenStack project name
  --os-project-domain-name OS_PROJECT_DOMAIN_NAME
                        OpenStack project domain name
  --os-username OS_USERNAME
                        OpenStack user name
  --os-user-domain-name OS_USER_DOMAIN_NAME
                        OpenStack user domain name
  --os-auth-url OS_AUTH_URL
                        OpenStack Keystone Auth URL
  --os-password OS_PASSWORD
                        OpenStack password
  --os-interface OS_INTERFACE
                        OpenStack authentication interface
```

The command line arguments can also be defined by environment variables, making use with docker simple.

```
$cat bigiq_regkey_pool_cleaner.sh.env
export LOGLEVEL=INFO
export LICENSEPOOLINTERVAL=300
export LICENSEREPORTFILE=/tmp/licensereport.txt
export BIGIQHOST=licenshost
export BIGIQUSERNAME=admin
export BIGIQPASSWORD=admin
export LICENSEPOOL=BIGIPVEREGKEYS
export OS_PROJECT_NAME=admin
export OS_PROJECT_DOMAIN_NAME=default
export OS_USERNAME=admin
export OS_USER_DOMAIN_NAME=default
export OS_AUTH_URL=https://cloudctlr:35357/v3
export OS_PASSWORD=admin
export OS_INTERFACE=public
```

You run the script as a daemon with the exported values from the env file.

```
$ source bigiq_regkey_pool_cleaner.sh.env; ./bigiq_regkey_pool_cleaner.py -d 
2019-06-27 15:12:22,136 - bigiq_regkey_pool_cleaner - DEBUG - Running in daemon mode, polling every 300 seconds
2019-06-27 15:12:22,136 - bigiq_regkey_pool_cleaner - DEBUG - Polling licenses in BIGIPVEREGKEYS pool
```

The repository comes with a Dockerfile to help you build a docker image of this application.

```
$ docker build -t bigiq_regkeypool_cleaner:latest demo/openstack/bigiq_regkey_pool_cleaner
```

To can simply run your container with a docker environment file.

```
$ docker run --rm -it --env-file ./demo/openstack/bigiq_regkey_pool_cleaner/bigiq_regkey_pool_cleaner.env bigiq_regkeypool_cleaner:latest
```

