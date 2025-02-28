C. Configure SonarQube: (2core and 2gb ram, ports: 22, 5432, 9000, 80 , JDK 11)
        a. Install & Configure PSQL
        b. Install & Configure SonarQube scanner
    

--> Install Java
--------------------
1. yum install java-1.8* -y or install openjdk-11-jdk -y

--> Install PostgreSql
-------------------------

1. dnf module list postgresql
2. sudo dnf module enable postgresql:13 
3. yum install postgresql-server postgresql-devel postgresql -y
4. /usr/bin/postgresql-setup --initdb
5. sudo systemctl start postgresql
6. sudo systemctl enable postgresql

7. su - postgres
8. psql
    --   CREATE USER sonar WITH PASSWORD 'sonar';
    --   ALTER USER sonar WITH SUPERUSER

9. Edit the pg_hba.conf
    NOTE: Need to run #pg_ctl reload to reload the config.
        Which hosts are allowed to connect
        How clients are authenticated
        Which PostgreSQL user names they can use
        Which databases they can access

    vi /var/lib/pgsql/data/pg_hba.conf
    * change METHOD from peer/ident to trust 

 psql
    --   CREATE DATABASE sonar;
    --   GRANT ALL PRIVILEGES ON DATABASE sonar TO sonar;
service postgresql restart (in root user)


--> SonarQube Setup:
-----------------------
1. Download soarnqube and extract it.

        wget https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-8.9.2.46101.zip
        unzip sonarqube-8.9.2.46101.zip
        mv sonarqube-8.9.2.46101.zip sonarqube
        cd sonarqube

2. Configure JDBC details in the "$SONARQUBE-HOME/conf/sonar.properties" file

        vi sonar.properties
        sonar.jdbc.username=sonar
        sonar.jdbc.password=sonar
        
        #--postgress---
        sonar.jdbc.url=jdbc:postgresql://localhost/sonar/
        
        sonar.path.data=/var/sonarqube/data
        sonar.path.temp=/var/sonarqube/temp

3. Add sonar user and grant ownership to /opt/sonarqube directory
        useradd sonar

        4.1 Create & Modify sonarQube folder permissions

                mkdir /var/sonarqube
                chown -R sonar /var/sonarqube
                chown -R sonar /opt/sonarqube

4. Update below parameters to the "/etc/sysctl.conf" file and run "#sysctl -p" command to load the parameters.

        vm.max_map_count=524288
        fs.file-max=131072

5. Update below parameters to the /etc/security/limits.conf" file  - Edit from root user

        sonar hard nofile 65535
        sonar soft nofile 65535
        
        5.1. Start SonarQube service from sonar user
                su - sonar
                cd /opt/sonarqube/bin/linux-86-64
                ./sonar.sh start
                ./sonar.sh status
                firewall-cmd --permanent --add-port=9000/tcp
                sudo firewall-cmd --reload

6. open browser and access the sonarqube
        http://localhost:9000 
        login with admin/admin and cnage password

7. In sonarqube, create new project and specify the project key and Dispay key
       Project Key: webapp
       Display Key: demo-webapp
------>click on Setup and generate token (copy the token, it's required to integrate with maven) (4c131801c0a088101ab86fd018dbfe0a23779eb9)
       click continue and select prokject main language(java) and build tool(maven). 
       copy the execte cmd to Run in Maven server.

{mvn sonar:sonar \
  -Dsonar.projectKey=webapp \
  -Dsonar.host.url=http://192.168.1.247:9000 \
  -Dsonar.login=f9cb0a05f2f32070605b330a43ddefb8580723f1}

    7.1 go to maven server
         cd /ST_CICD/java_source/
         /opt/apache-maven-3.8.2/bin/paste the execute cmd (it will provide the url, open in browser)
         



--> Integrating SonarQube with Jenkins
---------------------------------------
  * Download sonar scanner onto Jenkins
  * Update sonar scanner properties
  * Install sonar scanner plugun
  * Configure sonar scanner and sonar server
  * Execute job

1. On Sonarqube server
        Generate a sonarqube token to authenticate from Jenkins

2. On Jenkins server
        Install Sonarqube plugin
        Configure Sonarqube credentials
        Add Sonarqube to jenkins "configure system"
        Install SonarScanner
        Run Pipeline job


    
        