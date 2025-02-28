
1. Installation Steps
   Login to instance as a root user and install Java

     yum install java-1.8* -y or yum install java-openjdk11 -y
     java -version

2. Download Artifactory packages onto /opt/
  
    cd /opt 
    wget https://jfrog.bintray.com/artifactory/jfrog-artifactory-oss-6.9.6.zip    or

    rpm based cmd
    wget https://releases.jfrog.io/artifactory/artifactory-rpms/artifactory-rpms.repo -O jfrog-artifactory-rpms.repo;
    sudo mv jfrog-artifactory-rpms.repo /etc/yum.repos.d/;
    sudo yum update && sudo yum install jfrog-artifactory-oss

3. extract artifactory tar.gz file

    unzip jfrog-artifactory-oss-6.9.6.zip

4. Go inside to bin directory and start the services

    cd /opt/jfrog-artifactory-oss-6.9.6/bin
    ./artifactory.sh start

    or install rpm based install use this cmd's
    service artifactory start

    firewall-cmd --permanent --add-port=8082/tcp
    sudo firewall-cmd --reload
    
5. access artifactory from browser

    http://<PUBLIC_IP_Address>:8082

6. Provide credentials

    username: admin
    password: passwrod 

7. get started and change the new password, select the base URL  http://<PUBLIC_IP_Address>:8082
   create repositories --> maven , click next and finish.
   Artifactory --> Atifacts --> Set Me Up --> repository: libs-snapshot, type password
   click on Generate Maven Settings --> Generate setting --> it will generate xml file ( download the seeting.xml file)
   
   open setting.xml file, change the <username> admin </username> , <password> admin </password> and <url>http://xx.xx.xx.xx:8082/arti.....</url>
   
   7.1 Artifactory --> Atifacts --> Set Me Up --> repository: libs-release --> copy the deploy distributionManagement.


8. open maven server 
   cd .m2  (it will keep all the dependencies in /root/.m2 dir)
   ls -l
   cpoly the the setting.xml file and paste it in .m2 dir

   8.1 cd /ST_CICD/ 
       vi pom.xml
       paste the deploy distributionManagement in before </project>
       /opt/apache-maven3.8.2/bin/mvn -U deploy (it will build the project and deploy the articats to artifactory)

9. Please check the .war file in artifactory dashboard
   artifacts--> libs-release --> project folder 




Integrate Artifactory with Jenkins:
------------------------------------------

1. Login to Jenkins to integrate Artifactory with Jenkins

    Install "Artifactory" plug-in
    Manage Jenkins -> Jenkins Plugins -> available -> artifactory

2. Configure Artifactory server credentials

    Manage Jenkins -> Configure System -> Artifactory
        Artifactory Servers
            Server ID : Artifactory-Server
            URL : Artifactory Server URL
            Username : admin
            Password : `admin@123

3. to test--->

    Create a Maven Project
    3.1 Create a new job
            Job Name : artifactory-project
    3.2 Source code management
            Git URL : get URL here
    3.3 Build Environment
            Resolve artifacts from Artifactory : <provide Artifactory server and repository details>
    3.4 Build - Goals: clean install
    3.5 Post-build Actions
            Deploy Artifacts to Artifactory : <provide Artifactory server and repository details>
    3.6 Execute job