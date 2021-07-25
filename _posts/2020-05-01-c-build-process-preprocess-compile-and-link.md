---
title: C++ Build Process -- Preprocess, Compile and Link
# C++ Build Process: Preprocess, Compile and Link. : cannot be recognised in this case.
published: true
date: 2020-05-01 10:39
author: zgxsin
comments: true
categories: [C++]
---
<!-- wp:paragraph -->
<p>Each C++ <strong>source file</strong> needs to be <strong>compiled</strong> into an object file. The object files resulting from the compilation of multiple source files are then linked into an executable, a shared library, or a static library (the last of these being just an archive of object files). <strong>C++ source files generally have the .cpp, .cxx or .cc extension suffixes.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The first step that the compiler will do on a source file is run the <strong>preprocessor</strong> on it. <strong>Only source files are passed to the compiler</strong> (to preprocess and compile it).<strong> Header files aren’t passed to the compiler. Instead, they are included from source files.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For each C++ source file, the preprocessor will build a translation unit by inserting content in it when it finds an #include directive at the same time that it’ll be stripping code out of the source file and of the headers when it finds <a href="http://www.cplusplus.com/doc/tutorial/preprocessor/#conditional_inclusions">conditional compilation</a> blocks whose directive evaluates to <code>false</code>. It’ll also do some <a href="http://www.cplusplus.com/doc/tutorial/preprocessor/">other tasks</a> like macro replacements.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Once the preprocessor finishes creating that (sometimes huge) translation unit, the compiler starts the compilation phase and produces the object file.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Source</h2>
<!-- /wp:heading -->

<!-- wp:list {"ordered":true} -->
<ol><li><a href="https://www.toptal.com/c-plus-plus/c-plus-plus-understanding-compilation">https://www.toptal.com/c-plus-plus/c-plus-plus-understanding-compilation</a></li></ol>
<!-- /wp:list -->
