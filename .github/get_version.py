import version

import os

os.system(f'echo "VERSION={version.VERSION}.0" >> $GITHUB_ENV')
