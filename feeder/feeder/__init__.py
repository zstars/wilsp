
import os
import config as config_module

config = config_module.config[os.environ.get("FEEDER_CONFIG", "development")]
