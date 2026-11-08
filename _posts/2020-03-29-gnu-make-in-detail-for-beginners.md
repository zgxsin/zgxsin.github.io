---
title: GNU Make in Detail for Beginners
published: true
date: 2020-03-29 15:52
author: "Guoxiang (Shawn) Zhou"
comments: true
categories: [Technical]
---

<!-- wp:paragraph -->
<p>For those who wants to understand <strong>GNU Make</strong> better, I found this <a href="https://opensourceforu.com/2012/06/gnu-make-in-detail-for-beginners/">article</a> very helpful and useful. </p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Here I write down some essentials from the mentioned article.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>The Beginning of Makefile </h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Large projects can contain thousands of lines of code, distributed in multiple source files, written by many developers and arranged in several sub-directories.&nbsp;</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Each project needs a <strong>Makefile</strong> — a script that describes the project structure, namely, the source code files, the dependencies between them, compiler arguments, and how to produce the target output (normally, one or more executables). Whenever the make command is executed, the Makefile in the current working directory is interpreted, and the instructions executed to produce the target outputs. The Makefile contains a collection of rules, macros, variable assignments, etc. (‘Makefile’ or ‘makefile’ are both acceptable.)</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The general syntax of a Makefile rule is as follows:</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>target: dependency1 dependency2 ...
[TAB] action1
[TAB] action2
    ...</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>A simple Makefile for a small project is as follows:</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>all: main.o module.o
    gcc main.o module.o -o target_bin
main.o: main.c module.h
    gcc -I . -c main.c
module.o: module.c module.h
    gcc -I . -c module.c
clean:
    rm -rf *.o
    rm target_bin</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>where we have four targets in this file:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code><strong>all</strong></code>&nbsp;is a <strong>special target</strong> that depends on&nbsp;<code>main.o</code>&nbsp;and&nbsp;<code>module.o</code>, and has the command (from the “manual” steps earlier) to make GCC link the two object files into the final executable binary.</li><li><code><strong>main.o</strong></code>&nbsp;is a <strong>filename target</strong> that depends on&nbsp;<code>main.c</code>&nbsp;and&nbsp;<code>module.h</code>, and has the command to compile&nbsp;<code>main.c</code>&nbsp;to produce&nbsp;<code>main.o</code>.</li><li><code><strong>module.o</strong></code>&nbsp;is a <strong>filename target</strong> that depends on&nbsp;<code>module.c</code>&nbsp;and&nbsp;<code>module.h</code>; it calls GCC to compile the&nbsp;<code>module.c</code>&nbsp;file to produce&nbsp;<code>module.o</code>.</li><li><code><strong>clean</strong></code>&nbsp;is a <strong>special target</strong> that has no dependencies, but specifies the commands to clean the compilation outputs from the project directories.</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>The <strong>make</strong> command accepts a target parameteImprovedr (one of those defined in the <strong>Makefile</strong>), so the generic command line syntax is&nbsp;<code><strong>make &lt;target&gt;</strong></code>. However, <strong>make</strong> also works if you do not specify any target on the command line, saving you a little typing; <strong>in such a case, it defaults to the first target defined in the Makefile</strong>. In our Makefile, that is the target&nbsp;<code><strong>all</strong></code>, which results in the creation of the desired executable binary&nbsp;<code>target_bin</code>!</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Features in Makefile</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Assignments</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>There are different ways of assigning variables in a Makefile. Though variable assignments can occur in any part of the Makefile, on a new line, most variable declarations are found at the beginning of the Makefile.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4>Simple Assignments (:=)</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We can assign values (RHS) to variables (LHS) with this operator, for example:&nbsp;<code>CC := gcc</code>. With simple assignment (<code>:=</code>), the value is expanded and stored to <strong>all occurrences </strong>in the <strong>Makefile</strong> when its first definition is found.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4>Recursive Assignment (=)</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Recursive assignment involves variables and values that are <strong>not evaluated immediately</strong> on encountering their definition, but are <strong>re-evaluated every time they are encountered in an action that is being executed.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4>Conditional assignment (?=)</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Conditional assignment statements assign the given value to the variable only if the variable does not yet have a value.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4>Appending (+=)</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The appending operation appends texts to an existing variable. For example:</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>CC = gcc
CC += -W</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p><code>CC</code>&nbsp;now holds the value&nbsp;<code>gcc -W</code>.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Using Patterns and Special Variables</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The&nbsp;<code><strong>%</strong></code>&nbsp;character can be used for <strong>wildcard pattern-matching</strong>, to provide generic targets. For example:Improved</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>%.o: %.c
[TAB] actions</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>When&nbsp;<code><strong>%</strong></code>&nbsp;appears in the dependency list, it is replaced with the same string that was used  in the target.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Inside</strong> <strong>actions</strong>, we can use special variables for matching filenames. Some of them are:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><code><strong>$@</strong></code>&nbsp;(full target name of the current target)</li><li><code><strong>$?</strong></code>&nbsp;(returns the dependencies that are newer than the current target)</li><li><code><strong>$*</strong></code>&nbsp;(returns the text that corresponds to&nbsp;<code>%</code>&nbsp;in the target)</li><li><code><strong>$&lt;</strong></code>&nbsp;(name of the first dependency)</li><li><code><strong>$^</strong></code>&nbsp;(name of all the dependencies with space as the delimiter)</li></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3>Action Modifiers</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We can change the behavior of the <strong>actions</strong> we use by prefixing certain action modifiers to the actions. Two important action modifiers are:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>-  (minus)</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>ImprovedPrefixing this to any action causes any error that occurs while executing the action to be ignored. &nbsp;Looking at the Makefile from our sample: in the clean target, the&nbsp;<code><strong>rm target_bin</strong></code>&nbsp;command will produce an error if that file does not exist (this could happen if the project had never been compiled, or if&nbsp;<code>make clean</code>&nbsp;is run twice consecutively). To handle this, we can prefix the&nbsp;<code>rm</code>&nbsp;command with a minus, to ignore errors:&nbsp;<code><strong>-rm target_bin</strong></code>.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>@ (at)</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>It suppresses the standard <strong>print-action</strong>-to-standard-output behavior of make, for the action/command that is prefixImproveded with&nbsp;<code>@</code>. For example, to echo a custom message to standard output, we want only the output of the echo command, and don’t want to print the echo command line itself.&nbsp;<code><strong>@echo Message</strong></code>&nbsp;will print “Message” without the echo command line being printed.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Use PHONY to Avoid File-target name conflicts</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Remember the&nbsp;<code>all</code>&nbsp;and&nbsp;<code>clean</code>&nbsp;special targets in our Makefile? What happens when the project directory has files with the names&nbsp;<code>all</code>&nbsp;or&nbsp;<code>clean</code>? The conflicts will cause errors. Use the&nbsp;<code><strong>.PHONY</strong></code>&nbsp;directive to specify which targets are not to be treated as files For example:&nbsp;<code>.PHONY: all clean</code>.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Simulating make Without Actual Execution</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>At times, maybe when developing the Makefile, we may want to trace the make execution (and view the logged messages) without actually running the actions, which is time consuming. <strong>Simply use&nbsp;<code>make -n</code>&nbsp;to do a “dry run”.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Using the Shell Command Output in A Variable</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Sometimes we need to use the output from one command/action in other places in the Makefile — for example, checking versions/locations of installed libraries, or other files required for compilation.&nbsp;We can obtain the shell output using the shell command. For example, to return a list of files in the current directory into a variable, we would run:&nbsp;<code>LS_OUT = $(shell ls)</code>.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Improved Makefile Example</h2>
<!-- /wp:heading -->

<!-- wp:code -->
<pre class="wp-block-code"><code>CC = gcc # Compiler to use
OPTIONS = -O2 -g -Wall # -g for debug, -O2 for optimise and -Wall additional messages
INCLUDES = -I . # Directory for header file
OBJS = main.o module.o # List of objects to be build
.PHONY: all clean # To declare all, clean are not files
 
all: ${OBJS}
    @echo "Building.." # To print "Building.." message
    ${CC} ${OPTIONS} ${INCLUDES} ${OBJS} -o target_bin 
 
%.o: %.c  # % pattern wildcard matching
    ${CC} ${OPTIONS} -c $*.c ${INCLUDES}
list:
    @echo $(shell ls) # To print output of command 'ls'
 
clean:
    @echo "Cleaning up.."
    -rm -rf *.o # - prefix for ignoring errors and continue execution
    -rm target_bin</code></pre>
<!-- /wp:code -->

<!-- wp:shortcode -->

[thumbs-rating-buttons]

<!-- /wp:shortcode -->
