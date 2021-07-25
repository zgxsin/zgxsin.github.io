---
title: Sudo in Ubuntu
published: true
date: 2020-04-05 13:35
author: zgxsin
comments: true
categories: [Linux and Ubuntu, Technical]
---
<!-- wp:heading -->
<h2>List sudoers </h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>To check all the sudo users in current system, you need to run</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash","highlightLines":"32"} -->
<pre class="wp-block-syntaxhighlighter-code"># This command will print all the users listed in the sudo group in /etc/group
# sudo:x:27:guzhou means that user guzhou belongs to sudo group.
guzhou@guzhou-ThinkPad-P53:~$ getent group sudo
sudo:x:27:guzhou

# Only list sudo users in your system.
guzhou@guzhou-ThinkPad-P53:~$ getent group sudo | cut -d: -f4
guzhou

# Check the sudo group.
guzhou@guzhou-ThinkPad-P53:~$ cat /etc/group
root:x:0:
daemon:x:1:
bin:x:2:
sys:x:3:
adm:x:4:syslog,guzhou
tty:x:5:
disk:x:6:
lp:x:7:
mail:x:8:
news:x:9:
uucp:x:10:
man:x:12:
proxy:x:13:
kmem:x:15:
dialout:x:20:
fax:x:21:
voice:x:22:
cdrom:x:24:guzhou
floppy:x:25:
tape:x:26:
sudo:x:27:guzhou
audio:x:29:pulse
dip:x:30:guzhou
www-data:x:33:
backup:x:34:
operator:x:37:
list:x:38:
irc:x:39:
src:x:40:
gnats:x:41:
shadow:x:42:
utmp:x:43:
video:x:44:
sasl:x:45:
plugdev:x:46:guzhou
staff:x:50:
games:x:60:
users:x:100:
nogroup:x:65534:
systemd-journal:x:101:
systemd-network:x:102:
systemd-resolve:x:103:
input:x:104:
crontab:x:105:
syslog:x:106:
messagebus:x:107:
netdev:x:108:
mlocate:x:109:
ssl-cert:x:110:
uuidd:x:111:
avahi-autoipd:x:112:
bluetooth:x:113:
rtkit:x:114:
ssh:x:115:
lpadmin:x:116:guzhou
whoopsie:x:117:
scanner:x:118:saned
saned:x:119:
pulse:x:120:
pulse-access:x:121:
avahi:x:122:
colord:x:123:
geoclue:x:124:
gdm:x:125:
guzhou:x:1000:
sambashare:x:126:guzhou
nvidia-persistenced:x:127:
nm-openvpn:x:128:
rdma:x:129:
docker:x:130:guzhou
_chrony:x:131:
vboxusers:x:132:
</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading -->
<h2>Command "su" and "sudo"</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>su</strong>&nbsp;is the Linux command to substitute (change) user. In Ubuntu, we cannot change to root account using su command since there is no password set for  root account. In a word, the root account is blocked. However, we can use "sudo su" to switch to root.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">guzhou@guzhou-ThinkPad-P53:~$ sudo su
[sudo] password for guzhou: 
# Now you are in root account as you can see "#".
# Switch from root to user guzhou.
root@guzhou-ThinkPad-P53:/home/guzhou# su - guzhou
guzhou@guzhou-ThinkPad-P53:~$ sudo su

# You can also switch back using "exit"
root@guzhou-ThinkPad-P53:/home/guzhou# exit
exit
guzhou@guzhou-ThinkPad-P53:~$ 
</pre>
<!-- /wp:syntaxhighlighter/code -->
