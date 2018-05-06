# Soccer Stats

This module aims to develop statistics for soccer, powered by [Torneo](www.torneo.ca) data

## Settings File

The sensitive information is stored in a settings.json file in the folder where soccer_stat is stored, so to avoid sharing sensitive information via GitHub.
The settings file has the following structure:

```javascript
{
  "torneo":{
    "remote_host": "xxx.xxx.xx.xxx",
    "remote_ssh_port": xx,
    "ssh_pkey": "/<path>/<to>/<private key>/id_rsa",
    "dbname": "xxxxxxxxx",
    "dbuser": "xxxxxxxxx",
    "dbpassword": "xxxxxxxxxxxxxxxxxxxxx",
    "port": xxxx
  }
}
```

Bear in mind that at this point in order to user the module the user needs ssh access to the server with their local machine.
