mediawiki_client
================

This is very simple terminal interface (TUI) for managing personal mediawiki installation.

I have a mediawiki installation on personal server for storing various notes, ranging from family addresses to code snippets, configuration files and commands I rarely use and can't remember.

While standard web-interface is functional, you have to launch a browser and it takes numerous clicks to find anything. 
I find it much more convenient to use **go my_commands** or **search IP** as shown below:

#### Installation ####

    cd mediawiki_client
    python setup.py install

#### Configuration ####
    
    cat ~/.config/wiki_client.conf
    
    [defaults]
    # This is the only required config directive, all the others are optional.
    MEDIAWIKI_URL: http://mywiki.example.net/
    
    # force an editor. Otherwise your default editor will be used.
    FORCE_EDITOR: vim
    
    # This is only required if you want to edit articles as a logged in user. (You have to create an account first)
    MEDIAWIKI_USERNAME: wikiuser
    MEDIAWIKI_PASSWORD: wikipassword
    
    # This is only required if your wiki installation is behind an additional HTTP auth.
    HTTP_AUTH_USERNAME: httpauth_user
    HTTP_AUTH_PASSWORD: httpauth_password
    
    # If you want to have less messages in the interactive mode.
    VERBOSE: false

#### Opening and editing a note
    
This goes to interactive mode:

    $ wiki_client
     Wiki command: go my_commands 
     Opening "my_commands" # at this point your default editor is opened with the content of "my_commands"
     Saving "my_commands"

This is a quicker way of going the same:

    $ wiki_client my_commands


     
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
