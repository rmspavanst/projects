1. Edit the host file in all the nodes

        hostnamectl set-hostname k8s-awx-master
        vi /etc/hosts
        ping k8s-awx-master

2. swapoff

        vi /etc/fstab (commentout the swap)
        swapoff -a

3. Allow the firewall ports 

        firewall-cmd --permanent --add-port=6443/tcp
        firewall-cmd --permanent --add-port=10250/tcp
        systemctl status firewalld
        sudo firewall-cmd --reload

        cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf 
        net.bridge.bridge-nf-call-ip6tables = 1 
        net.bridge.bridge-nf-call-iptables = 1 
        EOF
        sysctl --system

4. Add th ekubernetes repo

cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo 
[kubernetes] 
name=Kubernetes 
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-\$basearch 
enabled=1 
gpgcheck=1 
repo_gpgcheck=1 
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg 
exclude=kubelet kubeadm kubectl 
EOF

5. Disbale SElinux

        setenforce 0 
        sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config
        sestatus

6. Install dependences and docker

        yum install -y yum-utils device-mapper-persistent-data lvm2

        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo 
        yum update -y && yum install containerd.io docker-ce docker-ce-cli

mkdir /etc/docker 
cat > /etc/docker/daemon.json <<EOF 
{ 
  "exec-opts": ["native.cgroupdriver=systemd"], 
  "log-driver": "json-file", 
  "log-opts": { 
    "max-size": "100m" 
  }, 
  "storage-driver": "overlay2", 
  "storage-opts": [ 
    "overlay2.override_kernel_check=true" 
  ] 
} 
EOF

    mkdir -p /etc/systemd/system/docker.service.d 
    systemctl daemon-reload 
    systemctl restart docker 
    systemctl enable docker

7. Install kubernetes

    yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes 
    systemctl enable --now kubelet
    cat /etc/sysconfig/network-scripts/ifcfg-enp0s3

8. Initiate masterNode

    kubeadm init --pod-network-cidr 10.244.0.0/16 --apiserver-advertise-address=192.168.1.123

    watch docker images

    kubeadm join 192.168.0.123:6443 --token 77h1ak.dkb8iu8lvwb3btrg --discovery-token-ca-cert-hash sha256:fe300860ee55a41082aa068d874d876dcb3e596318d604baf898b16ce9ef7c92


mkdir -p $HOME/ .kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

9. to create network

kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"

yum install bash-completion 
echo "source <(kubectl completion bash)" >> ~/.bashrc

10. join worker nodes (run the below cmd in worker nodes)
    
    kubeadm join 192.168.0.123:6443 --token 77h1ak.dkb8iu8lvwb3btrg --discovery-token-ca-cert-hash sha256:fe300860ee55a41082aa068d874d876dcb3e596318d604baf898b16ce9ef7c92

11. to change the Role

    kubectl label node <node name> node-role.kubernetes.io/<role name>=<key - (any name)>
    kubectl label node kubernetes-worker1 node-role.kubernetes.io/worker1=worker1


12. Run the deployment manifest file

        kubectl aaply -f create-K8s-deployment.yaml
        kubectl get deploy,po,svc -owide
        