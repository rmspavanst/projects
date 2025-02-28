Install Maven on Jenkins (Maven Build Server)
-------------------------------------------

1. Download maven packages https://maven.apache.org/download.cgi onto Jenkins server. In this case I am using /opt/maven as my installation     
   directory - Link : https://maven.apache.org/download.cgi

   Install jdk11 ( sudo yum -y install  java-11-openjdk java-11-openjdk-devel)
   java -version
   
2. Creating maven directory under /opt
        mkdir /opt/maven
        cd /opt/maven
3. downloading maven version 3.8.2
        wget https://downloads.apache.org/maven/maven-3/3.8.2/binaries/apache-maven-3.8.2-bin.zip
        unzip /opt/maven/apache-maven-3.8.2-bin.zip
        cd apache-maven-3.8.2/bin
        ./mvn --version

   Note: for testing clone the source code and run manually
         git clone https://github.com/rmspavan/ST_CICD.git
         cd ST_CICD && LL -la (can see pom.xml)
         /opt/maven/bin/mvn package (to build)
         ll  (can see target dir, it's have all the generated artifacts)

        
4. Setup M2_HOME and M2 paths in .bash_profile of user and add these to path variable

        vi ~/.bash_profile
        M2_HOME=/opt/maven
        M2=$M2_HOME/bin
        PAHT=<Existing_PATH>:$M2_HOME:$M2

5. Check point
   logoff and login to check maven version Check maven version

          mvn --version



6. So far you have completed installation of maven software to support maven plugin on jenkins console. Let's jump onto jenkins to complete   remining steps.

7. Setup maven on jenkins console
        7.1 Install maven plugin without restart
                Manage Jenkins > Jenkins Plugins > available > Maven Invoker
        
8. (Update) Install "Maven Integration" Plugin as well
        8.1 Install maven Integration Plugin without restart
               Manage Jenkins > Jenkins Plugins > available > Maven Integration

9. Configure java path
        Manage Jenkins > Global Tool Configuration > Maven