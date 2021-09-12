import logging
import logging.handlers
import os 
import sys 

def create_logger(file: str, name: str, level: str, rotating: bool = False):
    print(file)
    path = os.path.split(file)[0]
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist 
        os.makedirs(path)
        print("New directory is created: {}".format(path))
  
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # If logger already has handler, assume it was already created
    if len(logger.handlers) == 1:
        return logger

    if rotating:
        handler = logging.handlers.RotatingFileHandler(
            file, maxBytes=10000000, backupCount=3)
    else:
        handler = logging.FileHandler(file)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p')

    handler.setFormatter(formatter)

    logger.addHandler(handler)
    
    #
    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setLevel(logging.DEBUG)
    handler_stdout.setFormatter(formatter)
    logger.addHandler(handler_stdout)

    return logger
