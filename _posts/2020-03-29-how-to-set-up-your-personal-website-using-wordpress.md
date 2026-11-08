---
title: How To Set Up Your Personal Website Using WordPress
published: true
date: 2020-03-29 11:35
author: "Guoxiang (Shawn) Zhou"
comments: true
categories: [Technical]
---

<!-- wp:paragraph -->
<p>In this blog, I will talk about how to set up your personal website using <a href="https://wordpress.org/">WordPress</a> step-by-step. It is oriented for those who just start building their personal website.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>What You Need to Build Your Personal Website</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul><li>A Domain Name</li><li>A Web Hosting Server</li><li>A Personal Laptop</li><li>Internet Access</li><li>A Little Money and Patience</li></ul>
<!-- /wp:list -->

<!-- wp:heading -->
<h2>Step-by-Step Guide</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Here I will list the detailed steps of setting up your personal website. For me, I am using my laptop with Ubuntu 19.01 to do all the steps listed below.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Get a Domain Name</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>For those who do not understand the domain name, please refer to this link <a href="https://www.wpbeginner.com/beginners-guide/beginners-guide-what-is-a-domain-name-and-how-do-domains-work/">here</a>. However, this is not necessary if you do not want to spend too time on it. You can just go ahead to figure out how to get a domain name. There are several online providers for domain names:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><a rel="noreferrer noopener" href="https://www.wpbeginner.com/refer/godaddy/" target="_blank">GoDaddy</a></li><li><a href="https://www.alibabacloud.com/domain">Alibaba Cloud</a></li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>One thing to notice that is you might also get a free domain name when you buy the online web hosting service, such <a href="https://www.bluehost.com/special/wpbeginner?utm_source=%28direct%29&amp;utm_medium=affiliate&amp;utm_campaign=affiliate-link_mbalkhi_Blogger">BlueHost</a>，which has a special offer for <a href="https://wordpress.org/">WordPress</a> users. WordPress is a powerful open source software for building websites, blogs, apps and etc.. I actually use this software to write this post. </p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>I personally choose <a href="https://www.alibabacloud.com/domain">Alibaba Cloud</a> to buy a domain name with ''.com" suffix, which is most recognized and popular in my mind. Here is the screenshot from their website. </p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":442,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/03/image-10-1024x576.png -->
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>You just need to search your personal domain name with your chosen suffix such as ".com" and ".site" in your mind and choose one from the search result and finally pay for it. And now you have your domain name already. Regarding the price, I just payed $7.9 for a ".com" domain name for one year!</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Get a Web Hosting Server Service</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The next thing to do is to obtain a server where you can store the data of your websites and keep your website live for the most of time.  Any laptop can literally act as a server. However, it is recommended to use the product from specialized hosting providers since they are more stable and oriented for this purpose. You can choose <a href="https://www.bluehost.com/?utm_source=google&amp;utm_medium=brandsearch&amp;kclickid=adc91240-4bc4-442c-810e-63372ca190f0&amp;kenshoo_ida=Blue%20Host%20IDA&amp;gclid=Cj0KCQjwjoH0BRD6ARIsAEWO9DsaC5jQU09y28zAnkACApC0MtzFl6svXKVQ-djS7AzBJX9X7VfNQosaAvZqEALw_wcB&amp;utm_campaign=affiliate-link_searchbrandpromo_PPC">BlueHost</a> to get both domain name and web hosting server service. I  stick with Alibaba Cloud and choose their Elastic Computing Service (ECS).  As a new user of their service, I have free trial period for 12 months. I install clean Ubuntu 18.04 LTS for my server, which can be easily done using their console platform.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Deploy LAMP and WordPress</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>In previous step, we have both domain name and our web hosting server. To set up a personal website, we can install a software bundle called <a href="https://en.wikipedia.org/wiki/LAMP_(software_bundle)">LAMP</a> (<strong>L</strong>inux,&nbsp;<strong>A</strong>pache,&nbsp;<strong>M</strong>ySQL,&nbsp;<strong>P</strong>HP/<strong>P</strong>erl/<strong>P</strong>ython), which is a popular example of web service stack. This can be easily done in Ubuntu systems. I follow this </p>
<!-- /wp:paragraph -->

<!-- wp:embed {"url":"https://www.youtube.com/watch?v=oLsA2kj_bMU\u0026list=PLirg7u3zKHagBFXXcL170jHiAmpxoKBoM\u0026index=2\u0026t=0s","type":"video","providerNameSlug":"youtube","responsive":true,"className":"wp-embed-aspect-16-9 wp-has-aspect-ratio"} -->
<figure class="wp-block-embed is-type-video is-provider-youtube wp-block-embed-youtube wp-embed-aspect-16-9 wp-has-aspect-ratio"><div class="wp-block-embed__wrapper">
https://www.youtube.com/watch?v=oLsA2kj_bMU&amp;list=PLirg7u3zKHagBFXXcL170jHiAmpxoKBoM&amp;index=2&amp;t=0s
</div></figure>
<!-- /wp:embed -->

<!-- wp:paragraph -->
<p>to install LAMP as well as WordPress for my server. It works like a charm! Here I briefly sum the steps to be done in the server side:</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code># ==================================================
# Install required tools 
# ==================================================
# Update software cache
sudo apt update 

# Upgrade software
sudo apt upgrade

# Install zip
sudo apt install zip

# Install common software
sudo apt install software-properties-common

# ==================================================
# Install LAMP stack
# ==================================================
sudo apt-get install lamp-server^

# MYSQL database intilialization
mysql -u root -p
# Run the following commands sequentially
# Here "wordpressuser" is the user name and "wordpresspassword" is the password.
CREATE DATABASE wordpressdb;
CREATE USER wordpressuser@localhost IDENTIFIED BY 'wordpresspassword';
GRANT ALL PRIVILEGES ON wordpressdb.* TO wordpressuser@localhost;
FLUSH PRIVILEGES;
exit

# ==================================================
# Install WordPress
# ==================================================
cd /tmp
wget https://wordpress.org/latest.zip
unzip -q latest.zip -d /var/www/html/
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html
mkdir -p /var/www/html/wp-content/uploads
chown -R www-data:www-data /var/www/html/wp-content/uploads

# Finally, open https://your_server_ip/wordpress in your local laptop and set up and install WordPress.</code></pre>
<!-- /wp:code -->

<!-- wp:heading {"level":3} -->
<h3>Domain Name Resolution</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Now if you type <em>your_domain_name/wordpress</em> (<em>your_domain_name</em> also includes the suffix such as .com) in your web browser,  unfortunately you will  see nothing meaningful, because your domain name is not understood by the internet service provider (ISP). That's why we need Domain Name Resolution to set up a correspondence between your domain name and your server's IP address. When you buy a domain name, you will be usually shown how to set up Domain Name Resolution for that.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>In my case,  I follow this <a href="https://www.alibabacloud.com/help/doc-detail/39903.htm">guide</a> to resolve my domain name. It is very easy to do!</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Browse Your Personal Website</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>It is almost done. After you finish the domain name resolution, you need to wait for around 10 minutes for the DNS server to recognize your domain name. Please also make sure the ports 80 and 433 of your server is open as 80 and 443 were chosen as the default HTTP and HTTPS ports. Then you type <em>your_domain_name/wordpress</em> in your web browser, you should see the default WordPress software homepage. Usually we should direct type <em>your_domain_name</em> to get this homepage. </p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>To configure this, you first need to change the settings in WordPress. In your homepage, go to the WordPress Dashboard and find <strong>Settings-&gt;General Settings</strong>. You will find two entries called <strong>WordPress Address (URL)</strong> and <strong>Site Address (URL),</strong> please change them like the following image. </p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":409,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/03/image-4.png -->
<!-- /wp:image -->

<!-- wp:paragraph -->
<p><strong>Remember to replace your actual domain name with <em>your_domain_name</em></strong>.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Next, you need to run</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code># Copy the index.php from wordpress folder to /var/www/html
cp wordpress/index.php .

cp wordpress/.htacccess .</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>inside the folder <strong><em>/var/www/html</em></strong> of your server.  And you need to do some modifications in <em><strong>index.php </strong></em>in <strong><em>/var/www/html </em></strong>at your server. Open <em><strong>index.php</strong></em> and  find this line</p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":412,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/03/image-7.png -->
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>and replace it with </p>
<!-- /wp:paragraph -->

<!-- wp:image {"id":410,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/03/image-5.png -->
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>Last step is that you need to configure <a href="https://httpd.apache.org/">Apache</a> to  load <em><strong>index.php </strong></em>instead of <strong><em>index.html</em></strong>. Please check this <a href="https://www.phusionpassenger.com/library/install/apache/working_with_the_apache_config_file.html">link</a> to see where your Apache configuration file is located. In my case, it is located in <strong><em>/etc/apache2/apache2.conf</em></strong>. What you need to do is to edit this file and find this block inside the file</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>&lt;Directory /var/www/&gt;
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
&lt;/Directory&gt;
</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>and change it to </p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>&lt;Directory /var/www/&gt;
        Options Indexes FollowSymLinks
        DirectoryIndex index.php
        AllowOverride ALL
        Require all granted
&lt;/Directory&gt;
</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>Finally you need to restart apache by running</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>sudo service apache2 restart</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>Now you should visit your website by directly typing <em>your_domain_name</em> in your web browser.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Add SSL Certificate for Your Domain Name</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>At previous step, you can normally visit your website by <em>your_domain_name</em> in your browser. But your website will be marked insecure since no SSL certificate is installed for your domain name.  Please check this <a href="https://www.wpbeginner.com/wp-tutorials/how-to-add-ssl-and-https-in-wordpress/">link</a> to understand SSL certificate based on your need. You can google online for a free certificate or buy one with a  cheap price. I bought one from<a href="https://world.taobao.com/"> Taobao.com</a>. <br>Here I list the steps I did to obtain and install SSL certificate for my domain name. Notice these steps might not apply to your case exactly.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>Go to Taobao.com and place an order for SSL certificate for a single domain name</li><li>You will be asked to provide your domain name for registration and email address for communication</li><li>You will be asked to add a TXT record in your DNS setting for your domain name at Alibaba Cloud with the provided entry values. Check the image below.</li></ul>
<!-- /wp:list -->

<!-- wp:image {"id":413,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/03/image-8.png -->
<!-- /wp:image -->

<!-- wp:list -->
<ul><li>Yo will receive your SSL certificate with the following structure</li></ul>
<!-- /wp:list -->

<!-- wp:image {"id":415,"width":597,"height":391,"sizeSlug":"large"} -->
<!-- Image lost in the WordPress migration: uploads/2020/03/image-9.png -->
<!-- /wp:image -->

<!-- wp:list -->
<ul><li>Follow this <a href="https://www.alibabacloud.com/help/doc-detail/102450.html?spm=a2c5t.10695662.1996646101.searchclickresult.617a4909bm1IkH">link</a> to install SSL certificate</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Since we are using Apache web server, you just need the contents in <em>apache</em> folder of your SSL certificate. Please contact your SSL certificate provider for one-to-one correspondence between the files in <em>apache</em> folder and the file names inside the above mentioned <a href="https://www.alibabacloud.com/help/doc-detail/102450.html?spm=a2c5t.10695662.1996646101.searchclickresult.617a4909bm1IkH">link</a>.  With all the above steps done, you should now visit your website without pain.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Migrate Your WordPress Website to a new Host</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If you want to move your WordPress website to a new host. Please follow this <a href="https://www.wpbeginner.com/wp-tutorials/how-to-move-wordpress-to-a-new-host-or-server-with-no-downtime/" data-type="URL" data-id="https://www.wpbeginner.com/wp-tutorials/how-to-move-wordpress-to-a-new-host-or-server-with-no-downtime/">guide</a>. After migration, if you cannot open your previous pages in the new host, please change the permanent link to plain type and try again.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Known Issues</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Q: Can not save/update your post or pages in the default editor.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>A: Try to log out WordPress and then log in again.</p>
<!-- /wp:paragraph -->

<!-- wp:shortcode -->

[thumbs-rating-buttons]

<!-- /wp:shortcode -->
