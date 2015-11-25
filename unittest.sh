#!/bin/sh

cd new_domain/
$(pwd)/redis_agent/test/unittest.sh $(pwd)/redis_agent
