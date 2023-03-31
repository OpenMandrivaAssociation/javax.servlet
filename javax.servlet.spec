%{?_javapackages_macros:%_javapackages_macros}

Name:           javax.servlet
Version:        4.0.1
Release:        2
Summary:        Java Servlet API
Group:		Development/Java
License:        ASL 2.0
URL:            https://javaee.github.io/servlet-spec/
# Source for releases:
Source0:        https://maven.java.net/content/repositories/releases/javax/servlet/javax.servlet-api/%{version}/javax.servlet-api-%{version}-sources.jar
Source1:        https://maven.java.net/content/repositories/releases/javax/servlet/javax.servlet-api/%{version}/javax.servlet-api-%{version}.pom
BuildArch:      noarch
BuildRequires:	jdk-current
BuildRequires:	javapackages-local

%description
Java Servlet is the foundation web specification in the Java
Enterprise Platform. Developers can build web applications using
the Servlet API to interact with the request/response workflow.

Java Servlets is a JCP Standard technology for interacting with
the web on the Java EE platform.

%package javadoc
Summary:        API documentation for %{name}
Obsoletes:      %{name}-manual < %{version}-%{release}

%description javadoc
This package provides %{summary}.

%prep
%autosetup -p1 -c %{name}-%{version}-src

%build
. %{_sysconfdir}/profile.d/90java.sh
export PATH=$JAVA_HOME/bin:$PATH
export LANG=en_US.utf-8

buildjar() {
	if ! [ -e module-info.java ]; then
		MODULE="$1"
		shift
		echo "module $MODULE {" >module-info.java
		find . -name "*.java" |xargs grep ^package |sed -e 's,^.*package ,,;s,\;.*,,' -e 's/^[[:space:]]*//g' -e 's/[[:space:]]*\$//g' |sort |uniq |while read e; do
			echo "  exports $e;" >>module-info.java
		done
		for i in "$@"; do
			echo "	requires $i;" >>module-info.java
		done
		echo '}' >>module-info.java
	fi
	find . -name "*.java" |xargs javac
	find . -name "*.class" -o -name "*.properties" |xargs jar cf $MODULE-%{version}.jar
	jar i $MODULE-%{version}.jar
	# Javadoc for javax.servlet is broken and in need of compile
	# fixes
	#javadoc -d docs -sourcepath . $MODULE
}
buildjar javax.servlet

%install
mkdir -p %{buildroot}%{_javadir}/modules %{buildroot}%{_mavenpomdir}
cp javax.servlet-%{version}.jar %{buildroot}%{_javadir}/modules
ln -s modules/javax.servlet-%{version}.jar %{buildroot}%{_javadir}/
ln -s modules/javax.servlet-%{version}.jar %{buildroot}%{_javadir}/javax.servlet.jar
cp %{S:1} %{buildroot}%{_mavenpomdir}/
%add_maven_depmap javax.servlet-api-%{version}.pom javax.servlet-%{version}.jar

%files -f .mfiles
%{_datadir}/java/modules/*.jar
%{_datadir}/java/*.jar
