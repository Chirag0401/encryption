#!/bin/bash
# UserData script for Amazon Linux

# Set the Squid proxy server address
squid_server="http://your_squid_server:3128"

# Include variables from vars/ppe.yaml
source /etc/ansible/vars/ppe.yaml

# Ensure bashrc contains YUM_PROXY
if ! grep -q "export YUM_PROXY=$squid_server" ~/.bashrc && [ "$(hostname)" != "non_proxy_server" ]; then
  echo "export YUM_PROXY=$squid_server" >> ~/.bashrc
fi

# Ensure /etc/yum.conf contains PROXY
if ! grep -q "proxy=$squid_server" /etc/yum.conf && [ "$(hostname)" != "non_proxy_server" ]; then
  echo "proxy=$squid_server" >> /etc/yum.conf
fi

# Install LDAP client packages
sudo yum install -y openldap-clients pam_ldap nss-pam-ldapd sssd sssd-client

# Ensure dependencies are installed
if [ "$(ansible_distribution)" == "CentOS" ] || [ "$(ansible_distribution)" == "Amazon" ]; then
  sudo yum install -y libselinux-python
fi

# Put Selinux in permissive mode
if [ "$(ansible_distribution)" == "CentOS" ] || [ "$(ansible_distribution)" == "Amazon" ]; then
  sudo setenforce permissive
fi

# Add lines to /etc/hosts
echo '172.16.32.199 UKDC1-OC-ADC01.worldpaypp.local' >> /etc/hosts
# Add other host entries...

# Join a node to an LDAP server
authconfig --enableshadow --enablecache --disablekrb5 --enableforcelegacy --ldapbasedn "dc=worldpaypp,dc=local" --ldapserver "$ldapServer" --update

# Enable home dir
authconfig --enablesssd --enablesssdauth --enablelocauthorize --enablemkhomedir --update

# Replace line for tls_cacerts
sed -i 's/TLS_CACERTDIR.*/TLS_CACERTDIR   \/etc\/openldap\/cacerts/' /etc/openldap/ldap.conf

# Copy files
cp ../files/sshd_config /etc/ssh/sshd_config
cp ../files/sssd.conf /etc/sssd/sssd.conf

# Create sudoers file
echo "your_sudoers_content_here" > /etc/sudoers.d/20-infra-ped-admin-users
chmod 0440 /etc/sudoers.d/20-infra-ped-admin-users

# Validate sudoers file
visudo -cf /etc/sudoers

# Copy certificate files based on distribution
if [ "$(ansible_distribution)" == "RedHat" ]; then
  cp ../files/ppe_certs/*.pem /etc/openldap/certs/
elif [ "$(ansible_distribution)" == "CentOS" ] || [ "$(ansible_distribution)" == "Amazon" ]; then
  cp ppe_certs/*.pem /etc/openldap/cacerts/
fi

# Replace line for ldap_tls_cacertdir
sed -i 's/ldap_tls_cacertdir = \/etc\/openldap\/certs/ldap_tls_cacertdir = \/etc\/openldap\/cacerts/' /etc/sssd/sssd.conf

# Change file ownership
chown root:root /etc/sssd/sssd.conf
chmod 400 /etc/sssd/sssd.conf

# Rehash the certificate
if [ "$(ansible_distribution)" == "CentOS" ] || [ "$(ansible_distribution)" == "Amazon" ]; then
  cacertdir_rehash /etc/openldap/cacerts/
elif [ "$(ansible_distribution)" == "RedHat" ]; then
  openssl rehash /etc/openldap/certs/
fi

# Stop SSSD service
sudo systemctl stop sssd

# Remove files
rm -f /var/lib/sss/db/* /var/log/sssd/*

# Disable LDAP in authconfig
authconfig --updateall --disableldap --disableldapauth

# Start SSSD service
sudo systemctl start sssd
sudo systemctl enable sssd

# Restart sshd service
sudo systemctl restart sshd
sudo systemctl enable sshd

# Populate service facts
systemctl list-units --type=service --all

# Reboot system if Selinux was set to permissive
if [ -f /var/run/reboot-required ]; then
  sleep 2 && shutdown -r now "Ansible package updates triggered"
fi
