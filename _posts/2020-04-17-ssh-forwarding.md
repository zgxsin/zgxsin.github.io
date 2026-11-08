---
title: SSH Forwarding
published: true
date: 2020-04-17 22:08
author: zgxsin
comments: true
categories: [Miscellaneous]
---

<!-- wp:paragraph -->
<p>I will talk about ssh forwarding in this blog. The main content contains local  forwarding and remote forwarding. I will take the <a href="https://github.com/cdr/code-server">coder_server</a> as an example in the end.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Local Forwarding</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>SSH local forwarding is to forward a port from local machine to the remote machine. <strong>The local machine is where you set up SSH connection</strong>. Local forwarding is set up with the <code>-L</code> option.  The command to set up local forwarding is:</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code># Run this command in your machine (local machine).
ssh user_name@ssh_connected_ip_address -L  local_port_number:localhost:remote_port_number</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>This will forward any connection to local_port_number of your local machine to the remote_port_number of the remote machine, which is <strong>user_name@ssh_connected_ip_address</strong> in this case.  For example,  if someone connects to your computer with a web browser, he/she gets the response of the web server running on <strong>remote machine</strong> if applicable (the port number is set according and the web server is running in the remote machine)</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>In the above example,<strong> the localhost is the remote machine</strong>. They can also be different.</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code># Run this command in your machine (local machine).
ssh user_name@ssh_connected_ip_address -L  local_port_number:forwarded_host:forwarded_port_number</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>The above command set up the ssh connection between the local machine and the remote machine (<strong>user_name@ssh_connected_ip_address</strong>). It will forward any connection to the local_port_number of the local machine to forwarded_port_number of the<strong> forwarded_host</strong>, which can be reached by the remote machine.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Below is a screenshot demonstrating the above concept. The <em>remotehost</em> in the image is actually the <em>remote machine </em>in our code above. Take care of the arrow in the image. It means the direction of forwarding.</p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":3374,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/04/image-13.png -->
<!-- /wp:image -->

<!-- wp:heading -->
<h2>Remote Forwarding</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>SSH remote forwarding is to forward a port from remote machine to the local machine. <strong>The local machine is where you set up SSH connection</strong>. Remote forwarding is set up with the <code>-R</code> option. The command to set up remote forwarding is:</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code># Run this command in your machine (local machine).
ssh user_name@ssh_connected_ip_address -R  remote_port_number:localhost:local_port_number</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>This will forward any connection to remote_port_number of your remote machine (user_name@ssh_connected_ip_address) to the local_port_number of the local machine. For example, if someone connects to the remote machine with a web browser, he/she gets the response of the web server running on the local machine if applicable (the port number is set according and the web server is running in the local machine).</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>In the above example, the local host is directly the local machine. They can be different as well.</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code># Run this command in your machine (local machine).
ssh user_name@ssh_connected_ip_address -R  remote_port_number:forwarded_host:forwarded__port_number</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>The above command set up the ssh connection between the local machine and the remote machine (<strong>user_name@ssh_connected_ip_address</strong>). It will forward any connection to the remote_port_number of the remote machine to forwarded_port_number of the forwarded_host, which can be reached by the local machine.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Below is a screenshot demonstrating the above concept. The <em>remotehost</em> in the image is actually the <em>remote machine</em> in our code above.</p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":3375,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/04/image-14.png -->
<!-- /wp:image -->

<!-- wp:heading -->
<h2>Example with Code Server</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><a href="https://github.com/cdr/code-server">Code server</a> is a popular open source work to run <a href="https://github.com/Microsoft/vscode">VS Code</a> in the remote server, which is accessible by a web browser in different devices. </p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Here is how I configure coder server:</p>
<!-- /wp:paragraph -->

<!-- wp:group -->
<div class="wp-block-group"><div class="wp-block-group__inner-container"><!-- wp:code -->
<pre class="wp-block-code"><code># Step 1. SSH into my remote server using ssh local forwarding. Make sure the remote server is running ssh server beforehand.
# I use port 8443 in my case
ssh user_name@remote_server_ip_address -L 8443:localhost:8443

# Step 2. Download coder server.

# Now you ssh into your remote server.

# Download the latest code server release file. You need to choose the file based on your machine type.

wget https://github.com/cdr/code-server/releases/download/3.1.1/code-server-3.1.1-linux-x86_64.tar.gz

# Uncompress the file

tar xvf code-server-3.1.1-linux-x86_64.tar.gz

# Go to the uncompressed folder

cd code-server-3.1.1-linux-x86_64/

# Step 3. Start code server in the remote server.

# Run code server with the consistent port number with ssh local forwarding.

./code-server --port 8443

info code-server 3.1.1 28e91ba70cd70fa9adf3f2e3e3b87631b5667ecf
info HTTP server listening on https://127.0.0.1:8443
info - Password is XXXXXXXXXXXXX
info - To use your own password set the PASSWORD environment variable
info - To disable use `--auth none`
info - Not serving HTTPS
info Automatic updates are enabled
info SSH server listening on localhost:33253
info - To disable use `--disable-ssh`

# Step 4. Open a browser in your local machine to visit the VS Code running in the remote server.

Open the browser in the local machine and visit localhost:8443
</code></pre>

<!-- /wp:code -->

<!-- wp:paragraph -->
<p>Finally, you need to enter your password to visit VS Code running in the remote server.</p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":3378,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/04/image-15-1024x582.png -->
<!-- /wp:image --></div></div>
<!-- /wp:group -->

<!-- wp:heading -->
<h2>Reference</h2>
<!-- /wp:heading -->

<!-- wp:list {"ordered":true} -->
<ol><li><a href="https://unix.stackexchange.com/questions/115897/whats-ssh-port-forwarding-and-whats-the-difference-between-ssh-local-and-remot">https://unix.stackexchange.com/questions/115897/whats-ssh-port-forwarding-and-whats-the-difference-between-ssh-local-and-remot</a></li></ol>
<!-- /wp:list -->
