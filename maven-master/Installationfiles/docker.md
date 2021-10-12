1. Install docker engine

    yum install docker -y
    service docker start
    service docker status

2. Pull Tomcat image from DockerHub
   
    docker pull tomcat
    docker images

3. Copy the .war form arifactory
   wget http://localhost:8081/artifactory/.war  (get the url form libs-release)

Note: create Dockerfile
-----   
FROM tomcat:latest
MAINTAINER "systemizer" 
COPY ./cicd.war /usr/local/tomcat/webapps

4. Create image from Dockerfile

    docker build . --tag webapp-tomcat

5. Create Docker Container

    docker run -d --name STapp -p 8080:8080 webapp-tomcat
    docker ps
    docker logs STapp