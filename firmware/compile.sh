
ZTC=~/.zerynth2/dist/r2.4.3/ztc/ztc

for i in "$@"
do
case $i in
    --device_id=*|-d=*)
    DEVICEID="${i#*=}"
    shift # past argument=value
    ;;
    --jwt=*|-j=*)
    JWT="${i#*=}"
    shift # past argument=value
    ;;
    --ssid=*|-s=*)
    SSID="${i#*=}"
    shift # past argument=value
    ;;
    --password=*|-p=*)
    PASSWORD="${i#*=}"
    shift # past argument=value
    ;;
    --default)
    DEFAULT=YES
    shift # past argument with no value
    ;;
    *)
          # unknown option
    ;;
esac
done

cp -rf template.py main.py

sed -i "s/SSID = ' '/SSID = '$SSID'/" main.py
sed -i "s/PASSWORD = ' '/PASSWORD = '$PASSWORD'/" main.py
sed -i "s/DEVICEID = ' '/DEVICEID = '$DEVICEID'/" main.py
sed -i "s/JWT = ' '/JWT = '$JWT'/" main.py

$ZTC compile ./ esp32_devkitc

