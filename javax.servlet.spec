Name:		javax.servlet
Version:	4.0.1
Release:	2
Summary:	Java Servlet API
Group:		Development/Java
License:	ASL 2.0 AND (CDDL-1.0 OR GPL-2.0-only WITH Classpath-exception-2.0)
URL:		https://javaee.github.io/servlet-spec/
Source0:	https://repo1.maven.org/maven2/javax/servlet/javax.servlet-api/%{version}/javax.servlet-api-%{version}-sources.jar

BuildArch:	noarch
BuildRequires:	python
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
Java Servlet %{version} is the Servlet API used by web applications and
by containers that register javax.servlet.Servlet. The system POM is
parentless: the upstream POM parents net.java:jvnet-parent 3, and that
parent cannot be installed beside the packaged jvnet-parent 5. Classes
are compiled for Java 8. The jar is the named module javax.servlet.

%prep
%setup -q -c -T
# The builders' rpmuncompress passes a sources jar to tar.
python - %{SOURCE0} <<'PY'
import sys
import zipfile
zipfile.ZipFile(sys.argv[1]).extractall(".")
PY
cp -p META-INF/LICENSE.txt LICENSE
rm -rf META-INF pom.xml
mkdir -p src/main/java src/main/resources
python - <<'PY'
import shutil
from pathlib import Path

root = Path("javax")
if not root.is_dir():
    raise SystemExit("missing javax sources")
java_root = Path("src/main/java")
res_root = Path("src/main/resources")
for path in root.rglob("*"):
    if not path.is_file():
        continue
    rel = path.relative_to(root)
    if path.suffix == ".java":
        dest = java_root / "javax" / rel
    elif path.suffix == ".properties":
        dest = res_root / "javax" / rel
    else:
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(path, dest)
shutil.rmtree(root)
javas = list(java_root.rglob("*.java"))
props = list(res_root.rglob("*.properties"))
if len(javas) != 77:
    raise SystemExit("java files " + str(len(javas)))
if len(props) != 7:
    raise SystemExit("properties " + str(len(props)))
for name in ("Servlet.java", "http/HttpServlet.java"):
    if not (java_root / "javax/servlet" / name).is_file():
        raise SystemExit("missing " + name)
license_text = Path("LICENSE").read_text(encoding="utf-8")
if "COMMON DEVELOPMENT AND DISTRIBUTION LICENSE" not in license_text:
    raise SystemExit("LICENSE is not the CDDL text")
if "CLASSPATH" not in license_text:
    raise SystemExit("LICENSE has no Classpath exception")
if list(Path(".").rglob("*.jar")) or list(Path(".").rglob("*.class")):
    raise SystemExit("prebuilt binary remains")
pom = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>javax.servlet</groupId>
  <artifactId>javax.servlet-api</artifactId>
  <version>%{version}</version>
  <packaging>jar</packaging>
  <name>Java Servlet API</name>
  <description>Java Servlet %{version} API, packaged without a parent POM.</description>
  <url>https://javaee.github.io/servlet-spec/</url>
  <licenses>
    <license>
      <name>CDDL + GPLv2 with classpath exception</name>
      <url>https://oss.oracle.com/licenses/CDDL+GPL-1.1</url>
      <distribution>repo</distribution>
    </license>
  </licenses>
  <properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <maven.compiler.release>8</maven.compiler.release>
  </properties>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.12.1</version>
        <configuration>
          <release>8</release>
        </configuration>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-jar-plugin</artifactId>
        <version>3.3.0</version>
      </plugin>
    </plugins>
  </build>
</project>
"""
Path("pom.xml").write_text(pom, encoding="utf-8")
text = Path("pom.xml").read_text(encoding="utf-8")
for needle in ("junit", "SNAPSHOT", "<source>", "<target>", "<parent>", "jvnet", "maven-bundle-plugin"):
    if needle in text:
        raise SystemExit("pom contains " + needle)
if "javax.servlet-api" not in text:
    raise SystemExit("pom lost its artifactId")
PY

%build -a
cat > module-info.java <<'EOF'
module javax.servlet {
    exports javax.servlet;
    exports javax.servlet.annotation;
    exports javax.servlet.descriptor;
    exports javax.servlet.http;
}
EOF
javac --release 9 --patch-module javax.servlet=target/classes -d target/classes module-info.java
jar uf target/javax.servlet-api-%{version}.jar -C target/classes module-info.class
java --module-path target/javax.servlet-api-%{version}.jar --describe-module javax.servlet > module-describe.txt
grep -q '^javax.servlet' module-describe.txt || { cat module-describe.txt; exit 1; }
if grep -q ' automatic$' module-describe.txt; then
	cat module-describe.txt
	exit 1
fi
grep -q 'exports javax.servlet$' module-describe.txt || { cat module-describe.txt; exit 1; }
grep -q 'exports javax.servlet.http' module-describe.txt || { cat module-describe.txt; exit 1; }
grep -q 'exports javax.servlet.annotation' module-describe.txt || { cat module-describe.txt; exit 1; }
grep -q 'exports javax.servlet.descriptor' module-describe.txt || { cat module-describe.txt; exit 1; }
python - <<'PY'
import struct
import zipfile
from pathlib import Path

jar = Path("target/javax.servlet-api-%{version}.jar")
if not jar.is_file():
    raise SystemExit("missing jar")
with zipfile.ZipFile(jar) as zf:
    names = set(zf.namelist())
    need = [
        "javax/servlet/Servlet.class",
        "javax/servlet/http/HttpServlet.class",
        "javax/servlet/LocalStrings.properties",
        "javax/servlet/http/LocalStrings.properties",
        "module-info.class",
    ]
    missing = [name for name in need if name not in names]
    if missing:
        raise SystemExit("jar missing " + " ".join(missing))
    if any(name.endswith(".java") for name in names):
        raise SystemExit("sources leaked into the jar")

    def major(name):
        data = zf.read(name)
        return struct.unpack(">H", data[6:8])[0]

    servlet_major = major("javax/servlet/Servlet.class")
    module_major = major("module-info.class")
if servlet_major != 52:
    raise SystemExit("Servlet class version " + str(servlet_major))
if module_major < 53:
    raise SystemExit("module-info class version " + str(module_major))
pom = Path("pom.xml").read_text(encoding="utf-8")
if "<parent>" in pom or "jvnet" in pom:
    raise SystemExit("installed pom still has a parent")
PY

%install -a
mkdir -p %{buildroot}%{_datadir}/java/modules
ln -s ../javax.servlet.jar %{buildroot}%{_datadir}/java/modules/javax.servlet-%{version}.jar
ln -s javax.servlet.jar %{buildroot}%{_datadir}/java/javax.servlet-%{version}.jar

%files -f .mfiles
%doc LICENSE
%{_datadir}/java/javax.servlet-%{version}.jar
%{_datadir}/java/modules/javax.servlet-%{version}.jar
