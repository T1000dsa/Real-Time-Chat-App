import shutil
import logging
import os
import sys
import subprocess

logger = logging.getLogger(__name__)

env_file = '.env'
env_example_file = '.env.example'
if os.path.exists(env_file):
    logger.debug(f'{env_file} file exist')

else:
    shutil.copyfile(env_example_file, env_file)
    logger.debug(f'{env_file} file was created from {env_example_file}')
    
    if sys.platform == 'win32':
        result = subprocess.run(['bash', 'migrations.sh'], capture_output=True, text=True)
    else:
        result = subprocess.run(['./migrations.sh'], capture_output=True, text=True)