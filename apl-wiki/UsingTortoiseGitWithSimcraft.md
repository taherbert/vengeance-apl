# Introduction

Simulationcraft recently switched from Subversion to Git. If you're a Windows user and have been using TortoiseSVN, you will likely find that TortoiseGit is a bit confusing at first (I did). This is compounded by the near lack of support documentation compared to TortoiseSVN. This is a step-by-step guide to getting set up with Git and TortoiseGit on Windows.


# Installing Git and TortoiseGit

First thing's first, we need to download and install all of the components.

  * Download and install the latest version of [Git](https://msysgit.github.io/). You're looking for the "Full Installer for official Git for Windows"; for this tutorial I'm using version 1.8.5.2. You will be presented with several options for the install; I left all of these at their defaults.
  * According to the [TortoiseGit site](https://tortoisegit.org/), you also need Windows Installer. Most people should already have this though. If not, grab it and install.
  * Download and install the latest version of [TortoiseGit](https://tortoisegit.org/download/). Again, I installed the default components.

# Setting up your local repository

Now we need the code. We're going to clone the remote repository to create our local repository, and then tweak some authentication settings.

Right click on the folder and choose `Git Clone` from the menu

![http://wiki.simulationcraft.googlecode.com/git/images/git_clone.png](http://wiki.simulationcraft.googlecode.com/git/images/git_clone.png)

This will bring up the "Git clone" dialog box, shown below. The URL you want can be found [here](http://code.google.com/p/simulationcraft/source/checkout) under "Option 1" - it's basically the google code URL with your google code account inserted in the middle. Directory is the location of the local repository that we're creating. This should auto-fill, but you can tweak that if you like (as I did - it will default to path\simulationcraft but I changed it to path\simcraft in this example). You can leave "Load Putty Key" empty or unchecked - google code doesn't use this type of authentication.

![http://wiki.simulationcraft.googlecode.com/git/images/git_clone_dialog.png](http://wiki.simulationcraft.googlecode.com/git/images/git_clone_dialog.png)

Now you should have a complete local repository. There are two more steps we need to perform to make committing and pushing code less painful. For these last two steps, right click on the folder containing your new local repository and choose
```
TortoiseGit > Settings
```
and navigate to the "Git" subheading in the left-hand pane.

![http://wiki.simulationcraft.googlecode.com/git/images/git_setup_name_email.png](http://wiki.simulationcraft.googlecode.com/git/images/git_setup_name_email.png)

First, we need to set our User Info. TortoiseGit wouldn't let me commit to my local repository without doing this, it just threw an error dialog back at me. I chose the "Local" radio button under "Config Source" and then put in my name and e-mail address. I chose the one associated with the google code account I'm using for simcraft, but I don't think that's required. For all I know you could put garbage data here and it would work.

The last step here is to add your google code password to the local .git/config file. Without this step, TortoiseGit will ask you for your password every time you commit, which would be annoying. To do this, click on the "Edit local .git/config" button, which will pop up a text editor window like the one below. Go down to the line reading
```
url = https://username@code.google.com/p/simulationcraft 
```
that specifies the `origin`. Insert your google code password (found [here](https://code.google.com/hosting/settings) ) into the URL as follows:
```
url = https://username:GOOGLECODEPASSWORD@code.google.com/p/simulationcraft
```

![http://wiki.simulationcraft.googlecode.com/git/images/git_edit_local_config_file.png](http://wiki.simulationcraft.googlecode.com/git/images/git_edit_local_config_file.png)

Hit save, and then hit "OK" to exit out of the TortoiseGit Settings menu. All Done!

# Making your first (new) commit

Git works a little differently than SVN, so the terminology is also a little different. If you're used to SVN, you think of "Commit" as meaning "send these changes to the remote repository." That's not how TortoiseGit uses the term though. In this case, "commit" is roughly (completely?) equivalent to staging the file in your local repository. You then "push" those changes to the remote repository ("origin").  In short, the workflow is sort of like this:
  * Make changes in working directory/repository
  * Commit those changes to local repository (aka "staging" the changed files)
  * Push the local repository to the remote repository ("origin")

As far as I know, anything you do not commit will not be pushed, so you can edit a bunch of files, commit a subset of those, and then push the subset. This is basically the equivalent process to checking/unchecking files in TortoiseSVN's commit dialog box. The added wrinkle with Git is that there can be multiple repositories (both local and remote), but we'll ignore that for now.

So to test that everything is set up properly, make a quick change to a file. Then right-click on the local repository folder and choose
```
Git Commit -> "master"
```
from the menu. This will give you a familiar-looking dialog box (shown below) that lets you set the commit message as well as choose which files to include in the commit. Type your commit message into the Message box and hit "OK" (nice feature of TortoiseGit: the OK button is greyed out until you type a message - no more blind commits). You'll see a progress bar and (hopefully) a success message.

![http://wiki.simulationcraft.googlecode.com/git/images/git_commit.png](http://wiki.simulationcraft.googlecode.com/git/images/git_commit.png)

Now we want to commit this to the remote repository. To do that, we right click on the local repository folder and choose
```
TortoiseGit > Push
```
![http://wiki.simulationcraft.googlecode.com/git/images/git_menu_push.png](http://wiki.simulationcraft.googlecode.com/git/images/git_menu_push.png)

This brings up the Push dialog box, which should auto-populate the local and remote repository fields under "Ref" with `master` and the Destination with `origin`. I didn't have to change any of these settings, I just hit OK to commit and it worked. If you were working on some branch, you might have to change one or all of these fields as appropriate.

![http://wiki.simulationcraft.googlecode.com/git/images/git_push_dialog.png](http://wiki.simulationcraft.googlecode.com/git/images/git_push_dialog.png)

Once you hit OK, you should get another progress bar and then (hopefully) another "success" message. Congratulations, you've made your first contribution with Git!