%define WRS_BUILD_NUM %{?_WRS_BUILD_NUM: %{_WRS_BUILD_NUM} } %{?!_WRS_BUILD_NUM: 1000}

Name: new-domain-redis-agent
Summary: New Domain Service Redis Agent installation package
Version: 1.0
Release: %{WRS_BUILD_NUM}
License: Copyright (C) 2009-2010 Trend Micro Incorporated. All rights reserved.
Group: Applications/System
Source: new-domain-redis-agent.tar.gz
BuildRoot: %{_tmppath}/build-root-%{name}
BuildArch: noarch
Packager: Peter L Chang(1.0)
prefix: /trend
Url: http://www.trendmicro.com/
Requires: python-redis >= 2.7
Requires: redis >= 2.8
Requires: ganglia-gmond >= 3.4
Requires: new-domain-common-lib >= %{version}-%{release}
Requires: monit >= 5.4
Requires: boto3 >= 1.1.2
Requires: botocore >= 1.1.12
Requires: python-futures >= 2.2
Requires: jmespath >= 0.7.1
Requires: simplejson >= 3.3.0
Requires: python-six >= 1.9
Requires: python-dateutil >= 1.4

%description

%prep

%setup -n new-domain-redis-agent

%build

%install
rm -rf $RPM_BUILD_ROOT
InstallDir=$RPM_BUILD_ROOT/%{prefix}/new_domain
# create directories
mkdir -p $InstallDir/
mkdir -p $InstallDir/bin/
mkdir -p $InstallDir/conf/
mkdir -p $InstallDir/log/
mkdir -p $InstallDir/raptn/
mkdir -p $InstallDir/mail/
mkdir -p $RPM_BUILD_ROOT/etc/cron.d/
# install files
install -c -m 755 bin/new_domain_redis_agent.py $InstallDir/bin/
install -c -m 755 redis_start.sh $InstallDir/
install -c -m 755 redis_stop.sh $InstallDir/
install -c -m 755 nds_monit_start.sh $InstallDir/
install -c -m 755 nds_monit_stop.sh $InstallDir/
install -c -m 755 nds_healthy_check.sh $InstallDir/
install -c -m 644 conf/new_domain_redis_agent.conf $InstallDir/conf/
install -c -m 644 raptn/filelist.txt $InstallDir/raptn/
install -c -m 644 agent.lck $InstallDir/
# install cron jobs
install -c -m 644 conf/cron_new_domain_redis_agent $RPM_BUILD_ROOT/etc/cron.d/
install -c -m 644 conf/cron_new_domain_redis_agent_mailer $RPM_BUILD_ROOT/etc/cron.d/
# install monit conf
install -c -m 700 conf/redis_monit.conf $InstallDir/conf/
install -c -m 700 conf/nds_healthy_check.conf $InstallDir/conf/

%clean

%pre

/usr/sbin/useradd -u 20034 alps
if [ "${?}" -ne "0" ]; then
	echo "user alps exists"
fi

%post

# add 'vm.overcommit_memory = 1' to /etc/sysctl.conf to solve Background save may fail under low memory condition
echo 'vm.overcommit_memory=1' > /etc/sysctl.conf
/sbin/sysctl vm.overcommit_memory=1
if [ "${?}" -ne "0" ]; then
	echo "Fail to modify /etc/sysctl.conf."
	exit 1
fi

# start redis
/trend/new_domain/redis_start.sh
if [ "${?}" -ne "0" ]; then
	echo "Fail to start redis server."
	exit 1
fi

%preun
# stop redis
if [ "$1" = 0 ] ; then 
	/trend/new_domain/redis_stop.sh
fi
%postun

%files
%defattr(-,alps,alps,0755)
%dir %{prefix}/new_domain/
%dir %{prefix}/new_domain/bin/
%dir %{prefix}/new_domain/conf/
%dir %{prefix}/new_domain/log/
%dir %{prefix}/new_domain/raptn/
%dir %{prefix}/new_domain/mail/
%defattr(0755,alps,alps,-)
%{prefix}/new_domain/bin/new_domain_redis_agent.py*
%defattr(0644,alps,alps,-)
%config(noreplace) %{prefix}/new_domain/conf/new_domain_redis_agent.conf
%{prefix}/new_domain/raptn/filelist.txt
%{prefix}/new_domain/agent.lck
%defattr(0755,root,root,-)
%{prefix}/new_domain/redis_start.sh
%{prefix}/new_domain/redis_stop.sh
%{prefix}/new_domain/nds_monit_start.sh
%{prefix}/new_domain/nds_monit_stop.sh
%{prefix}/new_domain/nds_healthy_check.sh
%defattr(0644,root,root,-)
/etc/cron.d/cron_new_domain_redis_agent
/etc/cron.d/cron_new_domain_redis_agent_mailer
%defattr(0700,root,root,-)
%{prefix}/new_domain/conf/redis_monit.conf
%{prefix}/new_domain/conf/nds_healthy_check.conf

%changelog
* Thu Sep 10 2015 Peter L Chang <peterl_chang@trend.com.tw> 
- Force hourly redis background dump
- Support S3 backup redis dump

* Wed Aug 5 2015 Peter L Chang <peterl_chang@trend.com.tw>
- check main and backup NDS Pattern Process Server's pattern version

* Thu May 23 2013 Peter L Chang <peterl_chang@trend.com.tw> 
- Add log and error handling to avoid pattern time larger than current time 

* Fri May 10 2013 Peter L Chang <peterl_chang@trend.com.tw> 
- modify redis_start.sh to support Redis local DB (Solve case: WRS Infrastructure WRS Infrastructure 1.0-01049)

* Tue May 07 2013 Peter L Chang <peterl_chang@trend.com.tw> 
- modify mail content and body (Solve case: WRS Infrastructure WRS Infrastructure 1.0-01048)

* Mon Apr 08 2013 Peter L Chang <peterl_chang@trend.com.tw> 
- move python-redis dependency from 2.4.13 to 2.7

* Wed Mar 06 2013 Peter L Chang <peterl_chang@trend.com.tw> 
- monitor NDS TTL through monit

* Fri Feb 22 2013 Peter L Chang <peterl_chang@trend.com.tw> 
- modify redis_start.sh/redis_stop.sh and change owner to root user ( Solve case: WRS Infrastructure WRS Infrastructure 1.0-01004)
- modify the term 'pattern version' to 'pattern timestamp' ( Solve case: WRS Infrastructure WRS Infrastructure 1.0-01005)
- adjust the email content

* Wed Feb 06 2013 Peter L Chang <peterl_chang@trend.com.tw> 
- fix monit to watch redis ( Solve case: WRS Infrastructure 1.0-00998)
- fix cronjob command (Solve case: WRS Infrastructure 1.0-00994)

* Mon Feb 04 2013 Peter L Chang <peterl_chang@trend.com.tw> 
- use pattern timestamp instead of current timestamp as [NDS_timestamp] ( Solve case: WRS Infrastructure 1.0-00996)
- add monit to watch redis
- stop redis then start it in rpm install

* Fri Jan 31 2013 Peter L Chang <peterl_chang@trend.com.tw> 1.0
- add --dmax -d in gmetric cmd( Solve case: WRS Infrastructure 1.0-00989)
- remove rsync and xinetd from build script

* Mon Jan 28 2013 Peter L Chang <peterl_chang@trend.com.tw> 1.0
- rpm will retry 2 times and sleep 1 sec for each to insert initial timeversion( Solve case: WRS Infrastructure 1.0-00988)

* Sun Dec 30 2012 Peter L Chang <peterl_chang@trend.com.tw> 1.0
- move common library to build in new-domain-common-lib

* Fri Dec 21 2012 Peter L Chang <peterl_chang@trend.com.tw> 1.0
- applying mail_queue_util to send email

* Mon Dec 17 2012 Peter L Chang <peterl_chang@trend.com.tw> 1.0
- Initial Build
