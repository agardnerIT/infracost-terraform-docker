FROM python:slim-buster

# Run apt update
RUN apt update

# Install all required packages for terraform
RUN apt-get install -y gnupg software-properties-common curl

# Add the HashiCorp GPG Key
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -

# Add the official HashiCorp Linux repo
RUN apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"

# Run apt update again to get latest packages
RUN apt update

# Install Terraform CLI
RUN apt install -y terraform

# Install Requests
RUN pip install requests

# Install infracost CLI
RUN curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh
