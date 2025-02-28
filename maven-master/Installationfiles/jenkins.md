1. Create Jenkins namespace
  
    kubectl get namespaces

    kubectl create namespace jenkins
    kubectl get namespaces
 
2. Create Jenkins deployment yaml file
 
vi jenkinsdeployment.yaml
 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jenkins
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jenkins
  template:
    metadata:
      labels:
        app: jenkins
    spec:
      containers:
      - name: jenkins
        image: jenkins/jenkins:lts-jdk11
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: jenkins-home
          mountPath: /var/jenkins_home
      volumes:
      - name: jenkins-home
        emptyDir: { }
		
kubectl create -f jenkinsdeployment.yaml -n jenkins
 
 
3. Deploy Jenkins
 
    kubectl get deploy -n jenkins
    kubectl get po -n jenkins
    
    kubectl logs pod_name -n jenkins
 
4. Create Jenkins Service yaml file
 
vi jenkinsservice.yaml

apiVersion: v1
kind: Service
metadata:
  name: jenkins
spec:
  type: NodePort
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: jenkins
 
kubectl create -f jenkinsservice.yml -n jenkins

kubectl get svc -n jenkins


5. Make Jenkins accessible outside by exposing as a Service

kubectl logs pod_name -n jenkins to get the password

227e3b53353f4a97bc4a3c695faba56b

6. Access Jenkins dashboard in browser
    
    * select he Install suggested plugins
    * Create admin password.

7. Install supported plugiuns
   * Manage jenkins --> Manage Pluguns --> avalible --> SonarQube Scanner, Artifactory, SSH Agent, Publish Over SSH
   * Manage Jenkis  --> Clobal Tool Configuration --> Add Maven
                                                        Name: maven
                                                        MAVEN_HOME: /optapche-maven-3.8.2 --> apply

   * Add credentials (sonarqube token): Manage jenkins --> Manage Credentials -->  Add --> kind : Secret text; Secret: paste the sonar qube token; ID: sonar
   * Add credentials (Jfrog Atrifactory): Manage jenkins --> Manage Credentials -->  Add --> kind : Username and Password; Username: admin;  Password: admin; ID: jfrog 
   * Add credentials (Jenkins server): Manage jenkins --> Manage Credentials -->  Add --> kind : Username with Private Key; Username: admin; Private Key: generate ssh-keygen -t rsa , location : /var/lib/jenkins/.ssh/id_rsa; cat id_rsa
   * Add credentials (github/gitlab): Manage jenkins --> Manage Credentials -->  Add --> kind : Username and Password; Username: admin;  Password: admin; ID: git


   * Manage Jenkins --> Congigure System -->  Add SonarQube -->  Name: sonar  
                                                                 server URL: http://artifactoryip:8082/artifactory 
                                                                 Server Auth: sonar
   * Manage Jenkins --> Congigure System -->  Add Artifactory Server --> Server ID: jfrog  
                                                                         URL: http://sonarqubeip:9000 
                                                                         Credentials: jfrog   --> apply/save
    
8. Copy the id_rsa.pub (jenkins server) paste in ansible server fo password less auth
   cat id_rsa.pub -- copy

   go to ansible server--> adduser admin --> mkdir .ssh && cd .ssh
   vi authorized_keys --> paste the .pub key
   chmod  600 authorized_keys

   visudo
   ## Allow root to run any cmds anywhere
   admin  ALL=(ALL)  ALL

9. login to k8s node do the same 
   
   --> adduser admin --> mkdir .ssh && cd .ssh
   vi authorized_keys --> paste the .pub key
   chmod  600 authorized_keys

   visudo
   ## Allow root to run any cmds anywhere
   admin  ALL=(ALL)  ALL


10. Jenkins Pipeline can be written in two modes:

      a. Scripted Pipeline
      b. Declarative Pipeline

  * Login to jenkins
  * New Item --> Enter an item Name: CICD-Pipeline --> Pipeline --> Description: CICD Pipeline using Jenkinsfile
  * Pipelline: Definition: Pipeline script from SCM -->SCM: git --> repository URL: https://github.com/rmspavan/ST_CICD.git; credentials: git; Branch: Masetr-->  Script Path: Jenkinsfile ---> Apply/Save
  * Build Now
   