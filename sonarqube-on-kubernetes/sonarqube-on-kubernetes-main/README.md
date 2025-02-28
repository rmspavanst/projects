# sonarqube-on-kubernetes
YAML configuration to deploy SonarQube on Kubernetes
https://medium.com/codex/easy-deploy-sonarqube-on-kubernetes-with-yaml-configuration-27f5adc8de90




Search
Write

Pavanrms St
Get unlimited access to the best of Medium for less than $1/week.
Become a member



Deploying Databases (PostgreSQL)
Create configuration of Persistent Volume Claim and Deployment for PostgreSQL. You can skip this step if you’re using an external service like a fully managed database service, etc.


And this is my YAML configuration for PostgreSQL deployment, don’t forget to set up the PostgreSQL credential in the config map section, we’ll use it later on Sonar YAML.


Deploying Application
Let’s start with create a configuration of Persistent Volume Claim used by SonarQube


Now we’ll create a Deployment configuration for SonarQube. At this stage, we need to do a little trick in configuring SonarQube. One of the configurations needed to run SonarQube in a Linux environment is to increase the maximum amount of virtual memory by changing the value of max_map_countto 524288. If SonarQube is deployed on a VM, this might not be a big deal as we can change it permanently. But in Kubernetes, it takes a bit of an extra step so this configuration can continue to be applied when pods are created. We can do this by adding a step initContainer in the Deployment template. In this step, we’ll deploy busybox and run the max_map_countconfiguration. I use the value 262144as the minimum required virtual memory to running SonarQube.

The configuration that we need also to pay attention to is the database connection settings. Official SonarQube image parameter using JDBC URL format to set the database connection. You can see the example below

“jdbc:postgresql://postgres:5432/sonar_db”
postgresvalue is based on PostgreSQL container name in Kubernetes environment, we can access the container by using the container name. Change it to your defined container name.
sonar_db value is based on POSTGRESQL_DATABASEwhat we define on the Postgres config map

Deploying Ingress
After the deployment configuration is applied, create an ingress to expose the service. In this step, I will use ingress with the Nginx controller. Deploying an Nginx controller is not too difficult because you can follow the steps in their documentation. Let’s start by adding a secret for the SSL certificates, you’ll need the SSL key and the SLL certificate.

This step is not required if you want to expose the SonarQube in HTTP protocol. You can just remove the tlssection in the Ingress YAML and apply it.

kubectl create secret tls my-fancy-certs — key ssl.key — cert ssl.crt -n sonar
after the secret is created, configure ingress with the Nginx class


And, here we go! just do some quick setup and your sonar is ready to use.

Closing
by installing SonarQube in the Kubernetes environment, we can easily maintain the version we are using. Simply by changing the image tag on the Deployment specs, and voila*!

*Please make sure you read the Release Upgrade Notes to prevent something unwanted

Another thigs to notes is if you’re application compiled in Java 15 environment, make sure you using Jacoco at least version 0.8.7(If you using Jacoco for code coverage reporting), because the Jacoco with version below 0.8.7 doesn’t support Java 15 yet.

In Gradle, you can add the following line to define the Jacoco version :

jacoco {
    toolVersion = “0.8.7”
}
Sonar
Kubernetes
Yaml
Deployment
Sonarqube
62


1




David Layardi
CodeX
Written by David Layardi
18 Followers
·
Writer for 
CodeX

Code Savvy | Pipeline & Automation enthusiast. Focus on learning and implementing DevOps culture | 🌐 https://layardi.com

Follow

More from David Layardi and CodeX
How Cloudflare Zero Trust & VS Code Tunnels Reducing My Back Pain
David Layardi
David Layardi

How Cloudflare Zero Trust & VS Code Tunnels Reducing My Back Pain
Sounds silly, but it’s real. Cloudflare Zero Trust (CZT) & VS Code Remote Tunnels being part of helps me reduce my back pain. In this…
12 min read
·
Apr 15
38



Automate the exploratory data analysis (EDA) to understand the data faster and easier
Mochamad Kautzar Ichramsyah
Mochamad Kautzar Ichramsyah

in

CodeX

Automate the exploratory data analysis (EDA) to understand the data faster and easier
What is EDA?
11 min read
·
Jul 12
1.8K

23



Programming Principles They Don’t Teach You In School
Nishant Aanjaney Jalan
Nishant Aanjaney Jalan

in

CodeX

Programming Principles They Don’t Teach You In School
Introduction to important principles you should know — DRY, KISS, SOLID
10 min read
·
Mar 3
1.6K

21



Automate Export From Jenkins API Job List to Google Sheets Using Google Apps Script
David Layardi
David Layardi

in

Geek Culture

Automate Export From Jenkins API Job List to Google Sheets Using Google Apps Script
One day… you were asked to create a list of data that comes from an API to a common platform appearance that will be easier for the…
7 min read
·
Aug 20, 2021
17



See all from David Layardi
See all from CodeX
Recommended from Medium
Complete Maven, Jenkins, SonarQube, Jfrog & Tomcat set-up
Alvis F
Alvis F

in

Level Up Coding

Complete Maven, Jenkins, SonarQube, Jfrog & Tomcat set-up
Installing Jenkins
9 min read
·
Jul 24
60



Diving into Seamless Code Quality: Unleashing the Power of SonarQube in GitLab Pipeline
Sheetal Agarwal
Sheetal Agarwal

in

Searce

Diving into Seamless Code Quality: Unleashing the Power of SonarQube in GitLab Pipeline
Developer is working on source code using GitLab as version control system and GitLab CI/CD for automating development pipeline. By…
6 min read
·
Jul 14


Lists



General Coding Knowledge
20 stories
·
593 saves


autogen
Natural Language Processing
875 stories
·
409 saves
SONARQUBE installation
Bernesnantony
Bernesnantony

SONARQUBE installation
● SonarQube is an open-source platform developed by SonarSource for continuous inspection of Code Quality
2 min read
·
Jul 23
1



Setting Up a CI/CD Pipeline for a Java Maven Project with GitHub Actions, SonarQube, Docker Hub…
Rkssh - DevOps as a service plateform
Rkssh - DevOps as a service plateform

Setting Up a CI/CD Pipeline for a Java Maven Project with GitHub Actions, SonarQube, Docker Hub…
The pipeline will build the project using Maven, analyze code quality using SonarQube, push the Docker image to Docker Hub, and finally…
2 min read
·
Aug 10


Azure Git Repository
Satya K
Satya K

Azure Git Repository
Azure Git repository and ensure that emails sent from your application don’t go to spam, you can follow these steps:
2 min read
·
5 days ago


How to run sonarqube in local using docker.
Nikesh Kumar T K
Nikesh Kumar T K

in

N-OMS Tech Radar

How to run sonarqube in local using docker.
In this article, we will learn how we can run docker container of sonarqube in our local system and how can we analyze our code locally.
2 min read
·
Jul 15
51



See more recommendations
Help

Status

About

Careers

Blog

Privacy

Terms

Text to speech

Teams