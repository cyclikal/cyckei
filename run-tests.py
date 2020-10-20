import os
import sys

if __name__ == "__main__":
    command_name = ""
    for i in range(1, len(sys.argv)):
        if i == len(sys.argv)-1:
            command_name = command_name + str(sys.argv[i]).lower()
        else:
            command_name = command_name + str(sys.argv[i]).lower() + " "
 
    if command_name == "help" or command_name == "":
        print("Command options")
    elif command_name == "all":
        os.system("pytest tests")
    else:
        command_name = "pytest tests\\"+command_name
        os.system(command_name)  