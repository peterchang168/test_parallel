#!/bin/sh

build_dir=$1

if [ $build_dir ]; then
	echo "build destionation =" $build_dir
else
	echo "No build_dir specified."
	echo
	echo "build.sh <BUILD_PATH>"
	exit -1
fi

# run unittest first
/bin/sh ./test/unittest.sh $(pwd)
if [ "$?" -ne "0" ]; then
	echo "unit test failed, exit build procedure."
	exit -1
fi

cur_dir=$(pwd)
package_name=new-domain-redis-agent
package_dir=$build_dir/$package_name

rm -rf $package_dir
mkdir -p $package_dir/

# just copy the files
cp -rf ./ $package_dir

# create md5 list
cd $package_dir
find -type f | xargs md5sum > md5sum.txt

cd ..
tar zcvf $package_name.tar.gz $package_name
rm -rf $package_name/*
mv $package_name.tar.gz $package_name

# clear rpmbuild dir
rm -rf $HOME/rpmbuild/
rm -f ~/.rpmmacros

# build RPMs
echo "%_topdir $HOME/rpmbuild/" > ~/.rpmmacros
mkdir -p $HOME/rpmbuild/BUILD/
mkdir -p $HOME/rpmbuild/SPECS/
mkdir -p $HOME/rpmbuild/RPMS/
mkdir -p $HOME/rpmbuild/SRPMS/
mkdir -p $HOME/rpmbuild/SOURCES/
rpmbuild -tb --define "_WRS_BUILD_NUM $WRS_BUILD_NUM" $package_name/$package_name.tar.gz
if [ $? != 0 ]; then
    echo build RPM failed
    exit -1;
fi
mkdir -p $package_name/rpm_packages/
cp -r $HOME/rpmbuild/RPMS/* $package_name/rpm_packages/
rm -rf $HOME/rpmbuild/
rm -f ~/.rpmmacros

cd $cur_dir
