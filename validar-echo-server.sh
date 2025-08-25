#!/bin/bash

HOST="server"
PORT="12345"
MSG="HolaEchoServer"


output=$(docker run --rm --network tp0_testing_net busybox sh -c "echo '$MSG' | nc $HOST $PORT")

if [ "$output" = "$MSG" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
