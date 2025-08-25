#!/bin/bash

HOST="server"
PORT="12345"
MSG="HolaEchoServer"


output=$(docker run --rm --network testing_net busybox sh -c "echo '$MSG' | nc $HOST $PORT")

if [ "$output" = "$MSG" ]; then
    echo "action: test_echo_server | result: success"
    exit 0
else
    echo "action: test_echo_server | result: fail"
    exit 1
fi
