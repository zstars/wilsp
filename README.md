
# Deployment

As of now the project has only been tested with Python 3.
Probably, Python 2.7 will NOT work without changes.

The project has several components. The main ones are the Feeders and the Servers.
It is recommended to use virtualenvs with them, although the same virtualenv can be used
for both.

## Feeder

### Requirements

The requirements for the Feeder component are defined in the requirements.txt file, which can be installed through
> pip install -r requirements.txt

In order for all the dependencies to be successfully installed, however, before doing that you
might need to install the development package for your python version, and the zbar library.
To do so, under Ubuntu:

> sudo apt-get install python3.5-dev
> sudo apt-get install libzbar-dev


### Configuration scheme

The main Feeder configuration file is the config.py script. The file is meant to be version-controlled.
Secret values should be referenced from that file as environment variables.

The cameras definition file (cams.yml) is a different, YML file. Its path is referenced through config.py through
the ```CAMS_YML``` setting.

### Scaling

To scale beyond a certain number of users you might need to increase your OS or Redis limits.

The OS open file and maximum number of connections limit may need to be increased. To check the current limits:
```limit -a```.

Redis by default supports a relatively low number of users (around 4000). To increase it, you need to run the server as such:
```
./redis-server --maxclients 100000
```

### REDIS statistics

cycle_elapsed: How long (in seconds) the current cycle of the stream has been active from the server-side
cycle_frames: How many frames have been rendered in that particular cycle

(FPS for the current cycle is thus cycle_frames / cycle_elapsed)

## Server

TO-DO 


# Research Papers

More details on the platform and its architecture, along with various performance and analysis, can be found in the published research papers:

- Rodriguez-Gil, L., Orduña, P., García-Zubia, J., & López-de-Ipiña, D. (2018). Interactive live-streaming technologies and approaches for web-based applications. Multimedia Tools and Applications, 77(6), 6471-6502. (Available: https://link.springer.com/article/10.1007/s11042-017-4556-6).
  
- Rodriguez-Gil, L., García-Zubia, J., Orduña, P., & López-de-Ipiña, D. (2017). An open and scalable Web-based interactive live-streaming architecture: The WILSP platform. IEEE Access, 5, 9842-9856. (Available: https://ieeexplore.ieee.org/document/7937791/).



### Known-issues and TO-DOs

- h264_source scheme might not be guaranteed to recover from ffmpeg or network failures. 
