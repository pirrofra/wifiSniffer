ZDM=~/.zerynth2/dist/r2.4.3/ztc/zdm


for i in "$@"
do
case $i in
    --fleet_id=*|-f=*)
    FLEETID="${i#*=}"
    shift # past argument=value
    ;;
    --name=*|-n=*)
    NAME="${i#*=}"
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


$ZDM device create $NAME $FLEETID

