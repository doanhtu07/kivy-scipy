# Overview

This is an example Kivy project that uses scipy. I have built it with buildozer and docker ubuntu image.

The hardest problem is to get scipy dependencies right. The solution can be found here: https://github.com/kivy/python-for-android/issues/2508

But I came to realize that even after you unzip and have gfortran running right, if you're using a Mac, it's possible that you cannot execute the gfortran binary provided from the Github issue above.

So, my solution is to swing up a Linux virtual machine and use buildozer on there since the provided gfortran binary is compatible with Linux.

## My machine system

- MacOS Intel Sonoma 14.5

## NOTES

- Since the code for the app belongs to a friend of mine, so I cannot show them here
- But the only important files are: Dockerfile, Makefile, Pipfile, buildozer.spec (so I keep them here)
- Makefile might look a little messy, there are stuff that can be cleaned up -> Look at this Makefile and the one from the issue above to get the big picture

---

- My Dockerfile will pull this Github repo by default, so you can then add your own Kivy app code and see how it works

  - You can also fork this repo and add your own code too

- You will also need to setup your enough dependencies like I did with pipenv if you use something else

---

- I've only looked at targeting for Android. So for iOS, that might need some extra work
- If I'm free, I'll look into it. But for now, if you have any questions, feel free to open an issue

# Use Dockerfile

Run `docker build --no-cache -t buffercapacity4-docker .` to build image

Run `docker run --name buffercapacity4 -it buffercapacity4-docker /bin/bash` to create new container shell

- Run `docker start <container_name>` to start existing container
- Run `docker exec -it <container_name> /bin/bash` to run existing container shell
- Container name is buffercapacity4

Run `source $(pipenv --venv)/bin/activate` to activate pipenv

Run `make` to install toolchains for gfortran that supports scipy

Run `buildozer android debug`

# After having apk file

Run `docker cp <container_name>:/home/ubuntu/example.txt ~/Downloads/` to copy file from container to local machine

- `docker cp buffercapacity4:/root/BufferCapacity4/bin/...apk /local/path/`

Boot up a virtual device in Android Studio

Run `adb devices` to see list of devices

Run `adb -s <emulator_id> install path/to/myapp.apk` to install apk on device emulator

Voila!
