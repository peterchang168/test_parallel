#!/bin/sh

if [ "$#" -lt "1" ]; then
	echo "error: not enough parameters."
	echo "usage: $0 [workspace_dir]"
	exit -1
fi

CWD="$1"

TEST_SRC_DIR="${CWD}/"

TEST_DIR="${CWD}/test/functest"
TEST_TMP_DIR="/tmp/redis_agent_functest"
TEST_REPORT_DIR="${TEST_TMP_DIR}/report"
TEST_REPORT_FILE_PATH="${TEST_REPORT_DIR}/func_result.xml"
SHELL_SCRIPTS="gmetric rsync"
TEST_SCRIPTS="redis_agent_func_test.py"

#===============================================================================
# run functest
#===============================================================================

echo "begin functional test..."

# re-create test tmp folder
rm -rf ${TEST_TMP_DIR}
mkdir -p ${TEST_TMP_DIR}

# copy source to test tmp dir
# cd ${TEST_SRC_DIR}
# cp ${TEST_FILES} ${TEST_TMP_DIR}

# copy test data to test tmp dir
cd ${TEST_DIR}
cp -rf * ${TEST_TMP_DIR}
chown -R alps:alps ${TEST_TMP_DIR}

# create test report dir
mkdir -p ${TEST_REPORT_DIR}

# change permission
#chown -R tester:tester ${TEST_TMP_DIR}
#chmod -R u+r,u+w ${TEST_TMP_DIR}

# run test with normal user
cd ${TEST_TMP_DIR}

# change shell script with execution mode
chmod 755 ${SHELL_SCRIPTS}

# composite options
OPTIONS="-v -s -x"
#OPTIONS="${OPTIONS} --with-xunit --xunit-file=${TEST_REPORT_FILE_PATH}"
#OPTIONS="${OPTIONS} -w ${TEST_TMP_DIR} ${TEST_SCRIPTS}"
# call nosetests
nosetests ${OPTIONS}
test_result=$?
# convert xml report
#coverage xml -o ${TEST_REPORT_DIR}/coverage.xml ${TEST_TMP_DIR}/LELGenerator.py

if [ "${test_result}" -ne "0" ]; then
	echo "error: func test failed!"
	exit -1
else
	echo "func test passed"
fi

exit 0


