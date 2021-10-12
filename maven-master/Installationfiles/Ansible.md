1. Install Ansible Package

    yum install ansible -y 
    ansible --version

2. Install python pip package

    yum install python-pip -y 
    pip install docker-py  

3. Create artifact directory
    mkdir /artifacts

4. Create playbook to create custom container images and push the image to the DockerHub registry.
    vi create-container-image.yaml

5. Run Playbook using Ansible
    ansible-playbook create-container-image.yaml