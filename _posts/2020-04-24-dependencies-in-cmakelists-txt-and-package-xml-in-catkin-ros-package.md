---
title: Dependencies in CMakeLists.txt and package.xml in Catkin ROS Package
published: true
date: 2020-04-24 18:50
author: zgxsin
comments: true
categories: [C++, cakin, Robotics, ros]
---

<!-- wp:heading -->
<h2>Create a Catkin ROS Package</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Follow this <a href="https://wiki.ros.org/ROS/Tutorials/CreatingPackage">tutorial</a> to create a sample catkin ROS package. The simple command syntax to create a catkin ROS package is</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">catkin_create_pkg &lt;package_name> [depend1] [depend2] [depend3]</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>After creating and initializing the catkin workspace,  go to <em>your_catkin_workspace/src</em> and create a package <em>beginner_tutorials</em>:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code">guzhou@guzhou-laptop:~/catkin_ws/src$ catkin_create_pkg beginner_tutorials std_msgs rospy roscpp
Created file beginner_tutorials/package.xml
Created file beginner_tutorials/CMakeLists.txt
Created folder beginner_tutorials/include/beginner_tutorials
Created folder beginner_tutorials/src
Successfully created files in /home/guzhou/catkin_ws/src/beginner_tutorials. Please adjust the values in package.xml.
</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>A lot of files are created.  The file structure of the created ROS package is as follows:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">guzhou@guzhou-laptop:~/catkin_ws/src$ tree
.
└── beginner_tutorials
    ├── CMakeLists.txt
    ├── include
    │   └── beginner_tutorials
    ├── package.xml
    └── src

4 directories, 2 files
</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>Here two files <strong>CMakeLists.txt</strong> and <strong>package.xml</strong> are created. The contents inside these two files are full of comments and instructions which tell you how to fill in these two files. To have a clear view of the contents in these two files, I remove all the comments and paste the default generated contents here:</p>
<!-- /wp:paragraph -->

<!-- wp:columns -->
<div class="wp-block-columns"><!-- wp:column -->
<div class="wp-block-column"><!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">cmake_minimum_required(VERSION 2.8.3)
project(beginner_tutorials)

find_package(catkin REQUIRED COMPONENTS
roscpp
rospy
std_msgs
)

catkin_package(

# INCLUDE_DIRS include

# LIBRARIES beginner_tutorials

# CATKIN_DEPENDS roscpp rospy std_msgs

# DEPENDS system_lib

)

include_directories(

# include

${catkin_INCLUDE_DIRS}
)</pre>

<!-- /wp:syntaxhighlighter/code --></div>
<!-- /wp:column -->

<!-- wp:column -->
<div class="wp-block-column"><!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;?xml version="1.0"?>
&lt;package format="2">
  &lt;name>beginner_tutorials&lt;/name>
  &lt;version>0.0.0&lt;/version>
  &lt;description>The beginner_tutorials package&lt;/description>

&lt;maintainer email="guzhou@todo.todo">guzhou&lt;/maintainer>

&lt;license>TODO&lt;/license>

&lt;buildtool_depend>catkin&lt;/buildtool_depend>
&lt;build_depend>roscpp&lt;/build_depend>
&lt;build_depend>rospy&lt;/build_depend>
&lt;build_depend>std_msgs&lt;/build_depend>
&lt;build_export_depend>roscpp&lt;/build_export_depend>
&lt;build_export_depend>rospy&lt;/build_export_depend>
&lt;build_export_depend>std_msgs&lt;/build_export_depend>
&lt;exec_depend>roscpp&lt;/exec_depend>
&lt;exec_depend>rospy&lt;/exec_depend>
&lt;exec_depend>std_msgs&lt;/exec_depend>

&lt;!-- The export tag contains other, unspecified, tags -->
&lt;export>
&lt;!-- Other tools can request additional information be placed here -->

&lt;/export>
&lt;/package></pre>

<!-- /wp:syntaxhighlighter/code --></div>
<!-- /wp:column --></div>
<!-- /wp:columns -->

<!-- wp:paragraph -->
<p>Catkin&nbsp;<code>CMakeLists.txt</code>&nbsp;files mostly contain <strong>ordinary CMake commands</strong>, plus a few catkin-specific ones.&nbsp; </p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The package dependencies are declared in&nbsp;<code>package.xml</code>. If they are missing or incorrect, <strong>you may be able to build from source and run tests in your own workspace, but your package will not work correctly when released to the ROS community.</strong> Others rely on this information to install the software they need for using your package. Your package must contain an XML file named<strong>&nbsp;package.xml</strong>, as specified by&nbsp;<a href="https://ros.org/reps/rep-0140.html">REP-0140</a>. These components are all required:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"xml"} -->
<pre class="wp-block-syntaxhighlighter-code">&lt;package format="2">
  &lt;name>your_package&lt;/name>
  &lt;version>0.0.0&lt;/version>
  &lt;description>
    your description about this package.
  &lt;/description>
  &lt;maintainer email="you@example.com">Your Name&lt;/maintainer>
  &lt;license>TODO&lt;/license>
  &lt;buildtool_depend>catkin&lt;/buildtool_depend>
&lt;/package></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading -->
<h2>Packages, Libraries and Executables</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The essential concepts in Catkin ROS packages include <strong>packages, libraries and executables</strong>. The package can contain several libraries and executables as well as <strong>headers</strong> (C++ .h or .hpp file).  Both libraries and executables are called <strong>targets</strong>. The main difference between an executable and a library is that an <strong>executable has a fixed starting point</strong>. <strong>A library can have multiple entry points, and there is no single point defined as the starting point</strong>. An executable could contain any code that could exist in a library. A library could contain any code that exists in an executable, except for the starting point. <strong>Separating libraries from executables allows programmers to compartmentalize functionality</strong>.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Header-only Libraries</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>A header-only library, as the name hints, is only made of headers. That actually means you don't have to link against binaries, because the whole code of this library is contained in headers, and <strong>this code will be compiled when you include them in your project</strong>.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>This kind of libraries is sometimes the most convenient portable solution, for example when dealing with <strong>templates</strong>. Please check <a href="https://stackoverflow.com/questions/495021/why-can-templates-only-be-implemented-in-the-header-file">here</a> and <a href="https://stackoverflow.com/questions/44774036/why-use-a-tpp-file-when-implementing-templated-functions-and-classes-defined-i">here</a> for the reasoning behind. </p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>C++ Catkin Library Dependencies</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>Catkin libraries</strong> are provided by <strong>ROS packages</strong> whether you install them from Ubuntu packages or build from source. When your package depends on a catkin C++ library, there are usually several kinds of dependencies which must be declared in your&nbsp;<code>package.xml</code>&nbsp;and&nbsp;<code>CMakeLists.txt</code>&nbsp;files.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>package.xml</h3>
<!-- /wp:heading -->

<!-- wp:heading {"level":4} -->
<h4><code>&lt;depend&gt;</code></h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>It is generally sufficient to mention each <strong>ROS package dependency</strong> once, like this:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"xml"} -->
<pre class="wp-block-syntaxhighlighter-code">&lt;depend>roscpp&lt;/depend> </pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>Sometimes, you may need or want more granularity for certain dependencies. The following sections explain how to do that. <strong>If in doubt, use the&nbsp;<code>&lt;depend&gt;</code>&nbsp;tag, it’s simpler.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4><code>&lt;build_depend&gt;</code></h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>If you only use some particular dependency for building your package, and not at execution time</strong>, you can use the&nbsp;<code>&lt;build_depend&gt;</code>&nbsp;tag. For example, the ROS angles package<strong> only provides C++ headers and CMake configuration files</strong>:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"xml"} -->
<pre class="wp-block-syntaxhighlighter-code">&lt;build_depend>angles&lt;/build_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>With this type of dependency, <strong>an installed binary of your package does not require the angles package to be installed</strong>. But, that could create a problem if your package <strong>exports</strong> a header that includes the&nbsp;<code>&lt;angles/angles.h&gt;</code>&nbsp;header. In that case you also need a&nbsp;<code>&lt;build_export_depend&gt;</code>.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4><code>&lt;build_export_depend&gt;</code></h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If you export a <strong>header</strong> that includes&nbsp;<code>&lt;angles/angles.h&gt;</code>, it will be needed by other packages that&nbsp;<code>&lt;build_depend&gt;</code>&nbsp;on yours:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"xml"} -->
<pre class="wp-block-syntaxhighlighter-code">&lt;build_export_depend>angles&lt;/build_export_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p><strong>This mainly applies to headers and CMake configuration files</strong>. <strong>Library packages referenced by libraries you export should normally specify&nbsp;<code>&lt;depend&gt;</code>, because they are also needed at execution time.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4><code>&lt;exec_depend&gt;</code></h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This tag declares dependencies for <strong>shared (dynamic) libraries, executables, Python modules, launch scripts and other files required when running your package</strong>. For example, the ROS openni_launch package provides launch scripts, which are only needed at execution time:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"xml"} -->
<pre class="wp-block-syntaxhighlighter-code">&lt;exec_depend>openni_launch&lt;/exec_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading {"level":3} -->
<h3>CMakeLists.txt</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>CMake <strong>does not know</strong> about&nbsp;<code>package.xml</code>&nbsp;dependencies, although catkin does. <strong>For your code to compile, the&nbsp;<code>CMakeLists.txt</code>&nbsp;must explicitly declare how to resolve all of your header and library references.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4>Finding the library</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>First, CMake needs to find the library. For catkin dependencies (catkin ROS package), this is easy:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code"># roscpp is a catkin ros package.
find_package(catkin REQUIRED COMPONENTS roscpp)</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>This&nbsp;<code>find_package()</code>&nbsp;call defines CMake variables that will be needed later for the compile and link steps. List all additional catkin dependencies in the same command:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code"># You will have two variables catkin_INCLUDE_DIRS and catkin_LIBRARIES set. catkin_INCLUDE_DIRS is collection of all the headers while catkin_LIBRARIES is a collection of all libraries
find_package(catkin REQUIRED COMPONENTS angles roscpp std_msgs)
﻿</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code"># Quick Test
find_package(catkin REQUIRED COMPONENTS angles roscpp std_msgs)
MESSAGE("catkin_INCLUDE_DIRS: " ${catkin_INCLUDE_DIRS})
MESSAGE("catkin_LIBRARIES: " ${catkin_LIBRARIES})</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>If you load the CMakeList.txt, the output will have two lines like below:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">catkin_INCLUDE_DIRS: /opt/ros/melodic/include/opt/ros/melodic/share/xmlrpcpp/cmake/../../../include/xmlrpcpp/usr/include
catkin_LIBRARIES: /opt/ros/melodic/lib/libroscpp.so/usr/lib/x86_64-linux-gnu/libboost_filesystem.so/opt/ros/melodic/lib/librosconsole.so/opt/ros/melodic/lib/librosconsole_log4cxx.so/opt/ros/melodic/lib/librosconsole_backend_interface.so/usr/lib/x86_64-linux-gnu/liblog4cxx.so/usr/lib/x86_64-linux-gnu/libboost_regex.so/opt/ros/melodic/lib/libxmlrpcpp.so/opt/ros/melodic/lib/libroscpp_serialization.so/opt/ros/melodic/lib/librostime.so/opt/ros/melodic/lib/libcpp_common.so/usr/lib/x86_64-linux-gnu/libboost_system.so/usr/lib/x86_64-linux-gnu/libboost_thread.so/usr/lib/x86_64-linux-gnu/libboost_chrono.so/usr/lib/x86_64-linux-gnu/libboost_date_time.so/usr/lib/x86_64-linux-gnu/libboost_atomic.so/usr/lib/x86_64-linux-gnu/libpthread.so/usr/lib/x86_64-linux-gnu/libconsole_bridge.so.0.4</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p><strong>Make sure all these packages are also mentioned in your&nbsp;<code>package.xml</code>&nbsp;using a&nbsp;<code>&lt;depend&gt;</code>&nbsp;or&nbsp;<code>&lt;build_depend&gt;</code>&nbsp;tag.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4>Include directories</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Note: <code>target_include_directories()</code> is preferred.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Before compiling, collect all the<strong> header paths</strong> you found earlier:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">include_directories(include ${catkin_INCLUDE_DIRS}) </pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>The&nbsp;<code>include</code>&nbsp;parameter is needed only if that sub-directory of your package contains headers used to compile your programs. In our example beginner_tutorials, there is an include folder which is created by default.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4>Exporting interfaces</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>You must declare the library and header <strong>packages</strong> needed by all the interfaces you <strong>export to other </strong>ROS packages:</p>
<!-- /wp:paragraph -->

<!-- wp:preformatted -->
<pre class="wp-block-preformatted"># This only list the catkin ros packages dependencies which are needed when your current catkin package is exported.
catkin_package(CATKIN_DEPENDS angles roscpp std_msgs)
</pre>
<!-- /wp:preformatted -->

<!-- wp:paragraph -->
<p><strong>Make sure all these packages are also mentioned in your&nbsp;<code>package.xml</code>&nbsp;using a&nbsp;<code>&lt;depend&gt;</code>&nbsp;or&nbsp;<code>&lt;build_export_depend&gt;</code>&nbsp;tag.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The&nbsp;<code>catkin_package()</code>&nbsp;command is only called once. It may need additional parameters, depending on what else your package exports.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>C++ System Library Dependencies</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>System libraries are part of your operating system distribution.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>When your package depends on a system C++ library, there are usually several kinds of dependencies which must be declared in your&nbsp;<code>package.xml</code>&nbsp;and&nbsp;<code>CMakeLists.txt</code>&nbsp;files.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>package.xml</h3>
<!-- /wp:heading -->

<!-- wp:heading {"level":4} -->
<h4><code>&lt;build_depend&gt;</code></h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This tag declares packages needed for <strong>building</strong> your programs, including development files like headers, libraries and configuration files. For each build dependency, <strong>specify the corresponding&nbsp;<a href="https://wiki.ros.org/rosdep">rosdep</a>&nbsp;key</strong>. On many <strong>Linux</strong> distributions these are called “<strong>development</strong>” packages, and their names generally end in&nbsp;<code>-dev</code>&nbsp;or&nbsp;<code>-devel</code>, like this:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"xml"} -->
<pre class="wp-block-syntaxhighlighter-code">&lt;build_depend>libgstreamer0.10-dev&lt;/build_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>Some C++ packages, like Eigen, have <strong>no run-time library</strong>, and everything is defined in the header files:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"xml"} -->
<pre class="wp-block-syntaxhighlighter-code">&lt;build_depend>eigen&lt;/build_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading {"level":4} -->
<h4><code>&lt;build_export_depend&gt;</code></h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If your package exports a header that includes an Eigen header like&nbsp;<code>&lt;Eigen/Geometry&gt;</code>, then other packages that&nbsp;<code>&lt;build_depend&gt;</code>&nbsp;on yours will need Eigen, too. To make that work correctly, declare it like this:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;build_export_depend>eigen&lt;/build_export_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>This type of dependency mainly applies to <strong>headers and CMake configuration files</strong>, and it typically names the “<strong>development</strong>” package:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;build_export_depend>libgstreamer0.10-dev&lt;/build_export_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading {"level":4} -->
<h4><code>&lt;exec_depend&gt;</code></h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The&nbsp;<code>&lt;exec_depend&gt;</code>&nbsp;is for shared (dynamic) libraries, executables, Python modules, launch scripts and other files required for running your package. Specify the run-time <strong>rosdep</strong> key, if possible, like this</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">libgstreamermm-1.0-1/bionic 1.10.0+dfsg-1 amd64
  C++ wrapper library for GStreamer (shared libraries)

libgstreamermm-1.0-dev/bionic 1.10.0+dfsg-1 amd64
  C++ wrapper library for GStreamer (development files)
</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;exec_depend>libgstreamer0.10-0&lt;/exec_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading {"level":4} -->
<h4><code>&lt;depend&gt;</code></h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This tag combines all the previous types of dependencies into one.<strong> It is not recommended for system dependencies, because it forces your package’s binary installation to depend on the “development” package</strong>, which is not generally necessary or desirable:</p>
<!-- /wp:paragraph -->

<!-- wp:preformatted -->
<pre class="wp-block-preformatted">&lt;depend&gt;curl&lt;/depend&gt;</pre>
<!-- /wp:preformatted -->

<!-- wp:heading {"level":4} -->
<h4>Development Packages</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>The&nbsp;<code>*-devel</code>&nbsp;packages (usually called&nbsp;<code>*-dev</code>&nbsp;in Debian-based distributions) usually contain all the files necessary to compile code against a given library.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For running an application using the library&nbsp;<code>libfoo</code>,&nbsp;only the actually shared library file (<code>*.so.*</code>, for example&nbsp;<code>libfoo.so.1.0</code>) are needed (plus possibly some data files and some version-specific symlinks).</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>When you actually want to <strong>compile</strong> a C++ application that uses that library, <strong>you'll need the header files</strong> (<code>*.h</code>, for example&nbsp;<code>foo.h</code>) that describe the <strong>interface</strong> of that application as well as a version-less symlink to the shared library (<code>*.so</code>, for example&nbsp;<code>libfoo.so</code>&nbsp;-&gt;&nbsp;<code>libfoo.so.1.0</code>). Those are usually bundled in the&nbsp;<code>*-devel</code>&nbsp;packages.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Sometimes the <code>*-devel</code> packages also include <strong>statically compiled versions of the libraries</strong> (<code>*.a</code>, for example <code>libfoo.a</code>) in case you want to build a complete stand-alone application that doesn't depend on dynamic libraries at all.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Below is an example of different packages for the same application.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code {"language":"bash"} -->
<pre class="wp-block-syntaxhighlighter-code"># libavformat57: FFmpeg library with (de)muxers for multimedia containers - runtime files

guzhou@guzhou-laptop:~$ apt-file list libavformat57
libavformat57: /usr/lib/x86_64-linux-gnu/libavformat.so.57
libavformat57: /usr/lib/x86_64-linux-gnu/libavformat.so.57.83.100
libavformat57: /usr/share/doc/libavformat57/changelog.Debian.gz
libavformat57: /usr/share/doc/libavformat57/copyright
libavformat57: /usr/share/lintian/overrides/libavformat57

guzhou@guzhou-laptop:~$  ls -l /usr/lib/x86_64-linux-gnu/libavformat.so.57.83.100
-rw-r--r-- 1 root root 2459288 Apr 24  2019 /usr/lib/x86_64-linux-gnu/libavformat.so.57.83.100
guzhou@guzhou-laptop:~$  ls -l /usr/lib/x86_64-linux-gnu/libavformat.so.57
lrwxrwxrwx 1 root root 24 Apr 24  2019 /usr/lib/x86_64-linux-gnu/libavformat.so.57 -> libavformat.so.57.83.100


# libavformat-dev: FFmpeg library with (de)muxers for multimedia containers - development files

guzhou@guzhou-laptop:~$ apt-file list libavformat-dev
libavformat-dev: /usr/include/x86_64-linux-gnu/libavformat/avformat.h
libavformat-dev: /usr/include/x86_64-linux-gnu/libavformat/avio.h
libavformat-dev: /usr/include/x86_64-linux-gnu/libavformat/version.h
libavformat-dev: /usr/lib/x86_64-linux-gnu/libavformat.a
libavformat-dev: /usr/lib/x86_64-linux-gnu/libavformat.so
libavformat-dev: /usr/lib/x86_64-linux-gnu/pkgconfig/libavformat.pc
libavformat-dev: /usr/share/doc/libavformat-dev/changelog.Debian.gz
libavformat-dev: /usr/share/doc/libavformat-dev/copyright

guzhou@guzhou-laptop:~$  ls -l /usr/lib/x86_64-linux-gnu/libavformat.so
lrwxrwxrwx 1 root root 24 Apr 24  2019 /usr/lib/x86_64-linux-gnu/libavformat.so -> libavformat.so.57.83.100
</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>Other languages (such as Java, Python, ...) use a <strong>different way</strong> of noting the API of a library (effectively including all the necessary information in the actual library) and thus usually need no separate&nbsp;<code>*-devel</code>&nbsp;packages (except maybe for documentation and additional tools).</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>CMakeLists.txt</h3>
<!-- /wp:heading -->

<!-- wp:heading {"level":4} -->
<h4>Finding the library</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>First, CMake needs to find the library. If you are lucky, someone has already provided a&nbsp;<em>CMake module</em>&nbsp;as was done for boost. Most boost C++ components are fully implemented in the header files. They do not require a separate shared library at run-time:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">find_package(Boost REQUIRED)</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>But, the boost thread implementation&nbsp;<em>does</em>&nbsp;require a library, so specify “COMPONENTS thread” if you need it:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">find_package(Boost REQUIRED COMPONENTS thread)</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>While the CMake community recommends standard names for those variables, some packages may <strong>not</strong> follow their recommendations.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Sometimes, no CMake module is available, but the library’s <strong>development package</strong> provides a&nbsp;<a href="https://www.freedesktop.org/wiki/Software/pkg-config/">pkg-config</a>&nbsp;file. To use that, first load the CMake&nbsp;<code>PkgConfig</code>&nbsp;module, then access the <strong>build flags </strong>provided by the library. You might check the usage of pkg_check_modules <a href="https://cmake.org/cmake/help/latest/module/FindPkgConfig.html">here</a>.</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code"># pkg_check_modules
# Checks for all the given modules, setting a variety of result 
# variables in the calling scope.

pkg_check_modules(&lt;prefix>
                  [REQUIRED] [QUIET]
                  [NO_CMAKE_PATH]
                  [NO_CMAKE_ENVIRONMENT_PATH]
                  [IMPORTED_TARGET [GLOBAL]]
                  &lt;moduleSpec> [&lt;moduleSpec>...])</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">find_package(PkgConfig REQUIRED)
pkg_check_modules (GLIB2 REQUIRED glib-2.0)</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>The first&nbsp;<code>pkg_check_modules()</code>&nbsp;parameter declares a <strong>prefix</strong> for CMake variables like&nbsp;<code>GLIB2_INCLUDE_DIRS</code>&nbsp;and&nbsp;<code>GLIB2_LIBRARIES</code>, later used for the compile and link. The&nbsp;<code>REQUIRED</code>&nbsp;argument <strong>causes configuration to fail unless</strong> the following “module” is the base name of a pkg-config file provided by the library. The corresponding CMake result for the above command is</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">-- Checking for module 'glib-2.0'
--   Found glib-2.0, version 2.56.4</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading {"level":4} -->
<h4>Include directories</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Before compiling, collect all the header paths you found earlier using&nbsp;<code>find_package()</code>&nbsp;or&nbsp;<code>pkg_check_modules()</code>:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">include_directories(include ${Boost_INCLUDE_DIRS} ${GLIB2_INCLUDE_DIRS})</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>The&nbsp;<code>include</code>&nbsp;parameter is needed only if that sub-directory of your package contains headers used to compile your programs. If your package also depends on other catkin ROS packages, add&nbsp;<code>${catkin_INCLUDE_DIRS}</code>&nbsp;to the list. Some packages provide variable names that do not comply with these recommendations. In that case, you must pass the absolute paths <strong>explicitly</strong> as&nbsp;<code>INCLUDE_DIRS</code>&nbsp;and&nbsp;<code>LIBRARIES</code>.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4>Exporting interfaces</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The&nbsp;<code>catkin_package()</code>&nbsp;command is only called once. In addition to any other parameters, it must declare the non-catkin <strong>system library</strong> and header packages needed by the <strong>interfaces you export</strong> to other ROS packages:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">catkin_package(DEPENDS Boost GLIB2)</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>Make sure all these packages are also mentioned in your&nbsp;<code>package.xml</code>&nbsp;using a&nbsp;<code>&lt;build_export_depend&gt;</code>&nbsp;or&nbsp;<code>&lt;depend&gt;</code>&nbsp;tag.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>C++ Message or Service Dependencies</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>When your C++ programs depend on ROS messages or services, they must be defined by catkin packages <strong>like</strong>&nbsp;<a href="https://wiki.ros.org/std_msgs">std_msgs</a>&nbsp;and&nbsp;<a href="https://wiki.ros.org/sensor_msgs">sensor_msgs</a>, which are used in the examples below.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>package.xml</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>For each C++ message dependency,&nbsp;<code>package.xml</code>&nbsp;should provide a&nbsp;<code><strong>&lt;depend&gt;</strong></code>&nbsp;tag with the ROS package name:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;depend>std_msgs&lt;/depend>
&lt;depend>sensor_msgs&lt;/depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading {"level":3} -->
<h3>CMakeLists.txt</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>For C++ access to <strong>ROS messages</strong>, CMake needs to find the message or service headers:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">find_package(catkin REQUIRED COMPONENTS std_msgs sensor_msgs)
include_directories(include ${catkin_INCLUDE_DIRS})</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>The&nbsp;<code>include</code>&nbsp;parameter is needed only if that sub-directory of your package contains headers also needed to compile your programs.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Since<strong> you presumably have build targets</strong> using the message or service headers, add this to ensure all their headers get built before any targets that need them:</p>
<!-- /wp:paragraph -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">add_dependencies(your_program ${catkin_EXPORTED_TARGETS})
add_dependencies(your_library ${catkin_EXPORTED_TARGETS})</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:heading -->
<h2>Python Module Dependencies</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>When your Python package <strong>imports</strong> <strong>other python modules</strong>,&nbsp;<code>package.xml</code>&nbsp;should provide a&nbsp;<code>&lt;exec_depend&gt;</code>&nbsp;with the appropriate package name.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><strong>System dependencies</strong>. For <strong>system dependencies</strong> like&nbsp;<code>python-numpy</code>&nbsp;or&nbsp;<code>python-yaml</code>, use the corresponding rosdep name:</li></ul>
<!-- /wp:list -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;exec_depend>python-numpy&lt;/exec_depend>
&lt;exec_depend>python-yaml&lt;/exec_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>These names are usually already defined in the&nbsp;<a href="https://github.com/ros/rosdistro/blob/master/rosdep/python.yaml">rosdistro repository</a>. If you need a module not yet defined there, please&nbsp;<a href="https://docs.ros.org/independent/api/rosdep/html/contributing_rules.html">fork that repository and add them</a>.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><strong>ROS infrastructure modules</strong>. Several ROS infrastructure modules, like&nbsp;<code>python-rospkg</code>&nbsp;or&nbsp;<code>python-rosdep</code>&nbsp;itself, apply to <strong>multiple</strong> ROS releases and are released <strong>independently</strong> of them. Resolve those module dependencies <strong>like</strong> other system packages, using the rosdep name:</li></ul>
<!-- /wp:list -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;exec_depend>python-rosdep&lt;/exec_depend>
&lt;exec_depend>python-rospkg&lt;/exec_depend>
﻿</pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:list -->
<ul><li><strong>ROS Python package</strong>. When you import from another <strong>ROS Python package</strong>, like&nbsp;<code>rospy</code>&nbsp;or&nbsp;<code>roslaunch</code>, always use the catkin package name:</li></ul>
<!-- /wp:list -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;exec_depend>roslaunch&lt;/exec_depend>
&lt;exec_depend>rospy&lt;/exec_depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:list -->
<ul><li><strong>ROS message or service</strong>. ROS message or service are defined as modules by ROS packages like&nbsp;<a href="https://wiki.ros.org/std_msgs">std_msgs</a>&nbsp;and&nbsp;<a href="https://wiki.ros.org/sensor_msgs">sensor_msgs</a>, used as examples here. Although&nbsp;<code>&lt;exec_depend&gt;</code>&nbsp;is adequate when all references are in Python, the recommended method is using a&nbsp;<code>&lt;depend&gt;</code>&nbsp;tag with the message package name:</li></ul>
<!-- /wp:list -->

<!-- wp:syntaxhighlighter/code -->
<pre class="wp-block-syntaxhighlighter-code">&lt;depend>std_msgs&lt;/depend>
&lt;depend>sensor_msgs&lt;/depend></pre>
<!-- /wp:syntaxhighlighter/code -->

<!-- wp:paragraph -->
<p>Your&nbsp;<code>CMakeLists.txt</code>&nbsp;<strong>need not specify Python-only dependencies</strong>. They are resolved automatically via&nbsp;<code>sys.path</code>.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Sources</h2>
<!-- /wp:heading -->

<!-- wp:list {"ordered":true} -->
<ol><li><a href="https://stackoverflow.com/questions/2358801/what-are-devel-packages">https://stackoverflow.com/questions/2358801/what-are-devel-packages</a></li><li><a href="https://docs.ros.org/melodic/api/catkin/html/howto/format2/index.html">https://docs.ros.org/melodic/api/catkin/html/howto/format2/index.html</a></li></ol>
<!-- /wp:list -->
