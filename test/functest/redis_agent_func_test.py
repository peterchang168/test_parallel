#!/bin/env nosetests

import os
import sys
import re
import copy
import StringIO
import subprocess
import signal
import calendar
import time
import shutil
import traceback
import threading
import unittest
import socket
import fake_redis
import calendar
try:
	import json
except:
	import simplejson as json

def check_true(value1, name =  ""):
	if value1 != True:
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s is not True" % (prefix, repr(value1))
	return True if value1 == True else False

def check_false(value1, name =  ""):
	if value1 != False:
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s is not False" % (prefix, repr(value1))
	return True if value1 == False else False

def check_eq(value1, value2, name =  ""):
	if value1 != value2:
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s == %s is not True" % (prefix, repr(value1), repr(value2))
	return True if value1 == value2 else False

def check_ne(value1, value2, name =  ""):
	if value1 == value2:
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s != %s is not True" % (prefix, repr(value1), repr(value2))
	return True if value1 != value2 else False

def check_ge(value1, value2, name =  ""):
	if (value1 >= value2) != True:
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s >= %s is not True" % (prefix, repr(value1), repr(value2))
	return True if value1 >= value2 else False

def check_gt(value1, value2, name =  ""):
	if (value1 > value2) != True:
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s > %s is not True" % (prefix, repr(value1), repr(value2))
	return True if value1 > value2 else False

def check_lt(value1, value2, name =  ""):
	if (value1 < value2) != True:
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
			print "%s%s < %s is not True" % (prefix, repr(value1), repr(value2))
	return True if value1 < value2 else False

def is_proc_alive(key):
	try:
		pps = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
		pgrep1  = subprocess.Popen(["grep", key], stdin=pps.stdout, stdout=subprocess.PIPE)
		pgrep2  = subprocess.Popen(["grep", "-v", "grep"], stdin=pgrep1.stdout, stdout=subprocess.PIPE)
		output = pgrep2.communicate()[0]
		lines = output.split('\n')
		total = 0
		for line in lines:
			if line.strip():
				total +=1	
		print lines
		if total>0:
			return True
		else:
			return False
	except Exception, e:
		print 'Fail to check process alive : %s' % e
		return True
	return False


def check_str_contain(value1, value2, name = ""):
	if not (value1.find(value2) >= 0):
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s doesn't contain %s" % (prefix, repr(value1), repr(value2))
	return True if value1.find(value2) >= 0 else False

def check_str_startswith(value1, value2, name = ""):
	if not (value1.startswith(value2) == True):
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s doesn't start with %s" % (prefix, repr(value1), repr(value2))
	return value1.startswith(value2)

def check_str_endswith(value1, value2, name = ""):
	if not (value1.endswith(value2) == True):
		prefix = ""
		if name != "":
			prefix = "%s: " % (name)
		print "%s%s doesn't end with %s" % (prefix, repr(value1), repr(value2))
	return value1.endswith(value2)

def get_format_time(org_time, org_fmt, new_fmt):
    return time.strftime(new_fmt, time.strptime(org_time, org_fmt))

#===============================================================================
# globals
#===============================================================================

# package dir
package_dir = "/trend/new_domain"
ra_exe_name = "new_domain_redis_agent.py"
ra_exe_path = os.path.join(package_dir, "bin", ra_exe_name)
ra_start_script = os.path.join(package_dir, "redis_start.sh")
ra_stop_script = os.path.join(package_dir, "redis_stop.sh")
#pp_exe_name = "new_domain_pattern_process.py"
#pp_exe_path = os.path.join(package_dir, "bin", pp_exe_name)
#last_success_path = os.path.join(package_dir, "latest_success.txt")
lock_path = os.path.join(package_dir, "agent.lck")
mail_dir = os.path.join(package_dir, "mail")
log_dir = os.path.join(package_dir, "log")
#src_dir = os.path.join(package_dir, "src")
raptn_dir = os.path.join(package_dir, "raptn")
filelist_path = os.path.join(raptn_dir, "filelist.txt")

# test run dir
cur_dir = os.path.abspath(os.path.curdir)
gmetric_path = os.path.join(cur_dir, "gmetric")
gmetric_out_path = os.path.join(cur_dir, "gmetric_out")
#hadoop_ls_log_path = os.path.join(cur_dir, "hadoop_cmd_ls_log")
#hadoop_get_log_path = os.path.join(cur_dir, "hadoop_cmd_get_log")
#pp_cmd_log_path = os.path.join(cur_dir, "pp_cmd_log")

# other data
#hadoop_dir = "/user/alps/new_domain_mr_job/"
REDIS = None
HOST = '127.0.0.1'
PORT = 6379
#===============================================================================
# tools
#===============================================================================

# reset last success file
def reset_filelist_file():
	subprocess.Popen("chmod +w %s" % (filelist_path) , shell = True).wait()
	subprocess.Popen("truncate -s 0 %s" % (filelist_path) , shell = True).wait()

# reset mail dir
def reset_mail_dir():
	subprocess.Popen("rm -rf %s" % (os.path.join(mail_dir, "*")) , shell = True).wait()

# reset log dir
def reset_log_dir():
	subprocess.Popen("rm -rf %s" % (os.path.join(log_dir, "*")) , shell = True).wait()

# reset redis agent pattern directory
def reset_raptn_dir():
	subprocess.Popen("rm -rf %s" % (os.path.join(raptn_dir, "*")) , shell = True).wait()

# reset pattern directory
def reset_ptn(ptn_dir):
	subprocess.Popen("rm -rf %s" % (os.path.join(ptn_dir, "*")) , shell = True).wait()

# reset lck file
def reset_lck():
	subprocess.Popen("rm -f %s" % (lock_path) , shell = True).wait()

# reset gmetric output
def reset_gmetric_output():
	subprocess.Popen("rm -f %s" % (gmetric_out_path) , shell = True).wait()

# replace rsync executable
def replace_rsync(test_dir):
	fake_rsync_path = os.path.join(test_dir, 'rsync')
	rsync_exe_path = os.path.join(cur_dir, 'rsync')
	subprocess.Popen("cp -f %s %s" % (fake_rsync_path, rsync_exe_path) , shell = True).wait()
	subprocess.Popen("chmod +x %s" % (rsync_exe_path) , shell = True).wait()

# replace s3 python library
def replace_aws_s3_python_library(test_dir):
	dst_path = '/trend/new_domain/bin/'
	fake_aws_s3_path = os.path.join(test_dir, 'aws_s3_util.py')
	dst_aws_s3_path = os.path.join(dst_path, 'aws_s3_util.py')
	subprocess.Popen("cp -f %s %s" % (fake_aws_s3_path, dst_aws_s3_path) , shell = True).wait()

# touch a fake redis dump
def touch_redis_dump():
	if not os.path.exists('/var/lib/redis'):
		subprocess.Popen("/bin/mkdir /var/lib/redis" , shell = True).wait()
	if not os.path.exists('/var/lib/redis/dump.rdb'):	
		subprocess.Popen("/bin/echo 'redis dump' > /var/lib/redis/dump.rdb" , shell = True).wait()
	else:
		return False
	return True

def remove_redis_dump():
	if os.path.exists('/var/lib/redis/dump.rdb'):	
		subprocess.Popen("/bin/rm -f /var/lib/redis/dump.rdb" , shell = True).wait()

# replace pattern process executable
#def replace_pattern_process(test_dir):
#	fake_pp_path = os.path.join(test_dir, "fake_new_domain_pp.py")
#	bk_pp_path = os.path.join(package_dir, "bin", pp_exe_name + ".bak")
#	# backup pattern process file if not exist
#	if os.path.exists(bk_pp_path) != True:
#		os.rename(pp_exe_path, bk_pp_path)
#	# else just remove pattern process file
#	else:
#		if os.path.exists(pp_exe_path) == True:
#			os.unlink(pp_exe_path)
#	# copy the fake pattern process file
#	subprocess.Popen("cp -f %s %s" % (fake_pp_path, pp_exe_path) , shell = True).wait()
#	subprocess.Popen("chmod +x %s" % (pp_exe_path) , shell = True).wait()

# reset pattern process file
#def reset_pattern_process():
#	bk_pp_path = os.path.join(package_dir, "bin", pp_exe_name + ".bak")
#	# restore pattern process file if backup file exists
#	if os.path.exists(bk_pp_path) == True:
#		if os.path.exists(pp_exe_path) == True:
#			os.unlink(pp_exe_path)
#		os.rename(bk_pp_path, pp_exe_path)
#	subprocess.Popen("rm -f %s" % (pp_cmd_log_path) , shell = True).wait()

# wait until previouse process end
def wait_prev_proc_end():
	while True:
		p = subprocess.Popen("ps -u alps -o pid -C python2.6 --no-headers -o cmd", shell = True, stdout = subprocess.PIPE)
		p.wait()
		procs = p.stdout.read().strip()
		p.stdout.close()
		if len(procs) == 0:
			return
		print "waiting for procs...\n%s" % (procs)
		time.sleep(1.0)

# global test timestamp
test_timestamp = 0

# set test timestamp
def set_timestamp():
	global test_timestamp
	test_timestamp = time.time()

# reset test environment
def reset_env():
	# subprocess.Popen("killall python2.6", shell = True).wait()
	reset_filelist_file()
	reset_mail_dir()
	reset_log_dir()
	reset_raptn_dir()
	reset_lck()
	reset_gmetric_output()
	# reset_pattern_process()
	set_timestamp()
		# reset redis
	reset_redis()
	# check if new_domain_redis_agent.py still running in 10 seconds
	t = 0
	while t < 15 and is_proc_alive('new_domain_redis_agent.py'):
		t +=1
		time.sleep(1)

# start redis
def start_redis():
	redis = fake_redis.RedisServer(6379)
	redis.start()
	return redis
#	p = subprocess.Popen("python %s" %redis_exe_path, shell = True)
#	while p.poll() is not None:
#		time.sleep(3)
#		p = subprocess.Popen("python %s" %redis_exe_path, shell = True)
#	print 'start redis result'
#	print p.pid
#	return p.pid

def stop_redis(redis):
	redis.stop()
#	os.kill(pid, signal.SIGTERM)

def get_exc_str(exc_info):
	io = StringIO.StringIO()
	io.write(str(exc_info[0]))
	io.write("\n")
	io.write(str(exc_info[1]))
	io.write("\n")
	io.write(traceback.format_exc())
	io.seek(0)
	return io.read()

type_testing_pattern = re.compile(".*")

# find files which match the specified pattern in a directory, it won't do recursive search
# parameters:
#	search_dir: the directory to be searched
#	file_name_pattern: 1. the compiled regular expression to match the file name
#					   2. a regular expression string
# return value:
#	a file name list that contains all file name match the pattern
#	if no file matched, return value is a empty list
#	if error occured, the value is None
def find_file_in_dir(search_dir, file_name_pattern):
	if search_dir is None:
		return None
	if file_name_pattern is None:
		return None
	if type(file_name_pattern) != type(type_testing_pattern):
		try:
			ptn = re.compile(file_name_pattern)
		except:
			return None
	else:
		ptn = file_name_pattern
	# get all files in the directory
	files = []
	for (r, d, f) in os.walk(search_dir):
		if os.path.samefile(r, search_dir) == True:
			files = f
			break
	matched_files = []
	# collect matched files
	for f in files:
		m = ptn.search(f)
		if m is not None:
			matched_files.append(f)
	return matched_files

# find directories which match the specified pattern in a directory, it won't do recursive search
# parameters:
#	search_dir: the directory to be searched
#	dir_name_pattern: 1. the compiled regular expression to match the file name
#					  2. a regular expression string
# return value:
#	a directory name list that contains all directory name match the pattern
#	if no file matched, return value is a empty list
#	if error occured, the value is None
def find_dir_in_dir(search_dir, dir_name_pattern):
	if search_dir is None:
		return None
	if dir_name_pattern is None:
		return None
	if type(dir_name_pattern) != type(type_testing_pattern):
		try:
			ptn = re.compile(dir_name_pattern)
		except:
			return None
	else:
		ptn = dir_name_pattern
	# get all directories in the directory
	dirs = []
	for (r, d, f) in os.walk(search_dir):
		if os.path.samefile(r, search_dir) == True:
			dirs = d
			break
	matched_dirs = []
	# collect matched files
	for d in dirs:
		m = ptn.search(d)
		if m is not None:
			matched_dirs.append(d)
	return matched_dirs

# read config file to a dictionaly from specified path
def load_config_file(path):
	f = open(path, "r")
	config_data = f.read()
	f.close()
	config_name = os.path.basename(path)
	config = {}
	exec(compile(config_data, config_name, "exec"))
	return config

# write a dictionaly to a file on specified path
def write_config_file(path, config):
	f = open(path, "w")
	for key in config:
		f.write("config['%s'] = %s\n" % (key, repr(config[key])))
	f.close()

# get mails, read all mail to a dictionaly list
def get_mails():
	mails = []
	dirs = find_dir_in_dir(mail_dir, "^mail_[0-9]{8}_[0-9]{6}_[0-9]{10}_[0-9]{3}$")
	dirs.sort()
	for d in dirs:
		json_path = os.path.join(mail_dir, d, "mail.json")
		f = open(json_path, "r")
		mail_dict = json.loads(f.read())
		f.close()
		mails.append(mail_dict)
	return mails

# get gmond status
def get_gmetric_stats():
	stats_dict = {}
	try:
		f = open(gmetric_out_path, "r")
		for line in f:
			line = line.rstrip()
			param_list = eval(line)
			if param_list[0] != "-n":
				raise Exception("1st param should be \"-n\"")
			name = param_list[1]
			d = {}
			i = 2
			while i < len(param_list):
				key = param_list[i]
				value = param_list[i + 1]
				d[key] = value
				i += 2
			if name not in stats_dict:
				stats_dict[name] = []
			stats_dict[name].append(d)
		f.close()
	except:
		pass
	return stats_dict

# read filelist.txt
def read_filelist_file():
	f = open(filelist_path, "r")
	s = f.read().strip()
	f.close()
	return s

# preare pattern based on current time
def prepare_rsync_ptn(ptn_dir, timelist):
	cur_tstamp = int(time.time())
	flist = []
	ret = []
	for token in timelist:
		idx = token[0]
		t = token[1]
		t = cur_tstamp+t
		t_struct = time.gmtime(t)
		date_dir = time.strftime('%Y%m%d', t_struct)
		date_dir = os.path.join(ptn_dir, date_dir)
		ptn = time.strftime('%Y%m%d%H%M', t_struct)
		ret.append(ptn)
		flist.append(('%s.ptn' %ptn, t))
		ptn_path = os.path.join(date_dir, '%s.ptn' %ptn)
		if not os.path.isdir(date_dir):
			os.mkdir(date_dir)
		f = open(ptn_path, 'w')
		for i in range(3):
			f.write('%s_%d.com\n' %(idx, i))
		f.close()
	for item in flist:
		f = open('%s/filelist.txt' %ptn_dir, 'a')
		f.write('%s\t%s\n' %(item[0], item[1]))
		f.close()
	return ret
   
# preare pattern based on current time
def prepare_two_rsync_ptn(ptn_dir, timelist):
	cur_tstamp = int(time.time())
	flist = []
	ret = []
	for token in timelist:
		idx = token[0]
		t = token[1]
		t = cur_tstamp+t
		t_struct = time.gmtime(t)
		date_dir = time.strftime('%Y%m%d', t_struct)
		date_dir = os.path.join(ptn_dir, date_dir)
		ptn = time.strftime('%Y%m%d%H%M', t_struct)
		ret.append(ptn)
		flist.append(('%s.ptn' %ptn, t))
		ptn_path = os.path.join(date_dir, '%s.ptn' %ptn)
		if not os.path.isdir(date_dir):
			os.mkdir(date_dir)
		f = open(ptn_path, 'w')
		for i in range(3):
			f.write('%s_%d.com\n' %(idx, i))
		f.close()
	for item in flist:
		f = open('%s/filelist.txt' %ptn_dir, 'a')
		f.write('%s\t%s\n' %(item[0], item[1]))
		f.close()
	for item in flist[1:]:
		f = open('%s/filelist.txt.11' %ptn_dir, 'a')
		f.write('%s\t%s\n' %(item[0], item[1]))
		f.close()
	return ret
				
def set_redis(key, value):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(1)

	try:
		sock.connect((HOST, PORT))
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(2)

	sock.send("*3\r\n$%d\r\n%s\r\n$%d\r\n%s\r\n$%d\r\n%s\r\n" % (len('SET'), 'SET',len(key), key, len(value), value))

	data = sock.recv(1024)
	resp = ""
	while len(data):
		resp = resp + data
		data = sock.recv(1024)
	sock.close()
	#print resp
	ret = resp.split('\r\n')
	#print ret
	if ret >2:
		return ret[1]
	else :
		return None


def get_redis(key):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(1)

	try:
		sock.connect((HOST, PORT))
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(2)

	sock.send("*2\r\n$%d\r\n%s\r\n$%d\r\n%s\r\n" % (len('GET'), 'GET',len(key), key))

	data = sock.recv(1024)
	resp = ""
	while len(data):
		resp = resp + data
		data = sock.recv(1024)
	sock.close()
	ret = resp.split('\r\n')
	#print ret
	if ret >2:
		return ret[1]
	else :
		return None


def reset_redis():
	flushdb_redis()
	set_redis_corruption("0")
	set_redis_SleepTime(0)

def set_redis_corruption(flag):
	REDIS.setCorruption(flag)

def set_redis_SleepTime(sleeptime):
	REDIS.setSleepTime(sleeptime)

def flushdb_redis():
	print 'flushdb_redis'
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(1)

	try:
		sock.connect((HOST, PORT))
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(2)

	sock.send("*1\r\n$%d\r\n%s\r\nQUIT\r\n" % (len('FLUSHDB'), 'FLUSHDB'))

	data = sock.recv(1024)
	resp = ""
	while len(data):
		resp = resp + data
		data = sock.recv(1024)
	sock.close()
	#print resp
	return resp

def set_bgexceptioncount(exception_count):
	exception_count = str(exception_count)
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(1)

	try:
		sock.connect((HOST, PORT))
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(2)
	sock.send("*2\r\n$%d\r\n%s\r\n$%d\r\n%s\r\n" % (len('BGEXCEPTIONCOUNT'), 'BGEXCEPTIONCOUNT',len(exception_count), exception_count))

	data = sock.recv(1024)
	resp = ""
	while len(data):
		resp = resp + data
		data = sock.recv(1024)
	sock.close()
	#print resp
	return resp


def get_ttl_redis(key):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(1)

	try:
		sock.connect((HOST, PORT))
	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(2)

	sock.send("*2\r\n$%d\r\n%s\r\n$%d\r\n%s\r\n" % (len('TTL'), 'TTL',len(key), key))

	data = sock.recv(1024)
	resp = ""
	while len(data):
		resp = resp + data
		data = sock.recv(1024)
	sock.close()
	ret = resp.split('\r\n')
		#print ret
	if ret >2:
		return ret[1]
	else :
		return None


class TestRedisAgent(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		global REDIS
		cls.redis = start_redis()
		REDIS = cls.redis
		time.sleep(1)

	def setUp(self):
		pass

	def tearDown(self):
		pass

	@classmethod
	def tearDownClass(cls):
		# stop redis
		stop_redis(cls.redis)


#===============================================================================
# test rsync the newer server
#===============================================================================


	def test_rsync_the_newer_server(self):
		print 'test_rsync_the_newer_server'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_rsync_the_newer_server")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_two_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		# check redis (check domain ttl in hour)
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17940), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)


#===============================================================================
# test basic normal
#===============================================================================

	
	def test_basic_normal(self):
		print 'test_basic_normal'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_basic_normal")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		# check redis (check domain ttl in hour)
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17940), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)


#===============================================================================
# test singleton
#===============================================================================


	def test_singleton(self):
		print 'test_singleton'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_singleton")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		time.sleep(0.5)
		# run one more process, should end immediately
		p2 = subprocess.Popen(cmd, shell = True)
		ret_p2 = p2.wait()
		# should return 255
		self.assertEqual(check_eq(ret_p2,255), True)
		# p1 should not end now
		self.assertEqual(check_eq(None,p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 1 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "Fail to get file lock [/trend/new_domain/agent.lck]"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		# check ttl in hour
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17940), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)



#===============================================================================
# test active rsync timeout
#===============================================================================

	
	def test_active_rsync_timeout(self):
		print 'test_active_rsync_timeout'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_active_rsync_timeout")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None,p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 1 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "process was executed overtime"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
                        t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
                        t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		# check ttl in hour
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17935), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)



#===============================================================================
# test all rsync timeout one server
#===============================================================================

	
	def test_all_rsync_timeout_one_server(self):
		print 'test_all_rsync_timeout_one_server'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_all_rsync_timeout_one_server")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		ret_p1 = p1.poll()
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 1 mail
		self.assertEqual(check_eq(len(mails),2), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "process was executed overtime"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[1]["body"], "Fail to rsync filelist.txt from all pattern process server"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual(stats_dict, {})



#===============================================================================
# test all rsync timeout two server
#===============================================================================

	
	def test_all_rsync_timeout_two_server(self):
		print 'test_all_rsync_timeout_two_server'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_all_rsync_timeout_two_server")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		ret_p1 = p1.poll()
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 3 mail
		self.assertEqual(check_eq(len(mails),3), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "process was executed overtime"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[1]["body"], "process was executed overtime"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[2]["body"], "Fail to rsync filelist.txt from all pattern process server"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual(stats_dict, {})



#===============================================================================
# test all rsync timeout three server
#===============================================================================

	
	def test_all_rsync_timeout_three_server(self):
		print 'test_all_rsync_timeout_three_server'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_all_rsync_timeout_three_server")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		ret_p1 = p1.poll()
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 4 mail
		self.assertEqual(check_eq(len(mails),4), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "process was executed overtime"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[1]["body"], "process was executed overtime"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[2]["body"], "process was executed overtime"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[3]["body"], "Fail to rsync filelist.txt from all pattern process server"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual(stats_dict, {})



#===============================================================================
# test active rsync fail
#===============================================================================

	
	def test_active_rsync_fail(self):
		print 'test_active_rsync_fail'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_active_rsync_fail")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None,p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 1 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "the failed request"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
                        t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
                        t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		# check ttl in hour
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17940), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)


#===============================================================================
# test config fail empty rsync server
#===============================================================================

	
	def test_config_fail_empty_rsync_server(self):
		print 'test_config_fail_empty_rsync_server'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_config_fail_empty_rsync_server")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)



#===============================================================================
# test all rsync fail two server
#===============================================================================

	
	def test_all_rsync_fail_two_server(self):
		print 'test_all_rsync_fail_two_server'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_all_rsync_fail_two_server")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 3 mail
		self.assertEqual(check_eq(len(mails), 3), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "the failed request"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[1]["body"], "the failed request"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[2]["body"], "Fail to rsync filelist.txt from all pattern process server"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual(stats_dict, {})



#===============================================================================
# test all rsync fail three server
#===============================================================================

	
	def test_all_rsync_fail_three_server(self):
		print 'test_all_rsync_fail_three_server'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_all_rsync_fail_three_server")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		#time.sleep(2)
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 4 mail
		self.assertEqual(check_eq(len(mails), 4), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "the failed request"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[1]["body"], "the failed request"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[2]["body"], "the failed request"), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[3]["body"], "Fail to rsync filelist.txt from all pattern process server"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual(stats_dict, {})



#===============================================================================
# test query redis timestamp connection fail 
#===============================================================================


	def test_query_redis_timestamp_conn_fail(self):
		print 'test_query_redis_timestamp_conn_fail'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_query_redis_timestamp_conn_fail")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		set_redis_corruption("1")
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "Socket closed on remote end"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual(stats_dict, {})



#===============================================================================
# test query redis timestamp connection timeout
#===============================================================================


	def test_query_redis_timestamp_conn_timeout(self):
		print 'test_query_redis_timestamp_conn_timeout'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_query_redis_timestamp_conn_timeout")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		set_redis_SleepTime(4)
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "timed out"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual(stats_dict, {})



#===============================================================================
# test redis timestamp larger than rsync
#===============================================================================


	def test_redis_timestamp_larger_than_rsync(self):
		print 'test_redis_timestamp_larger_than_rsync'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_redis_timestamp_larger_than_rsync")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		cur_time = int(time.time())
		t_struct = time.gmtime(cur_time)
		cur_timestamp = time.strftime('%Y%m%d%H%M', t_struct)
		set_redis('[NDS_timeversion]','%d' % cur_time)
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		idx = 0
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 1
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(cur_timestamp, '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 1
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['0']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)


#===============================================================================
# test lost not expired pattern file
#===============================================================================


	def test_lost_not_expired_pattern_file(self):
		print 'test_lost_not_expired_pattern_file'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_lost_not_expired_pattern_file")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist0 = prepare_rsync_ptn(ptn_dir, [('test1',-50)])
		f = open('%s/filelist.txt' %ptn_dir, 'a')
		t = int(time.time()) - 3600 - 50
		t_struct = time.gmtime(t)
		ptn = time.strftime('%Y%m%d%H%M', t_struct)
		f.write('%s.ptn\t%s\n' %(ptn, t))
		f.close()
		tlist = prepare_rsync_ptn(ptn_dir, [('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "No such file or directory"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 5
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 5
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist0[0], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		# check ttl in hour
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 117), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 117), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 117), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)



#===============================================================================
# test lost expired pattern file
#===============================================================================


	def test_lost_expired_pattern_file(self):
		print 'test_lost_expired_pattern_file'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_lost_expired_pattern_file")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50)])
		f = open('%s/filelist.txt' %ptn_dir, 'a')
		t = int(time.time()) - 86400*6 -5
		t_struct = time.gmtime(t)
		ptn = time.strftime('%Y%m%d%H%M', t_struct)
		f.write('%s.ptn\t%s\n' %(ptn, t))
		f.close()
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		# check redis (check domain ttl in hour)
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17940), True)
		self.assertEqual(check_eq(int(get_redis('[NDS_timeversion]')), int(get_redis('test1_0.com'))), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)





#===============================================================================
# test update redis fail
#===============================================================================


	def test_update_redis_fail(self):
		print 'test_update_redis_fail'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_update_redis_fail")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('fail3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 1 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "Socket closed on remote end"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 3
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 3
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		# check redis (check domain ttl in hour)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)



#===============================================================================
# test update redis timeout
#===============================================================================


	def test_update_redis_timeout(self):
		print 'test_update_redis_timeout'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_update_redis_timeout")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('timeout3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 1 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "timed out"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 3
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 3
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			idx += 1
		# check redis (check domain ttl in hour)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)



#===============================================================================
# test parameter error
#===============================================================================


	def test_parameter_error(self):
		print 'test_parameter_error'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_basic_normal")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)


#===============================================================================
# test rsync folder is empty
#===============================================================================


	def test_rsync_folder_empty(self):
		print 'test_rsync_folder_empty'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_rsync_folder_empty")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#replace aws_s3_util.py
		replace_aws_s3_python_library(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# empty filelist.txt
		open('%s/filelist.txt' %ptn_dir, 'w').close()
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual(check_eq(len(stats_dict),0), True)
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)




#===============================================================================
# test no newer pattern operation_time_and_s3_pattern_time_less_than_an_hour
#===============================================================================


	def test_no_newer_pattern_operation_time_and_s3_pattern_time_less_than_an_hour(self):
		print 'test_no_newer_pattern_operation_time_and_s3_pattern_time_less_than_an_hour'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_no_newer_pattern_operation_time_and_s3_pattern_time_less_than_an_hour")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#replace aws_s3_util.py
		replace_aws_s3_python_library(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		f = open('%s/filelist.txt' %ptn_dir, 'r')
		content = f.read()
		lines = content.split('\n')
		timestamp = (lines[0].split('\t'))[1]
		set_redis('[NDS_timeversion]','%s' %timestamp)
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual('NewDomainRedisAgent_S3UpdateTime' in stats_dict, False)
		self.assertEqual(len(stats_dict), 0)
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)



#===============================================================================
# test no newer pattern and s3 bucket is empty
#===============================================================================


	def test_no_newer_pattern_and_s3_bucket_is_empty(self):
		print 'test_no_newer_pattern_operation_time_and_s3_bucket_is_empty'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_no_newer_pattern_and_s3_bucket_is_empty")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#replace aws_s3_util.py
		replace_aws_s3_python_library(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		f = open('%s/filelist.txt' %ptn_dir, 'r')
		content = f.read()
		lines = content.split('\n')
		timestamp = (lines[0].split('\t'))[1]
		set_redis('[NDS_timeversion]','%s' %timestamp)
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual('NewDomainRedisAgent_S3UpdateTime' in stats_dict, False)
		self.assertEqual(len(stats_dict), 0)
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)



#===============================================================================
# test no newer pattern and turn on S3 backup
#===============================================================================


	def test_no_newer_pattern_and_s3_backup(self):
		print 'test_no_newer_pattern'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_no_newer_pattern_and_s3_backup")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#replace aws_s3_util.py
		replace_aws_s3_python_library(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		f = open('%s/filelist.txt' %ptn_dir, 'r')
		content = f.read()
		lines = content.split('\n')
		timestamp = (lines[0].split('\t'))[1]
		set_redis('[NDS_timeversion]','%s' %timestamp)
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		self.assertEqual('NewDomainRedisAgent_S3UpdateTime' in stats_dict, True)
		self.assertEqual(len(stats_dict), 1)
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)


	
#===============================================================================
# test no newer pattern
#===============================================================================


	def test_no_newer_pattern(self):
		print 'test_no_newer_pattern'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_no_newer_pattern")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#replace aws_s3_util.py
		replace_aws_s3_python_library(test_dir)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		f = open('%s/filelist.txt' %ptn_dir, 'r')
		content = f.read()
		lines = content.split('\n')
		timestamp = (lines[0].split('\t'))[1]
		set_redis('[NDS_timeversion]','%s' %timestamp)
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check redis (check L4 health key not exist)
		self.assertEqual(check_eq(get_ttl_redis('[NDS]'), '-1'), True)


	
#===============================================================================
# test basic normal_turn_on_s3_backup
#===============================================================================
	def test_basic_normal_turn_on_s3_backup(self):
		print 'test_basic_normal_turn_on_s3_backup'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_basic_normal_turn_on_s3_backup")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#replace aws_s3_util.py
		replace_aws_s3_python_library(test_dir)
		# touch redis dump file
		is_touch_redis_dump = touch_redis_dump()
		# set times redis bgsave return in progressing exception 
		set_bgexceptioncount(6)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# remove redis dump if created by functest
		if is_touch_redis_dump:
			remove_redis_dump()
		# get mails
		mails = get_mails()
		# should have 0 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric "NewDomainRedisAgent_S3UpdateTime"
		gmetric_dump_ver = stats_dict['NewDomainRedisAgent_S3UpdateTime']
		valid_length = 1
		self.assertEqual(check_eq(valid_length, len(gmetric_dump_ver)), True)
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		# check redis (check domain ttl in hour)
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17935), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)


#===============================================================================
# test redis bgsave already in progressing in 1st try
#===============================================================================
	def test_redis_bgsave_already_in_progressing_in_1st_try(self):
		print 'test_redis_bgsave_already_in_progressing_in_1st_try'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_redis_bgsave_already_in_progressing_in_1st_try")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#replace aws_s3_util.py
		replace_aws_s3_python_library(test_dir)
		# touch redis dump file
		is_touch_redis_dump = touch_redis_dump()
		# set times redis bgsave return in progressing exception 
		set_bgexceptioncount(7)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,0), True)
		# remove redis dump if created by functest
		if is_touch_redis_dump:
			remove_redis_dump()
		# get mails
		mails = get_mails()
		# should have 1 mail
		self.assertEqual(check_eq(len(mails),0), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		#check gmetric "NewDomainRedisAgent_S3UpdateTime"
		gmetric_dump_ver = stats_dict['NewDomainRedisAgent_S3UpdateTime']
		valid_length = 1
		self.assertEqual(check_eq(valid_length, len(gmetric_dump_ver)), True)
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		# check redis (check domain ttl in hour)
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17935), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)


#===============================================================================
# test copy s3 fail
#===============================================================================
	def test_copy_s3_fail(self):
		print 'test_copy_s3_fail'
		wait_prev_proc_end()
		reset_env()
		self.assertEqual(is_proc_alive('new_domain_redis_agent.py'), False)
		test_dir = os.path.join(cur_dir, "test_copy_s3_fail")
		if not os.path.isdir(test_dir):
			os.mkdir(test_dir)
		#replace rysnc in cur_dir
		replace_rsync(test_dir)
		#replace aws_s3_util.py
		replace_aws_s3_python_library(test_dir)
		# touch redis dump file
		is_touch_redis_dump = touch_redis_dump()
		# set times redis bgsave return in progressing exception 
		set_bgexceptioncount(6)
		#prepare pattern process pattern path
		ptn_dir = os.path.join(test_dir, "ptn")
		reset_ptn(ptn_dir)
		if not os.path.isdir(ptn_dir):
			os.mkdir(ptn_dir)
		# prepare pattern process patterns
		tlist = prepare_rsync_ptn(ptn_dir, [('test1',-50), ('test2',-3600*1 -50), ('test2', -3600*2 -50), ('test3',-3600*3 -50), ('test4', -3600*4 -50), ('test5', -3600*5 -50), ('test6', -3600*6 -50), ('test7', -86400*6 -5)])
		# start redis
		redis_exe_path = os.path.join(test_dir, "fake_redis.py")
		set_redis('[NDS_timeversion]','1000000000')
		get_redis('[NDS_timeversion]')
		#
		# test success, 1st time
		#
		#param = ["sudo", "-u", "alps", "env", "PATH=%s" % (cur_dir), ra_exe_path, 
		param = ["env", "PATH=%s" % (cur_dir), ra_exe_path, 
			"-c", os.path.join(test_dir, "new_domain_redis_agent.conf")]
		cmd = str.join(" ", param)
		# run process
		p1 = subprocess.Popen(cmd, shell = True)
		# p1 should not end now
		self.assertEqual(check_eq(None, p1.poll()), True)
		# wait p1 end
		ret_p1 = p1.wait()
		# check expected result
		self.assertEqual(check_eq(ret_p1,255), True)
		# remove redis dump if created by functest
		if is_touch_redis_dump:
			remove_redis_dump()
		# get mails
		mails = get_mails()
		# should have 1 mail
		self.assertEqual(check_eq(len(mails),1), True)
		# check mail subject
		self.assertEqual(check_str_contain(mails[0]["subject"], "[New Domain][Redis Agent]"), True)
		self.assertEqual(check_str_contain(mails[0]["subject"], "Error Notification"), True)
		# check mail body
		self.assertEqual(check_str_contain(mails[0]["body"], "Fail in the stage to copy redis dump from local to S3"), True)
		# check gmetric output, latest one failed
		stats_dict = get_gmetric_stats()
		tlist = sorted(tlist)
		tlist = tlist[1:]
		"NewDomainRedisAgent_S3Version"
		#check gmetric 'NewDomainRedisAgent_RedisLatest'
		redis_latest = stats_dict['NewDomainRedisAgent_RedisLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(redis_latest)), True)
		for item in redis_latest:
			t = get_format_time(tlist[idx], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_RsyncLatest'
		rsync_latest = stats_dict['NewDomainRedisAgent_RsyncLatest']
		valid_length = 7
		idx = 0
		self.assertEqual(check_eq(valid_length, len(rsync_latest)), True)
		for item in rsync_latest:
			t = get_format_time(tlist[-1], '%Y%m%d%H%M', '%y%m%d%H%M')
			self.assertEqual(check_eq(item["-v"], t), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
		#check gmetric 'NewDomainRedisAgent_NewInsert'
		new_insert = stats_dict['NewDomainRedisAgent_NewInsert']
		valid_result = ['3', '3', '3', '3', '3', '0' , '3']
		idx = 0
		for item in new_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		#check gmetric 'NewDomainRedisAgent_ExistUpdate'
		exist_insert = stats_dict['NewDomainRedisAgent_ExistUpdate']
		valid_result = ['0','0','0','0','0','3','0']
		idx = 0
		for item in exist_insert:
			self.assertEqual(check_eq(item["-u"], "amount"), True)
			self.assertEqual(check_eq(item["-v"], valid_result[idx]), True)
			self.assertEqual(check_eq(item["-t"], "int32"), True)
			self.assertEqual(check_eq(item["-d"], "3600"), True)
			idx += 1
		self.assertEqual(check_ge((int(get_ttl_redis('[NDS]'))-int(time.time())), 17935), True)
		# check redis (check domain ttl in hour)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_0.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_1.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test1_2.com'))-int(time.time()))/3600, 119), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_0.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_1.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test2_2.com'))-int(time.time()))/3600, 118), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_0.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_1.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test3_2.com'))-int(time.time()))/3600, 116), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_0.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_1.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test4_2.com'))-int(time.time()))/3600, 115), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_0.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_1.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test5_2.com'))-int(time.time()))/3600, 114), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_0.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_1.com'))-int(time.time()))/3600, 113), True)
		self.assertEqual(check_eq((int(get_ttl_redis('test6_2.com'))-int(time.time()))/3600, 113), True)


#===============================================================================
# test redis_start shell script two time and then stop it
#===============================================================================
'''
def test_redis_start_and_stop_script():
	os.system("chmod 755 %s" % ra_start_script)
	os.system("chmod 755 %s" % ra_stop_script)
	os.system(ra_start_script)
	sub = subprocess.Popen("service redis status", stdout=subprocess.PIPE, stderr = subprocess.PIPE , shell = True)
	status = sub.stdout.read()
	sub.stdout.close()
	yield check_str_contain, status, "is running"
	os.system(ra_start_script)
	sub = subprocess.Popen("service redis status", stdout=subprocess.PIPE, stderr = subprocess.PIPE , shell = True)
	status = sub.stdout.read()
	sub.stdout.close()
	yield check_str_contain, status, "is running"
	os.system(ra_stop_script)
	sub = subprocess.Popen("service redis status", stdout=subprocess.PIPE, stderr = subprocess.PIPE , shell = True)
	status = sub.stdout.read()
	sub.stdout.close()
	yield check_str_contain, status, "is stopped"
	ret = os.system(ra_stop_script)
	sub = subprocess.Popen("service redis status", stdout=subprocess.PIPE, stderr = subprocess.PIPE , shell = True)
	status = sub.stdout.read()
	sub.stdout.close()
	yield check_str_contain, status, "is stopped"


'''


if __name__ == '__main__':
	unittest.main()
	# add test case to test redis_start.sh and redis_stop.sh
	test_redis_start_and_stop_script()



