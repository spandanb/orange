#!/bin/bash

#this is the client machine, i.e. does the user have sudo access?
CLIENTMACH=true

git submodule init
git submodule update

if [ "$CLIENTMACH" = true ]; then
    #create a virtual env
    ENVNAME=orangenv
    virtualenv --system-site-packages $ENVNAME
    source $ENVNAME/bin/activate
    python setup.py develop
else
    sudo apt-get update
    sudo apt-get install python-pip python-dev build-essential git -y
    sudo pip install setuptools
    sudo apt-get install libffi-dev libssl-dev -y
    sudo python setup.py develop
fi

