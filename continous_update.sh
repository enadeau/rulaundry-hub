#!/bin/bash
# Script to update status of the machine on the server periodically

while true
do
        echo Updating...
	python3 reading_multiplexer.py
        echo Updated.
        sleep 1
done
