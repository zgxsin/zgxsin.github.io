---
title: IP Address
published: true
date: 2020-03-30 18:32
author: zgxsin
comments: true
categories: [Miscellaneous]
---
<!-- wp:heading -->
<h2>What is IP Address</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Please check this video to get an intuitive understanding of IP address if you have no idea of it.</p>
<!-- /wp:paragraph -->

<!-- wp:core-embed/youtube {"url":"https://www.youtube.com/watch?v=8zEVA-Bxs-0","type":"video","providerNameSlug":"youtube","className":"wp-embed-aspect-16-9 wp-has-aspect-ratio"} -->
<figure class="wp-block-embed-youtube wp-block-embed is-type-video is-provider-youtube wp-embed-aspect-16-9 wp-has-aspect-ratio"><div class="wp-block-embed__wrapper">
https://www.youtube.com/watch?v=8zEVA-Bxs-0
</div></figure>
<!-- /wp:core-embed/youtube -->

<!-- wp:heading -->
<h2>Public IP Address</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>A public IP address is an&nbsp;IP address&nbsp;that your home or business&nbsp;router&nbsp;receives from your&nbsp;ISP. Public IP addresses are required for any publicly accessible network&nbsp;hardware&nbsp;such as a home router and the servers that host websites ((<a href="https://www.lifewire.com/what-is-a-public-ip-address-2625974">https://www.lifewire.com/what-is-a-public-ip-address-2625974</a>)). To get your public IP address, you can simply type </p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">curl ifconfig.me</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>in your terminal and then you will see you public IP address.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Dynamic IP Address</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Every time your device is connected to the internet, the internet service provider (ISP) will allocate an IP address for your device from their available IP addresses. Since this IP address is changing every time, it is called dynamic IP address. </p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":914,"sizeSlug":"large"} -->
<figure class="wp-block-image size-large"><img src="http://localhost/wp-content/uploads/2020/03/image-23-1024x572.png" alt="" class="wp-image-914"/></figure>
<!-- /wp:image -->

<!-- wp:heading {"level":3} -->
<h3>Static IP Address</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Static IP address is the permanent internet address and never changes. It is an&nbsp;IP address&nbsp;that was <strong>manually</strong> configured for a device, versus one that was assigned by a&nbsp;<a href="https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol">DHCP</a>&nbsp;server. It's called static because it doesn't change.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>A static IP address is useful when you host a website of your own. Because this address won't change, so other people will always know how to connect to it once they know your static IP address.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Private IP Address</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>A&nbsp;private IP address&nbsp;is an unique identifier for all the devices behind a router or other device that <strong>serves</strong> IP addresses. The static IP address in most ways works the same as public IP address.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>With private IP addresses, the devices in your home can have the same private IP addresses as your neighbor's devices, or anyone else's all around the world.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>When you open a website from your laptop, the request is sent from the laptop to the router as a private IP address, after which the router requests the website from your ISP using the public IP address assigned to your network. Once the request has been made, the operations are reversed — the ISP sends the address of the website to your router, which forwards the address to the laptop that asked for it.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Understanding <em>ip addr show</em></h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>In Linux system, we use </p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">ip addr show </pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>to check the <strong>private</strong> IP address of the device. <strong>ifconfig</strong> is not recommended ((<a href="http://blog.cyphermox.net/2017/05/if-youre-still-using-ifconfig-youre.html">http://blog.cyphermox.net/2017/05/if-youre-still-using-ifconfig-youre.html</a>)).</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The result from this command is a little complex. </p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":956,"sizeSlug":"large"} -->
<figure class="wp-block-image size-large"><img src="http://localhost/wp-content/uploads/2020/03/image-26.png" alt="" class="wp-image-956"/></figure>
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>Here are the <a href="http://linux-ip.net/html/tools-ip-address.html">explanations</a>. I briefly list it here and add detailed information.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Each device is given an sequential number as an identifying number. This is merely a convenience, and should not be used to refer to devices. The second field in an entry is the interface name (which usually corresponds to the device name). Next, we see the<strong> device&nbsp;flags</strong>&nbsp;and <strong>maximum transmission unit size.</strong> The final fields in the first line of output for each device entry refer to the traffic control queuing discipline (<strong>qdisc</strong>) and the Ethernet buffer transmit queue length (<strong>qlen</strong>). For more on understanding and using traffic control under linux, see&nbsp;<a href="http://lartc.org/howto/">the LARTC documentation</a>.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The second line of output describes the link layer characteristics of the device. <strong>For Ethernet devices, this will always say "link/ether" followed by the hardware address of the device and the media broadcast address</strong>. For more detail on the link layer characteristics of a device see&nbsp;<a href="http://linux-ip.net/html/tools-ip-link.html">here</a>.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Subsequent lines of output describe the <strong>IP addresses</strong> available on each interface. In a typical installation only one address is used on each interface, although an arbitrary number of addresses can also be used on each interface. Each line contains the <strong>IP address</strong> and <strong>netmask</strong> in CIDR notation, an optional broadcast address, scope information and a label. Let's examine the scope and label first and then discuss IP addressing and broadcast calculation. The possible values for scope are outlined in the following table.</p>
<!-- /wp:paragraph -->

<!-- wp:table -->
<figure class="wp-block-table"><table><tbody><tr><td><strong>Scope</strong></td><td><strong>Description</strong></td></tr><tr><td>global</td><td>valid everywhere</td></tr><tr><td>site</td><td>valid only within this site (IPv6)</td></tr><tr><td>link</td><td>valid only on this device</td></tr><tr><td>host</td><td>valid only inside this host (machine)</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:paragraph -->
<p>Scope is normally determined by the&nbsp;<strong>ip</strong>&nbsp;utility without explicit use on the command line. For example, an IP address in the 127.0.0.0/8 range falls in the range of localhost IPs, so should not be routed out any device. This explains the presence of the&nbsp;<strong>host</strong>&nbsp;scope for addresses bound to interface&nbsp;<strong>lo</strong>. Usually, addresses on other interfaces are public interfaces, which means that their scope will be global.&nbsp;</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Detailed Explanation</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Interface flags are listed in the angle brackets. Check the flags <a href="http://linux-ip.net/html/tools-ifconfig.html#tb-tools-ifconfig-flags">here</a> and <a href="http://man7.org/linux/man-pages/man7/netdevice.7.html">here</a>.</p>
<!-- /wp:paragraph -->

<!-- wp:group -->
<div class="wp-block-group"><div class="wp-block-group__inner-container"><!-- wp:list -->
<ul><li>UP </li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>The interface is turned on. It is ready to accept packets for transmission and it may inject into the kernel packets received from other nodes on the network. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>LOOPBACK</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>The interface does not communicate with other hosts. All packets sent through it will be returned and nothing but bounced packets can be received. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>BROADCAST</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>The interface has the facility to send packets to all hosts sharing the same link. A typical example is an Ethernet link. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>POINTOPOINT</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>The link has only two ends with one node attached to each end. All packets sent to this link will reach the peer and all packets received by us came from this single peer. If neither LOOPBACK nor BROADCAST nor POINTOPOINT are set, the interface is assumed to be NMBA (Non-Broadcast Multi-Access). This is the most generic type of device and the most complicated one, because the host attached to a NBMA link has no means to send to anyone without additionally configured information. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>MULTICAST</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It is an advisory flag indicating that the interface is aware of multi- casting i.e. sending packets to some subset of neighboring nodes. Broadcasting is a particular case of multi-casting, where the multicast group consists of all nodes on the link. It is important to emphasize that software must not interpret the absence of this flag as the inability to use multi-casting on this interface. Any POINTOPOINT and BROADCAST link is multi-casting by definition, because we have direct access to all the neighbors and, hence, to any part of them. Certainly, the use of high bandwidth multicast transfers is not recommended on broadcast-only links because of high expense, but it is not strictly prohibited. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>PROMISC</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>The interface listens to and feeds to the kernel all traffic on the link even if it is not destined for us, not broadcasted and not destined for a multicast group of which we are member. Usually this mode exists only on broadcast links and is used by bridges and for network monitoring. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>ALLMULTI</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>The interface receives all multicast packets wandering on the link. This mode is used by multicast routers. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>NOARP</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>This flag is different from the other ones. It has no invariant value and its interpretation depends on the network protocols involved. As a rule, it indicates that the device needs no address resolution and that the software or hardware knows how to deliver packets without any help from the protocol stacks. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>DYNAMIC</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p> It is an advisory flag indicating that the interface is dynamically created and destroyed. </p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>SLAVE</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>This interface is bonded to some other interfaces to share link capacities.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>LOWER_UP</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Driver signals L1 up (since Linux 2.6.17) . LOWER_UP is a physical layer link flag (the layer below the network layer, where IP is generally located). LOWER_UP indicates that an Ethernet cable was plugged in and that the device is connected to the network. LOWER_UP differs from UP, which additionally requires the network interface to be enabled.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>NB.</strong> There are other flags but they are either obsolete (NOTRAILERS) or not implemented (DEBUG) or specific to some devices (MASTER, AUTOMEDIA and PORTSEL). We do not discuss them here. </p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:group -->

<!-- wp:paragraph -->
<p>Here we take the interface 2 in our example for clarification.</p>
<!-- /wp:paragraph -->

<!-- wp:group -->
<div class="wp-block-group"><div class="wp-block-group__inner-container"><!-- wp:list -->
<ul><li><em>enp6s0f1</em>&nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It is the interface name. It can be any string.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code>mtu 1500</code>&nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>it sets <strong>m</strong>aximum <strong>t</strong>ransmission <strong>u</strong>nit = 1500 bytes, this is the largest size that a frame sent over this interface can be. This number is usually limited by the Ethernet protocol's cap of 1500. If you send a larger packet and it arrives at an Ethernet interface, then the frame will get fragmented and its payload transmitted in 2 or more packets. Not really any benefit to that, so it's best to follow standards.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code>qdisc <a href="http://man7.org/linux/man-pages/man8/tc-fq_codel.8.html">fq_codel</a></code> &nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It sets queuing discipline = combines Fair Queuing with the CoDel AQM scheme, this determines how an interface chooses which packet to transmit next, when it's being overloaded. Particularly, <em>noqueue</em> means that this interface does not queue anything and <em>loop</em> means that the interface s in the black-hole mode, i.e.  all packets sent to it are immediately discarded.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code>group default</code>&nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Interface groups give a single interface to clients by combining the capabilities of the aggregated interfaces on them.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code>qlen 1000</code>&nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It sets transmission <strong>q</strong>ueue<strong> len</strong>gth = 1000 packets. The 1000th packet will be queued, the 1001st will be dropped.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code>link/ether</code>&nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It means the link layer protocol is&nbsp;<code>Ethernet</code>, the content afterwards is <strong>MAC address</strong>. The laptop doesn't have a MAC address. The network card has a MAC address. So if you have a wireless card and an Ethernet card, you'll have two MAC addresses.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code>brd</code>&nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It means broadcast. This is the address that the device will set as&nbsp;<code>destination</code>&nbsp;when it sends a broadcast. An interface sees all traffic on the wire it's sitting on, but is polite enough to only read data addressed to it. The way you address an interface is by using it's specific address, or the broadcast address.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code>inet</code>&nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It means the network layer protocol is <code>internet</code> (<code>ipv4</code>). <strong>inet6</strong> meas network layer protocol is <code>internet</code> (<code>ipv</code>6). The number directly after the inet address is the number of 1s in its subnet mask.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>valid_lft/preferred_lft&nbsp;</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It stands for lifetime. If you get this address through&nbsp;<code>DHCP</code>, then you'll have a valid lifetime for your lease on the IP address. And just to make hand-offs a little bit easier, a (probably) shorter&nbsp;preferred&nbsp;lifetime is set.</p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:group -->

<!-- wp:shortcode -->
[thumbs-rating-buttons]
<!-- /wp:shortcode -->
