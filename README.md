# glygen_llm_api
## Installation of source code on the respective servers
Steps for deploying source code to a server with script.

+ VPN to GW server: 

  GW vpn server

+ connect to the GW server (ex.: GW test server)

  Open your terminal and type the following

  ssh <user_name>@server
  ```
  ssh <user_name>@<server>
  ```
  you'll be prompted for your username and password, enter them.

+ (if you are a new user do this step else skip to next).

  Clone the git repository:
  ```
  git clone https://github.com/glygener/glygen-llm-api.git
  ```

+ Move to folder "\glygen-llm-api"
  ```
  cd glygen-llm-api
  ```
+ (do this step if you are deploying this branch for the first time else skip to next).

  ```
  git pull
  ```
  Or use 
  ```
  git pull origin ver_??
  ```
  you'll be prompted for your GitHub username and password, enter them.

+ Change to the GitHub branch you wish to update on the server.
  git checkout <branch_name>
  ```
  git checkout ver_1.0
  ```

+ Check whether it's switched to the desired branch
  ```
  git branch
  ```

  The current working branch will be displayed with a "*" before it.
  ```shell
    7fece56
    master
    ver1-simplifyed-search
  * ver_1.0
  ```

+ update this repository, pull the latest GitHub changes
  ```
  git pull origin ver_??
  ```
  you'll be prompted for your GitHub username and password, enter them.

+ Move to folder "\api"
  ```
  cd api
  ```

+ Deploying code by running script. For 'sudo' command please use server password.

    + For Test server:
      ```
      docker stop running_glygen_ai_api_tst
      python3 create_api_container.py --server tst
      docker start running_glygen_ai_api_tst
      ```
    + For Beta server:
      ```
      docker stop running_glygen_ai_api_beta
      python3 create_api_container.py --server beta
      docker start running_glygen_ai_api_beta
      ```
    + For Production server:
      ```
      docker stop running_glygen_ai_api_prd
      python3 create_api_container.py --server prd
      docker start running_glygen_ai_api_prd

  You'll receive a message, stating the full container ID. If this is not the message, please contact your supervisor or Rene.

+ Exit the server
  ```
  exit
  ```

That's it, you are done.

## Installation phases
* **During Development phase:**
  Production and Beta have the code from the last version branch. Test has the code from the master.

* **During Test phase:**
  Production has the code from the last version branch. Test and Beta have the code from the master.

* **Release:**
  A new branch is created. Production and Beta get the code from the branch. Test remains master.
