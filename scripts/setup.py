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
        subprocess.run(['python', '-c', 'from src.core.services.tasks import send_email_task'], check=True)
        result = subprocess.run(['powershell', '.\\migrations.sh'], capture_output=True, text=True)
    else:
        subprocess.run(['python', '-c', 'from src.core.services.tasks import send_email_task'], check=True)
        result = subprocess.run(['./migrations.sh'], capture_output=True, text=True)