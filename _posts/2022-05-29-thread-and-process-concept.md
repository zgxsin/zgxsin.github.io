---
title: The concept of thread, process and cores
published: true
date: 2022-05-29
author: "Guoxiang (Shawn) Zhou"
---

# Introduction

Consider the cores, threads and processes as follows:

- Cores are your mouth
- Threads (hardware threads) are your hand
- Process (done by CPU) are eating your food.

So if you have multiple mouths (cores) then you can eat a lot at a time. But it would be bottlenecked by your hand (hardware thread) because only two hands are used to put food in multiple mouth. So the speed would be slow.

Likewise, if you have multiple hands (hardware threads) and only one mouth (core) then problem would also occur. Here the bottleneck would be your mouth as your hand can give you plenty of food at a time but it is restricted by your mouth.

So there should be a complete balance between the thread and the cores so that the CPU can be at it's best efficiency. That's why we see double the thread w.r.t cores which in a way symbolizes one mouth and two hand. It's like `1:2` ratio. The core itself cannot work on multiple threads in parallel. It needs a switch between single threads. The switching between these threads is what we call concurrent execution. It mimics the the parallel execution.

# Threads

## Hardware Threads

**Hardware threads** are the threads that actually perform computation. Contemporary machine architectures offer one or more hardware threads per CPU core.

## Software Threads

**Software threads** (also known as OS threads or system threads) are the threads that the operating system manages across all processes and schedules for execution on hardware threads. It’s typically possible to create `more` software threads than hardware threads, because when a software thread is blocked (e.g., on I/O or waiting for a mutex or condition variable), throughput can be improved by executing other, unblocked, threads.

## [STD::THREAD](https://en.cppreference.com/w/cpp/thread/thread)

**std::threads are objects in a C++ process that act as handles to underlying software threads**. Some std::thread objects represent “null” handles, i.e., correspond to no software thread, because they’re in a default-constructed state (hence have no function to execute), have been moved from (the moved-to std::thread then acts as the handle to the underlying software thread), have been joined (the function they were to run has finished), or have been detached (the connection between them and their underlying software thread has been severed).

### Join and Detach

When `std::thread::join()` is called, the calling thread will block until the thread of execution has completed. Basically, this is one mechanism that can be used to know when a thread has finished. When std::thread::join() returns, the OS thread of execution has completed and the C++ thread object can be destroyed.

When `std::thread::detach()` is called, the thread of execution is "detached" from the thread object and is no longer represented by a thread object - they are two `independent` things. The C++ thread object can be destroyed and the OS thread of execution can continue on. If the program needs to know when that thread of execution has completed, some other mechanism needs to be used. `std::thread::join()` cannot be called on that thread object any more, since it is no longer associated with a thread of execution.

It is considered an error to destroy a C++ thread object while it is still "joinable". That is, in order to destroy a C++ thread object either std::thread::join() needs to be called (and completed) or std::thread::detach() must be called. If a C++ thread object is still joinable when it's destroyed, an exception will be thrown.
