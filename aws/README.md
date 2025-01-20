# aws configure
Provide:
AWS Access Key ID
AWS Secret Access Key
Default region (e.g., us-east-1)
Output format (e.g., json)

# Terraform Configuration: main.tf

# Steps to Deploy:
1. Initialize Terraform:
    terraform init

2. Preview the Execution Plan:
    terraform plan

3. Apply the Configuration:
    terraform apply

View Outputs: After deployment, the public IPs, private IPs, and instance IDs of the instances will be displayed in the output.

# Clean Up Resources:
1. To destroy the instances and related resources:
    terraform destroy