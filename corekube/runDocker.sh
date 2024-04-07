sudo docker run --rm -d --network host -v $(pwd):/mount  --name gnbsim0 mbilals/5gc-gnbsim:1milisecdelaySctpNoDelay-v21 sleep 1d
sudo docker run --rm -d --network host -v $(pwd):/mount  --name gnbsim1 mbilals/5gc-gnbsim:1milisecdelaySctpNoDelay-v21 sleep 1d
sudo docker run --rm -d --network host -v $(pwd):/mount  --name gnbsim2 mbilals/5gc-gnbsim:1milisecdelaySctpNoDelay-v21 sleep 1d
sudo docker run --rm -d --network host -v $(pwd):/mount  --name gnbsim3 mbilals/5gc-gnbsim:1milisecdelaySctpNoDelay-v21 sleep 1d
sudo docker run --rm -d --network host -v $(pwd):/mount  --name gnbsim4 mbilals/5gc-gnbsim:1milisecdelaySctpNoDelay-v21 sleep 1d
sudo docker run --rm -d --network host -v $(pwd):/mount  --name gnbsim5 mbilals/5gc-gnbsim:1milisecdelaySctpNoDelay-v21 sleep 1d
sudo docker run --rm -d --network host -v $(pwd):/mount  --name gnbsim6 mbilals/5gc-gnbsim:1milisecdelaySctpNoDelay-v21 sleep 1d
sudo docker run --rm -d --network host -v $(pwd):/mount  --name gnbsim7 mbilals/5gc-gnbsim:1milisecdelaySctpNoDelay-v21 sleep 1d
