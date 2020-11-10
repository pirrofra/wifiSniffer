# wifiSniffer

wifiSniffer is an utility that analyzes Wifi Probe requests for counting people or tracking their movements.

## Configuration
Before deploying the utility, if you're planning to use it with a Zerynth Device, the content of auth.env must be changed:

```
WORKSPACEID='Workspace ID generated from ZDM'
JWT='Access Token of the ZDM account'
```


## Deployment

Use docker compose to run the utility.\
In the main directory of the repository use:

```bash
docker-compose build
docker-compose run
```
to run the framework.

## Firmware
To deploy scanner devices using the Zerynth Toolchain, a framework is provided. Just get the device id and token from the ZDM, and in the firmware change the value of `SSSID` and `password`, so the device can connect to the Internet and publish data.\
For more information about how to flash, deploy the firmware and get the device credentials from ZDM, visit [Zerynth](https://docs.zerynth.com/latest/) website.

## Usage
All services are published on the port `80`.
- The main route redirects to grafana
- POST request to `\api\rawData`for adding data
- POST request to `\api\room\<name>`, with `{"mac":"MAC ADDRESS"}` as an attachment, to add a new name for a scanner
- GET request to `\api\room\<name>`, to get the list of scanner's mac addresses that uses this name
- GET request to `\api\room`, to get the list of all scanners' names
- GET request to `\api\peopleCounting\<name>` with `{"start":startTimestamp,"end":endTimestamp}` as an attachment, to get people counting esitimates
- GET request to `\api\MovementGraph` with `{"start":startTimestamp,"end":endTimestamp,"rooms":["room1","room2"..]}` as an attachment, to get the graph of users' movements in the rooms listed

- GET request to `\api\relationshipGraph` with `{"start":startTimestamp,"end":endTimestamp,"rooms":["room1","room2"..]}` as an attachment, to get the graph of users' interactions in the groups listed

### Optional parameters
- `at,wt,dt` are optional parameters for people counting requests
- `Tmin,Tmax` are optional parameters for graph requests 