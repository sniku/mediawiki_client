mediawiki_client
================

This is very simple terminal interface (TUI) for managing personal mediawiki installation.

I have a mediawiki installation on personal server for storing various notes, ranging from family addresses to code snippets, configuration files and commands I rarely use and can't remember.

While standard web-interface is functional, you have to launch a browser and it takes numerous clicks to find anything. 
I find it much more convenient to use **go my_commands** or **search IP** as shown below:

#### Installation ####

    # install twill from the official source. Version in debian/ubuntu repo is broken. New version in pip is buggy.
    pip install http://darcs.idyll.org/~t/projects/twill-0.9.tar.gz
    # install mediawiki_client
    cd mediawiki_client
    python setup.py install

#### Configuration ####
    
    cat ~/.config/wiki_client.conf
    
    [defaults]
    # This is the only required config directive, all the others are optional.
    MEDIAWIKI_URL: http://mywiki.example.net/
    
    # force an editor. Otherwise your default editor will be used.
    # I use vim, but you can use gedit or "gvim --nofork" or whatever you like.
    FORCE_EDITOR: vim
    
    # This is only required if you want to edit articles as a logged in user. (You have to create an account first)
    MEDIAWIKI_USERNAME: wikiuser
    MEDIAWIKI_PASSWORD: wikipassword
    
    # This is only required if your wiki installation is behind an additional HTTP auth.
    HTTP_AUTH_USERNAME: httpauth_user
    HTTP_AUTH_PASSWORD: httpauth_password
    
    # If you want to have less messages in the interactive mode.
    VERBOSE: false

#### Most common use case

MOst common use case is to open specific article for editing or viewing

    $ wiki_client my_article
    
Ar this point article "my_article" will be opened in your text editor.
If article doesn't exits, it will be created.


#### Interactive mode
    
This goes to interactive mode:

    $ wiki_client
     Wiki command: go my_commands 
     Opening "my_commands" # at this point your default editor is opened with the content of "my_commands"
     Saving "my_commands"


     
#### Searching for a note

    $ wiki_client
    Wiki command: /IP  # this is shortcut for "search IP"
    Searching for "IP"
    1: Sysadmin tools 
    	 nmap -sT -PN -n -sV -p- 192.168.5.63 # scan the shit out of this IP == ip configuration ==
    2: Kzk notes 
    	 select ip , count( ip ) as ile group by ip 
    3: Network 
    	 IP : 192.168.5.254
    4: Work notes 
    	 Subnet mask Example IP 
        
    Select 1, 2, 3, 4 to open the article
     
    Wiki command: 3
    Opening "Network" # opens content of "Network" in your default editor

#### Uploading a file

By default mediawiki requires you to log-in before you can upload a file so fill in your username and password in the config file first. 
    
    $ wiki_client upload ~/path/to/file.txt

#### Quick edits

This is the a quick way to append short text to the end of your article:

    $ wiki_command append my_article "some text here"
    
It's great for integrating with other programs. You can run this for example in cron.

There's alternative version if you want to append text from a text file:

    $ wiki_command append my_article < ~/path/to/some_file.txt
    


    
