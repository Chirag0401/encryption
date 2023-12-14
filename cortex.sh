#!/bin/bash
# UserData script for Amazon Linux

# Path of panw directory on the Server
if [ ! -d "/etc/panw" ]; then
  mkdir -p /etc/panw
fi

# Path of cortex.conf file on the endpoint
if [ ! -f "/etc/panw/cortex.conf" ]; then
  touch /etc/panw/cortex.conf
fi

# Ensure bashrc contains YUM_PROXY
if ! grep -q 'export YUM_PROXY={{squid_server}}' ~/.bashrc && [ "$(hostname)" != "non_proxy_server" ]; then
  echo 'export YUM_PROXY={{squid_server}}' >> ~/.bashrc
fi

# Ensure bashrc contains HTTP_PROXY
if ! grep -q 'export HTTP_PROXY={{squid_server}}' ~/.bashrc && [ "$(hostname)" != "non_proxy_server" ]; then
  echo 'export HTTP_PROXY={{squid_server}}' >> ~/.bashrc
fi

# Ensure bashrc contains HTTPS_PROXY
if ! grep -q 'export HTTPS_PROXY={{squid_server}}' ~/.bashrc && [ "$(hostname)" != "non_proxy_server" ]; then
  echo 'export HTTPS_PROXY={{squid_server}}' >> ~/.bashrc
fi

# Ensure /etc/yum.conf contains PROXY
if ! grep -q 'proxy={{squid_server}}' /etc/yum.conf && [ "$(hostname)" != "non_proxy_server" ]; then
  echo 'proxy={{squid_server}}' >> /etc/yum.conf
fi

# Install dependent packages
sudo yum install -y policycoreutils-python.x86_64 selinux-policy-devel.noarch

# Whitelist some URLs in squid.conf
echo 'acl whitelist dstdomain fisproduction.xdr.us.paloaltonetworks.com' >> /etc/squid/squid.conf
# Add other whitelist entries...

# Add the Server ID and Server URL to cortex.conf
echo '--distribution-id bace349faf0f473b82d42e56eff35c87' >> /etc/panw/cortex.conf
echo '--distribution-server https://distributions.traps.paloaltonetworks.com' >> /etc/panw/cortex.conf
echo '--proxy-list={{ proxy }}' >> /etc/panw/cortex.conf

# Copy Cortex Agent
cp /home/ec2-user/FIS-Linux-7_7_2_66464.zip /etc/panw

# Unarchive Cortex Agent
tar -xzvf /home/ec2-user/FIS-Linux-7_7_2_66464_rpm.tar.gz -C /etc/panw

# Check if Cortex Agent is installed
if ! rpm -q cortex-agent; then
  # Install the Cortex Agent package
  sudo yum install /etc/panw/cortex-7.7.2.66464.rpm -y
else
  # Reinstall the Cortex Agent package
  sudo yum reinstall /etc/panw/cortex-7.7.2.66464.rpm -y
fi

# Set/Add the Proxy Server into the cortex.conf file 
/opt/traps/bin/cytool proxy set "{{proxy}}"

# Stop all
/opt/traps/bin/cytool runtime stop all

# Sleep for 30 seconds
sleep 30

# Start all
/opt/traps/bin/cytool runtime start all

# Check when agent last time checked in
/opt/traps/bin/cytool last_checkin
