---
title: Set a SSH Server in a Home Laptop
published: true
date: 2020-04-18 15:32
author: zgxsin
comments: true
categories: [Technical]
---

<!-- wp:paragraph -->
<p>There are difference scenarios to use <a href="https://en.wikipedia.org/wiki/Secure_Shell">ssh</a> connection. Many people might prefer to have a powerful laptop of their own, which they don't move a lot. And they use their other light devices to connect to it whenever they want.  In this blog, I will take about how to set up this kind of service.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Networks and IP Addresses</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most home internet devices are actually connected to a <strong>modem/router</strong> which is provided by your ISP (internet service provider).  The modem and the router provide different functions and they are often combined into one device. <strong>A modem is a device that provides access to the Internet&nbsp;while a router is a device that allows multiple computers to join the same&nbsp;local network</strong>&nbsp;(see <a href="https://pc.net/helpcenter/answers/difference_between_router_and_modem">here</a>).</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For example, usually you will be provided with<strong> Ethernet interfaces</strong>  when you order an internet service. These interfaces are connected to the ISP <strong>modem/router</strong>. You might also have WIFI <strong>interfaces</strong>, which are usually provided by the administrators of your living place. The administrators have their own router connected to ISP <strong>modem/router</strong> via the <strong>Ethernet interface</strong>.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Any of your devices connected to these interfaces (<strong>Ethernet interfaces and WIFI interfaces</strong>) has the same public IP address and but different private IP addresses, which are allocated by the ISP's router or the administrators's router. This is achieved by <strong>NAT</strong> (Network Address Translation). </p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Network Address Translation</strong>. Since many computers and devices can be connected to the internet and there is a<strong> limited number of IPV4</strong> addresses in the world, the router will translate and route all the packets to the correct place. In practice this means that from an outside observer, every device from<strong> router's local network </strong>will share the same public IP address, while inside the local network they will have different private IP addresses. </p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The privates IP addresses are unique behind the ISP's <strong>or</strong> administrators's router so that it can recognize different devices connected to it. <strong>Note that your device connecting to ISP's router might have the same private IP address with your device connecting to administrators's router  as there are two local networks provided by these two routers.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Your personal router works the same way. In case you only have one Ethernet interface at your home provided by your ISP and you want wireless internet connection for your devices, you can buy a router. And you connect the router with the Ethernet interface. Your router will be allocated with a <strong>private IP address</strong> in the ISP router's local network. This can be found in your router's admin page. <strong>From the router's side, this private IP address will be regarded as its public IP address</strong>. <strong>And your router also has a private IP address in its own local network</strong>.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The router itself also has Ethernet interfaces and WIFI interfaces. Now you can connect your devices to the Ethernet interfaces and WIFI interfaces of your own router. And the private IP addresses of your devices are now allocated by your own router instead of ISP's or administrators' router. But the public address of all your devices is still the same, now matter you connect your device to your own router or the ISP router or the administrators' router. Below is an image illustrating the above mentioned configuration.</p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":3421,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/04/image-17.png -->
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>Generally the devices connected to the same local network (<strong>no nested layers</strong>) can communicate with each other, i.e., they can <em>ping</em> each other using their allocated private IP addresses. However, it is up to the router settings. For example, if the router enables wireless isolation, any device which connects to this router cannot ping each other even though they are in the same local network. If your ISP's router enables this setting, you can not do anything. But there is a way to work around it. You can use your own router and connect your devices to it. Now your devices are in the same local network provided by your router. You can disable the wireless isolation in your router setting to make the devices ping each other. </p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Illustration with Examples</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>I have two devices A and B at my hand. I directly connect them to the WIFI "Student" provided by  the administrator's router.</p>
<!-- /wp:paragraph -->

<!-- wp:image {"align":"center","id":3431,"sizeSlug":"large"} -->
<div class="wp-block-image"><figure class="aligncenter size-large"><!-- Image lost in the WordPress migration: uploads/2020/04/image-21.png --></figure></div>
<!-- /wp:image -->

<!-- wp:image {"align":"center","width":572,"height":406} -->
<div class="wp-block-image"><figure class="aligncenter is-resized"><!-- Image lost in the WordPress migration: uploads/2020/04/image-18.png --></figure></div>
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>Then I check the private IP addresses of the two devices. They are 10.0.147.209 and 10.0.150.240 for A (guzhou@guzhou-laptop) and B (zhou@GuoxiangdeMacBook-Pro) respectively.  I ping 10.0.150.240 (B) from A and I cannot find it.  This might be due to the wireless isolation by the administrator's router.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash","highlightLines":"4"} -->
<pre class="wp-block-syntaxhighlighter-code">guzhou@guzhou-laptop:~$ ip addr | grep inet
    inet 127.0.0.1/8 scope host lo
    inet6 ::1/128 scope host 
    inet 10.0.147.209/21 brd 10.0.151.255 scope global dynamic noprefixroute wlp82s0
    inet6 fe80::1a7a:91f4:5:dd9e/64 scope link noprefixroute 
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
    inet6 fe80::42:26ff:fe4a:923/64 scope link 

guzhou@guzhou-laptop:~$ ping 10.0.150.240
PING 10.0.150.240 (10.0.150.240) 56(84) bytes of data.
From 10.0.147.209 icmp_seq=9 Destination Host Unreachable
From 10.0.147.209 icmp_seq=10 Destination Host Unreachable
From 10.0.147.209 icmp_seq=11 Destination Host Unreachable
From 10.0.147.209 icmp_seq=12 Destination Host Unreachable
From 10.0.147.209 icmp_seq=13 Destination Host Unreachable
From 10.0.147.209 icmp_seq=14 Destination Host Unreachable
From 10.0.147.209 icmp_seq=15 Destination Host Unreachable
From 10.0.147.209 icmp_seq=16 Destination Host Unreachable
From 10.0.147.209 icmp_seq=17 Destination Host Unreachable
From 10.0.147.209 icmp_seq=18 Destination Host Unreachable

</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:syntaxhighlighter/code {"language":"bash","highlightLines":"6"} -->
<pre class="wp-block-syntaxhighlighter-code">[zhou@GuoxiangdeMacBook-Pro ~]$ ifconfig | grep inet
	inet 127.0.0.1 netmask 0xff000000 
	inet6 ::1 prefixlen 128 
	inet6 fe80::1%lo0 prefixlen 64 scopeid 0x1 
	inet6 fe80::6a:ccec:5e57:a8de%en0 prefixlen 64 secured scopeid 0x4 
	inet 10.0.150.240 netmask 0xfffff800 broadcast 10.0.151.255
	inet6 fe80::ec49:b5ff:fede:df5b%awdl0 prefixlen 64 scopeid 0x9 
	inet6 fe80::ec49:b5ff:fede:df5b%llw0 prefixlen 64 scopeid 0xa 
	inet6 fe80::efaf:9619:8742:f4ae%utun0 prefixlen 64 scopeid 0xb 
	inet6 fe80::ba72:b935:31ce:842b%utun1 prefixlen 64 scopeid 0xc 
	inet6 fe80::4cc:2204:251a:69cd%utun2 prefixlen 64 scopeid 0xd 
	inet6 fe80::fb9d:5830:5f0a:3290%utun3 prefixlen 64 scopeid 0xe </pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>Now I have my own router connected to the Ethernet interface in my room. Below is my router's information. My router is assigned a private IP address 10.0.89.45, which it will regard as its public IP address, by ISP's router and it has a private IP address 192.168.1.1 in its own local network.</p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":3485,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/04/image-24.png -->
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>I connect my two devices to the WIFI "zgxsin-5G" provided by my own router. </p>
<!-- /wp:paragraph -->

<!-- wp:image {"align":"center","id":3478,"width":568,"height":244,"sizeSlug":"large"} -->
<div class="wp-block-image"><figure class="aligncenter size-large is-resized"><!-- Image lost in the WordPress migration: uploads/2020/04/image-22.png --></figure></div>
<!-- /wp:image -->

<!-- wp:image {"align":"center","id":3480,"sizeSlug":"large"} -->
<div class="wp-block-image"><figure class="aligncenter size-large"><!-- Image lost in the WordPress migration: uploads/2020/04/image-23.png --></figure></div>
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>The private IP addresses of my two devices are changed to 192.168.1.4 (A) and 192.168.1.3 (B). And I can ping 192.168.1.3 (B) from A and vice versa. If  i enable <strong>wireless isolation</strong> in the settings of my own router, they cannot ping each other any more.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash","highlightLines":"4"} -->
<pre class="wp-block-syntaxhighlighter-code">guzhou@guzhou-laptop:~$ ip addr | grep inet
    inet 127.0.0.1/8 scope host lo
    inet6 ::1/128 scope host 
    inet 192.168.1.4/24 brd 192.168.1.255 scope global dynamic noprefixroute wlp82s0
    inet6 fe80::570e:c106:ce00:ee1d/64 scope link noprefixroute 
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
    inet6 fe80::42:26ff:fe4a:923/64 scope link 

guzhou@guzhou-laptop:~$ ping 192.168.1.3
PING 192.168.1.3 (192.168.1.3) 56(84) bytes of data.
64 bytes from 192.168.1.3: icmp_seq=1 ttl=64 time=284 ms
64 bytes from 192.168.1.3: icmp_seq=2 ttl=64 time=4.25 ms
64 bytes from 192.168.1.3: icmp_seq=3 ttl=64 time=21.3 ms
64 bytes from 192.168.1.3: icmp_seq=4 ttl=64 time=45.1 ms
64 bytes from 192.168.1.3: icmp_seq=5 ttl=64 time=67.0 ms
64 bytes from 192.168.1.3: icmp_seq=6 ttl=64 time=4.21 ms


</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:syntaxhighlighter/code {"language":"bash","highlightLines":"6"} -->
<pre class="wp-block-syntaxhighlighter-code">[zhou@GuoxiangdeMacBook-Pro ~]$ ifconfig | grep inet
	inet 127.0.0.1 netmask 0xff000000 
	inet6 ::1 prefixlen 128 
	inet6 fe80::1%lo0 prefixlen 64 scopeid 0x1 
	inet6 fe80::6a:ccec:5e57:a8de%en0 prefixlen 64 secured scopeid 0x4 
	inet 192.168.1.3 netmask 0xffffff00 broadcast 192.168.1.255
	inet6 fe80::ec49:b5ff:fede:df5b%awdl0 prefixlen 64 scopeid 0x9 
	inet6 fe80::ec49:b5ff:fede:df5b%llw0 prefixlen 64 scopeid 0xa 
	inet6 fe80::efaf:9619:8742:f4ae%utun0 prefixlen 64 scopeid 0xb 
	inet6 fe80::ba72:b935:31ce:842b%utun1 prefixlen 64 scopeid 0xc 
	inet6 fe80::4cc:2204:251a:69cd%utun2 prefixlen 64 scopeid 0xd 
	inet6 fe80::fb9d:5830:5f0a:3290%utun3 prefixlen 64 scopeid 0xe</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>In the above examples, my devices always have the same public IP address.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>SSH Configuration</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>To use SHH, you need to have SSH server running in your device.  You can install the openssh-server application, which will allow you to run an SSH server on your device (host device) that will handle requests for access to the host device from other devices. Run the following code to install SSH client and server.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">guzhou@guzhou-laptop:~$ sudo apt-get update &amp;&amp; sudo apt-get upgrade

# Install the openssh-server application and client. You should also install the openssh-client on machines that will be used as clients.
guzhou@guzhou-laptop:~$ sudo apt-get install openssh-client
guzhou@guzhou-laptop:~$ sudo apt-get install openssh-server

# Check whether SSH server is running in your machine.
guzhou@guzhou-laptop:~$ ps -A | grep sshd
 1429 ?        00:00:00 sshd
</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>I install both SSH client and server in my device. I can SSH into my own machine at the same machine using the reserved keyword <strong>localhost</strong>. The default password is the your account password for this machine.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">guzhou@guzhou-laptop:~$ ssh localhost 
guzhou@localhost's password: 
Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 5.3.0-46-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

 * Kubernetes 1.18 GA is now available! See https://microk8s.io for docs or
   install it with:

     sudo snap install microk8s --channel=1.18 --classic

 * Multipass 1.1 adds proxy support for developers behind enterprise
   firewalls. Rapid prototyping for cloud operations just got easier.

     https://multipass.run/

 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

0 packages can be updated.
0 updates are security updates.

Your Hardware Enablement Stack (HWE) is supported until April 2023.
Last login: Sat Apr 18 12:52:26 2020 from 10.0.147.209
guzhou@guzhou-laptop:~$ 
</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading -->
<h2>SSH in the Same Local Network</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If you have your own router connected to the ISP modem/router and your devices are connected to your own router.  After finishing the SSH configuration (install both SSH client and server) for your devices, you can setup SSH connection among each other.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Continuing  with illustration above,  I use this machine B (<strong>zhou@GuoxiangdeMacBook-Pro</strong>) as a SSH client and connect it to SSH server running in the machine A (<strong>guzhou@guzhou-laptop</strong>). The private IP address of A is 192.168.1.4 from the above example.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Now i am in the terminal environment of <strong>A</strong> from <strong>B</strong> using SSH connection.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">[zhou@GuoxiangdeMacBook-Pro ~]$ ssh guzhou@192.168.1.4
The authenticity of host '192.168.1.4 (192.168.1.4)' can't be established.
ECDSA key fingerprint is SHA256:ZcX8wlkJ2NQoZzzYnNDbT1kbjQmqQm7cT0cGnFkQoJw.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '192.168.1.4' (ECDSA) to the list of known hosts.
guzhou@192.168.1.4's password: 
Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 5.3.0-46-generic x86_64)
 
 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage
 
 * Kubernetes 1.18 GA is now available! See https://microk8s.io for docs or
   install it with:
 
     sudo snap install microk8s --channel=1.18 --classic
 
 * Multipass 1.1 adds proxy support for developers behind enterprise
   firewalls. Rapid prototyping for cloud operations just got easier.
 
     https://multipass.run/
 
 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch
 
0 packages can be updated.
0 updates are security updates.
 
Your Hardware Enablement Stack (HWE) is supported until April 2023.
Last login: Sat Apr 18 15:42:16 2020 from 192.168.1.4
guzhou@guzhou-laptop:~$ </pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading -->
<h2>SSH in Different Networks</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If my device A (home device) is connected to the Ethernet interface provided by ISP and my device B is connected  to the external network, i.e., they have different public IP addresses, it is not trivial for device B to SSH into device A since there are two layers of NAT among device A.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>This is the double NAT problem.  There is no easy way to do this but to contact your ISP to change their router setting. However, you can use a VPN server to do this.</p>
<!-- /wp:paragraph -->
