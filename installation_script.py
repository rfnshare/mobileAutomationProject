import glob
import json
import re
import shutil
import subprocess
import sys
import importlib
import platform
import os
import time


def install_package(package_name):
    print(f"{package_name} is not installed. Installing...")
    try:
        # Determine the appropriate package manager based on the platform
        if platform.system() == "Linux":
            package_manager = "pip3" if shutil.which("pip3") else subprocess.run(
                ["sudo", "apt", "install", "python3-pip"], check=True)
        elif platform.system() == "Darwin":  # macOS
            package_manager = "pip"
        elif platform.system() == "Windows":
            package_manager = "pip.exe"
        else:
            print("Unsupported operating system")
            sys.exit(1)

        subprocess.run(
            [package_manager, "install", package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        print(f"{package_name} has been installed.")
    except subprocess.CalledProcessError:
        print(f"Failed to install {package_name}. Please install it manually.")
        sys.exit(1)


# Check and install 'tqdm' if not already installed
try:
    importlib.import_module("tqdm")
except ImportError:
    install_package("tqdm")

# Check and install 'colorama' if not already installed
try:
    importlib.import_module("colorama")
except ImportError:
    install_package("colorama")

from tqdm import tqdm
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class InstallationError(Exception):
    def __init__(self, package, message):
        self.package = package
        self.message = message
        super().__init__(self.message)


class PackageManagerNotFound(Exception):
    def __init__(self, package_manager):
        self.package_manager = package_manager
        self.message = f"{package_manager} package manager not found. Please install it and try again."
        super().__init__(self.message)


def get_package_manager():
    system_platform = platform.system().lower()
    if system_platform == "windows":
        package_manager = ["choco", "npm"]
    elif system_platform == "linux":
        package_manager = ["brew", "apt", "npm"]
    elif system_platform == "darwin":
        package_manager = ["brew", "npm"]
    else:
        raise InstallationError("Unsupported operating system")

    # Check if the selected package manager is available in the system
    if package_manager is None:
        raise PackageManagerNotFound("apt, brew, or npm")
    return package_manager
    # try:
    #     subprocess.run(
    #         [package_manager, "--version"],
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE,
    #         check=True,
    #         shell=system_platform == "windows",  # Use shell=True only for Windows
    #     )
    #     return package_manager, sub_package_manager
    # except subprocess.CalledProcessError:
    #     raise PackageManagerNotFound(package_manager)


def execute_command(command):
    try:
        return subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None


def find_java_directory():
    # Define search patterns for JDK installation directories
    jdk_patterns = {
        "posix": ["/usr/lib/jvm/java-*", "/home/linuxbrew/.linuxbrew/opt/java/bin"],
        "nt": [r"C:\Program Files\Java\jdk-*", r"C:\Program Files\OpenJDK\jdk-*"],
    }

    current_os = os.name
    jdk_paths = []

    if current_os in jdk_patterns:
        patterns = jdk_patterns[current_os]
        for pattern in patterns:
            jdk_paths += glob.glob(pattern)

    if not jdk_paths:
        raise EnvironmentError("No Java JDK installations found matching the patterns.")

    return jdk_paths[0]  # Return the first matching JDK path


def find_sdk_directory():
    system = platform.system()
    home_dir = os.path.expanduser("~")

    if system == "Linux":
        possible_paths = [
            "/usr/local/android-sdk",  # Common installation path on Linux
            f"{home_dir}/Android/Sdk",  # Android Studio default SDK path
            "/usr/lib/android-sdk",
        ]
    elif system == "Darwin":
        possible_paths = [
            "/usr/local/android-sdk",  # Common installation path on macOS
            f"{home_dir}/Library/Android/sdk",  # Android Studio default SDK path on macOS
        ]
    elif system == "Windows":
        possible_paths = [
            f"{home_dir}\\AppData\\Local\\Android\\Sdk",  # Default SDK path on Windows
            "C:\\Android\\android-sdk",
        ]
    else:
        print("Unsupported operating system.")
        return None

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def is_installed(package_name, check_commands, min_version=None):
    if package_name == "Android SDK":
        sdk_directory = find_sdk_directory()
        print(f"{Fore.GREEN}SDK Path: {sdk_directory}{Style.RESET_ALL}")
        if sdk_directory is None:
            return False, None
        else:
            return True, None
    for check_command in check_commands:
        version_output = execute_command(check_command)
        if version_output:
            pattern = r"(\d+\.\d+(\.\d+)?)"
            match = re.search(pattern, version_output.strip())
            installed_version = match.group(1)

            if min_version:
                installed_version_u = list(map(int, installed_version.split(".")))
                min_version_u = list(map(int, min_version.split(".")))

                if installed_version_u < min_version_u:
                    return False, installed_version  # Return the installed version
            return True, installed_version  # Return the installed version

    return False, None  # Return False if no version information is found


def execute_install_or_update_command(command, package_name):
    # Capture the error output and log it
    try:
        subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
            shell=True,
            universal_newlines=True,
            cwd=os.getcwd(),
        )
        return True
    except subprocess.CalledProcessError as e:
        # If the installation or update fails, log the error
        error_message = e.stdout
        log_error(package_name, error_message)
        return False


def update_or_install_package(package_name, commands):
    os_package_manager = get_package_manager()
    for package_manager, command in commands.items():
        if package_manager in os_package_manager:
            print(f"{package_name} installing/updating using {package_manager}...")
            if execute_install_or_update_command(command, package_name):
                return True  # Return True on success
            else:
                print(f"Unable to install/update with {package_manager} package manager. Trying with the next package manager...")
    return False


def handle_sub_package(
        sub_package_name, install_command, update_command, uninstall_command
):
    # Install the sub-package
    try:
        print(f"Installing {sub_package_name}...")
        subprocess.run(
            install_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=True,
        )
        print(f"{sub_package_name} has been successfully installed.")
    except subprocess.CalledProcessError:
        print(f"An error occurred while installing {sub_package_name}.")

    # Update the sub-package (if an update command is provided)
    if update_command:
        try:
            print(f"Updating {sub_package_name}...")
            subprocess.run(
                update_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                shell=True,
            )
            print(f"{Fore.GREEN}{sub_package_name} has been updated to the latest version.{Style.RESET_ALL}")
        except subprocess.CalledProcessError:
            print(f"{Fore.RED}An error occurred while updating {sub_package_name}.{Style.RESET_ALL}")

    # Uninstall the sub-package (if an uninstallation command is provided)
    if uninstall_command:
        try:
            print(f"Uninstalling {sub_package_name}...")
            subprocess.run(
                uninstall_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                shell=True,
            )
            print(f"{sub_package_name} has been uninstalled.")
        except subprocess.CalledProcessError:
            print(f"An error occurred while uninstalling {sub_package_name}.")


def check_and_install_or_update(package_details):
    package_name = package_details["name"]
    check_commands = package_details["check_commands"]
    install_commands = package_details["install_commands"]
    update_commands = package_details["update_commands"]
    uninstall_commands = package_details.get("uninstall_commands", {})
    min_version = package_details.get("min_version", None)
    sub_packages = package_details.get("sub_packages", [])

    # package_manager, sub_package_manager = get_package_manager()
    installed = False

    # Check if the package is already installed
    is_installed_result, installed_version = is_installed(
        package_name, check_commands, min_version
    )
    if is_installed_result:
        if package_name == "Appium":
            print(f"{Fore.GREEN}{package_name} is already installed.{Style.RESET_ALL}")
            # appium_driver_list_output = execute_command("appium driver list")
            # if appium_driver_list_output:
            #     print(appium_driver_list_output)
        elif package_name == "JAVA":
            path = find_java_directory()
            print(f"{Fore.GREEN}JAVA Path: {path}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{package_name} is already installed.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}{package_name} is already installed.{Style.RESET_ALL}")
        return True
    # try to update the package if the user chooses to
    if installed_version is not None and not is_installed_result:
        update_choice = (
            input(
                f"{Fore.YELLOW}{package_name} is below the required minimum version {min_version}. Do you want to update it? (yes/no): {Style.RESET_ALL}"
            )
            .strip()
            .lower()
        )
        if update_choice in {"yes", "y"}:
            if update_or_install_package(
                    package_name, update_commands
            ):
                print(f"{Fore.GREEN}{package_name} has been updated to the latest version.{Style.RESET_ALL}")
                return True
        else:
            print(f"{Fore.RED}Operation canceled. Please update {package_name} and try again.{Style.RESET_ALL}")
            return False  # Return failure status
    print(
        f"{Fore.YELLOW}{package_name} is not installed. Attempting installation...{Style.RESET_ALL}"
    )

    if update_or_install_package(package_name, install_commands):
        if package_name == "Appium":
            appium_driver_list_output = execute_command("appium driver list")
            if appium_driver_list_output:
                print(appium_driver_list_output)

                install_appium_driver = (
                    input(f"{Fore.YELLOW}Do you want to install 'appium driver'? (yes/no): {Style.RESET_ALL}")
                    .strip()
                    .lower()
                )
                if install_appium_driver in {"yes", "y"}:
                    print("Installing 'appium driver'...")
                    subprocess.run(
                        install_commands.get("appium driver", ""),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True,
                        shell=True,
                    )
                    print(f"{Fore.GREEN}'appium driver' has been successfully installed.{Style.RESET_ALL}")

                    # Ask the user to choose sub-packages to install
                    print(f"Available sub-packages for {package_name}:")
                    for i, sub_package in enumerate(sub_packages, start=1):
                        print(f"{i}. {sub_package['name']}")

                        while True:
                            try:
                                user_choice = input(
                                    f"{Fore.YELLOW}Choose a sub-package to install (1-{len(sub_packages)}) or 'exit' to finish: {Style.RESET_ALL}"
                                ).strip()
                                if user_choice.lower() == "exit":
                                    break

                                user_choice = int(user_choice)
                                if 1 <= user_choice <= len(sub_packages):
                                    selected_sub_package = sub_packages[user_choice - 1]
                                    sub_package_name = selected_sub_package["name"]
                                    sub_package_install_command = (
                                        selected_sub_package.get("install_command")
                                    )

                                    if sub_package_install_command:
                                        print(f"Installing {sub_package_name}...")
                                        if update_or_install_package(
                                                sub_package_name,
                                                sub_package_install_command,
                                        ):
                                            print(
                                                f"{Fore.GREEN}{sub_package_name} has been successfully installed.{Style.RESET_ALL}"
                                            )
                                        else:
                                            print(
                                                f"{Fore.RED}Failed to install {sub_package_name}.{Style.RESET_ALL}"
                                            )
                                    else:
                                        print(
                                            f"No install command found for {sub_package_name}."
                                        )
                                else:
                                    print(
                                        f"{Fore.LIGHTRED_EX}Invalid choice. Please enter a valid number or 'exit' to finish.{Style.RESET_ALL}"
                                    )
                            except (ValueError, IndexError):
                                print(
                                    f"{Fore.LIGHTRED_EX}Invalid input. Please enter a number or 'exit' to finish.{Style.RESET_ALL}"
                                )
                    else:
                        print("Failed to install 'appium driver'.")

        return True

    print(f"{Fore.RED}Failed to install or update {package_name} ...{Style.RESET_ALL}")
    return False


def set_environment_permanently(variable_name, value):
    system_platform = platform.system().lower()
    if system_platform == "linux":
        # Linux
        with open(os.path.expanduser("~/.bashrc"), "a") as bashrc_file:
            bashrc_file.write(f'export {variable_name}="{value}"\n')
    elif system_platform == "windows":
        # Windows
        os.system(f'setx {variable_name} "{value}"')
    elif system_platform == "darwin":
        # Mac (macOS)
        print(f"{Fore.RED}Mac variable set support not available, please set manually.{Style.RESET_ALL}")
    else:
        print("Unsupported operating system")


def set_environment_variable_if_not_set(variable_name, finder_function):
    value = os.environ.get(variable_name)
    if value is None:  # Check if the variable is not already set
        try:
            value = finder_function()
            if value:
                os.environ[variable_name] = value
                print(f"{variable_name} set to: {value} (temporary)")
                set_environment_permanently(variable_name, value)
                print(f"{variable_name} set permanently.")
            else:
                print(f"{variable_name} not found.")
        except EnvironmentError as e:
            print(f"Error: {e}")
    else:
        print(f"{Fore.GREEN}{variable_name} is already set to: {value}{Style.RESET_ALL}")


def check_android_sdk_paths(android_home):
    android_sdk_paths = [
        os.path.join(android_home, "platform-tools"),
        # Add more paths as needed
    ]

    for path in android_sdk_paths:
        print(f"{Fore.GREEN}Android SDK Paths: {path}{Style.RESET_ALL}")
        if not os.path.exists(path):
            raise EnvironmentError(f"Android SDK path not found: {path}")


def load_packages_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            packages = json.load(file)
        return packages
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []


def log_error(package_name, error_message):
    # Create a log directory if it doesn't exist
    log_dir = "installation_logs"
    os.makedirs(log_dir, exist_ok=True)

    # Define the log file path
    log_file = os.path.join(log_dir, f"{package_name}_install_error.log")

    # Write the error message to the log file
    with open(log_file, "w") as log:
        log.write(error_message)


def check_and_install_dependency(package_file_path):
    system_platform = platform.system()
    print(f"You're using {Fore.GREEN}{system_platform}{Style.RESET_ALL}")
    packages_to_install_or_update = load_packages_from_file(package_file_path)

    if not packages_to_install_or_update:
        print("No packages found in the file.")
        return
    total_packages = len(packages_to_install_or_update)

    # Create a tqdm progress bar
    progress_bar = tqdm(
        packages_to_install_or_update,
        total=total_packages,
        ncols=100,  # Adjust the width of the progress bar as needed
        ascii=True,  # Use ASCII characters for the progress bar
        dynamic_ncols=True,  # Allow dynamic resizing of the progress bar
    )

    for package_details in progress_bar:
        print()
        success = check_and_install_or_update(package_details)

        if not success:
            print(
                f"{Fore.RED}Failed to install/update {package_details['name']}. See Installation Logs. Aborting further execution.{Style.RESET_ALL}"
            )
            return

    # Finish the progress bar
    progress_bar.close()
    set_environment_variable_if_not_set("JAVA_HOME", find_java_directory())
    set_environment_variable_if_not_set("ANDROID_HOME", find_sdk_directory)
    android_home = os.environ.get("ANDROID_HOME")
    if android_home:
        check_android_sdk_paths(android_home)
    subprocess.run(
        ["appium-doctor"],
        check=True,
        shell=True,
    )


# Call the function to check and install or update the environment
if __name__ == "__main__":
    check_and_install_dependency("packages.json")
