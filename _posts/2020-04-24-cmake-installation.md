---
title: Installation in CmakeList.txt
published: true
date: 2020-04-24 17:52
author: zgxsin
comments: true
categories: [Miscellaneous]
---
<!-- wp:heading -->
<h2>Installation</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Executables</h3>
<!-- /wp:heading -->

<!-- wp:heading -->
<h2>Installing</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>ROS <strong>executables</strong> are installed in a <strong>per-package directory</strong>, not the distributions’s global&nbsp;<code>bin/</code>&nbsp;directory. There, they are accessible to&nbsp;<a href="http://wiki.ros.org/rosrun">rosrun</a>&nbsp;and&nbsp;<a href="http://wiki.ros.org/roslaunch">roslaunch</a>, without cluttering up the shell’s&nbsp;<code>$PATH</code>, and their names only need to <strong>be unique within each package</strong>. There are only a few core ROS commands like&nbsp;<code>rosrun</code>&nbsp;and&nbsp;<code>roslaunch</code>&nbsp;that install in the global&nbsp;<code>bin/</code>&nbsp;directory.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>List all your <strong>executables</strong> as TARGETS on an install command like this:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">install(TARGETS your_node
        RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">MESSAGE("CATKIN_PACKAGE_BIN_DESTINATION: " ${CATKIN_PACKAGE_BIN_DESTINATION})</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">CATKIN_PACKAGE_BIN_DESTINATION: lib/beginner_tutorials</pre>
<!-- /wp:syntaxhighlighter/code -->
