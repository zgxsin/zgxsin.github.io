---
title: Understand Python Environment in Ubuntu 18.04
published: true
date: 2020-04-04 17:44
author: "Guoxiang (Shawn) Zhou"
comments: true
categories: [Miscellaneous]
---

<!-- wp:paragraph -->
<p>Many people might be confused about python environments in Ubuntu. I will give a short introduction about python environments on Ubuntu 18.04.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Check Which Python You Are Using in Terminal</h2>
<!-- /wp:heading -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">$ which python
/usr/bin/python

$ which python3
/usr/bin/python3

# Now you know that your python executables are located in /usr/bin.
$ cd /usr/bin

# Type "ls python" + [tab] to list python related files
$ ls python [tab]
python             python2.7          python2-config     python3            python3.6-config   python3.6m-config  python3m           python-config      pythontex3
python2            python2.7-config   python2-qr         python3.6          python3.6m         python3-config     python3m-config    pythontex 

$ ls python -l
lrwxrwxrwx 1 root root 9 Apr 16  2018 python -> python2.7

$ ls python2 -l
lrwxrwxrwx 1 root root 9 Apr 16  2018 python2 -> python2.7

$ ls python3 -l
lrwxrwxrwx 1 root root 9 Apr  1 16:12 python3 -> python3.6
</pre>
<!-- /wp:syntaxhighlighter/code -->

<p>Form the image above, you can see that i am using python2.7 since /usr/bin/python is symbolically linked to /usr/bin/python2.7. To verify this, you can type python in your terminal :</p>

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">$ python
Python 2.7.17 (default, Nov  7 2019, 10:07:09) 
[GCC 7.4.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> 

$ python3
Python 3.6.9 (default, Nov  7 2019, 10:44:02) 
[GCC 8.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> </pre>
<!-- /wp:syntaxhighlighter/code -->

<p>You can use different python versions to run your file:</p>

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">$ python filename.py

$ python3 filename.py</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading -->
<h2>Manage Python Environment</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Here I will talk about the tool <strong>virtualenv</strong>. You need to install it first</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">~$ sudo pip install virtualenv

# Verify installation
~$ virtualenv --version
virtualenv 20.0.16 from /usr/local/lib/python2.7/dist-packages/virtualenv/__init__.pyc

~$ mkdir tmp 
~$ cd tmp
~/tmp$ virtualenv venv
~/tmp$ ls
venv

# Activate the python env.
~/tmp$ source venv/bin/activate

~/tmp$ which python
/home/guzhou-test/tmp/venv/bin/python

# You can install packages using pip inside this env.
~/tmp$ pip install matplotlib
....

# Check the installed package location. 
~/tmp$ pip show matplotlib
DEPRECATION: Python 2.7 reached the end of its life on January 1st, 2020. Please upgrade your Python as Python 2.7 is no longer maintained. A future version of pip will drop support for Python 2.7. More details about Python 2 support in pip, can be found at https://pip.pypa.io/en/latest/development/release-process/#python-2-support
Name: matplotlib
Version: 2.2.5
Summary: Python plotting package
Home-page: https://matplotlib.org
Author: John D. Hunter, Michael Droettboom
Author-email: matplotlib-users@python.org
License: PSF
Location: /home/guzhou-test/tmp/venv/lib/python2.7/site-packages
Requires: python-dateutil, kiwisolver, numpy, six, cycler, pyparsing, pytz, backports.functools-lru-cache, subprocess32
Required-by: 


# Deactive current python env and go back to system default python version.
~/tmp$ deactivate 
~/tmp$ which python
/usr/bin/python

</pre>
<!-- /wp:syntaxhighlighter/code -->

<p><a class="reference external" href="https://virtualenvwrapper.readthedocs.io/en/latest/index.html">virtualenvwrapper</a> provides a set of commands which makes working with virtual environments much more pleasant. It also places all your virtual environments in one place. To install it, run:</p>

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code"># Now you are in system default python env.
~/tmp$ sudo pip install virtualenvwrapper
# You can add the two lines below to your ~/.bashrc.
# You can also do: export WORKON_HOME=$HOME/.virtualenvs to make it hidden.
~/tmp$ export WORKON_HOME=$HOME/Envs
~/tmp$ source /usr/local/bin/virtualenvwrapper.sh</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>Now you can start using virtualenvwrapper. Here is a <a href="https://gist.github.com/bbengfort/246bc820e76b48f71df7">cheatsheet</a> for virtualenvwrapper.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code"># Create an env and you will be automatically switched on that env.
guzhou-test@guzhoutest-VirtualBox:~$ mkvirtualenv venv
created virtual environment CPython2.7.17.final.0-64 in 138ms
  creator CPython2Posix(dest=/home/guzhou-test/Envs/venv, clear=False, global=False)
  seeder FromAppData(download=False, pip=latest, setuptools=latest, wheel=latest, via=copy, app_data_dir=/home/guzhou-test/.local/share/virtualenv/seed-app-data/v1.0.1)
  activators PythonActivator,CShellActivator,FishActivator,PowerShellActivator,BashActivator
(venv) guzhou-test@guzhoutest-VirtualBox:~$ cd Envs/
(venv) guzhou-test@guzhoutest-VirtualBox:~/Envs$ ls
get_env_details  postdeactivate    postrmvirtualenv  premkproject     venv
initialize       postmkproject     preactivate       premkvirtualenv
postactivate     postmkvirtualenv  predeactivate     prermvirtualenv

# You can also explicitly specify that you want to work on this env.
(venv) guzhou-test@guzhoutest-VirtualBox:~/Envs$ workon venv

# Deactivate env.
(venv) guzhou-test@guzhoutest-VirtualBox:~/Envs$ deactivate 
guzhou-test@guzhoutest-VirtualBox:~/Envs$ 

# Rm env
guzhou-test@guzhoutest-VirtualBox:~/Envs$ rmvirtualenv venv
Removing venv...
guzhou-test@guzhoutest-VirtualBox:~/Envs$ workon venv
ERROR: Environment 'venv' does not exist. Create it with 'mkvirtualenv venv'.
guzhou-test@guzhoutest-VirtualBox:~/Envs$ 
</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading -->
<h2>References</h2>
<!-- /wp:heading -->

<!-- wp:list {"ordered":true} -->
<ol><li><a href="https://docs.python-guide.org/dev/virtualenvs/">https://docs.python-guide.org/dev/virtualenvs/</a></li></ol>
<!-- /wp:list -->
