import os
import requests
import tarfile
import zipfile
import shutil
import subprocess
import tempfile
import venv
import logging
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename

from config import PACKAGE_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def download_package_file(package_name, version=None, use_sdist=True):

    pypi_url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(pypi_url)
    response.raise_for_status()

    package_info = response.json()
    version = version or package_info['info']['version']

    if version not in package_info['releases']:
        raise Exception(f"Version {version} for package {package_name} not found.")

    package_files = package_info['releases'][version]
    current_tags = set(sys_tags())

    selected_file = None

    if use_sdist:
        # Select the first available source distribution
        for file in package_files:
            if file['packagetype'] == 'sdist':
                selected_file = file
                logging.info(f"Selected source distribution: {file['filename']}")
                break
    else:
        # Find a compatible wheel
        for file in package_files:
            if file['packagetype'] == 'bdist_wheel':
                try:
                    _, _, _, wheel_tags = parse_wheel_filename(file['filename'])
                    wheel_tags_set = set(wheel_tags)
                    if current_tags.intersection(wheel_tags_set):
                        logging.info(f"Selected wheel: {file['filename']}")
                        selected_file = file
                        break
                except Exception as e:
                    logging.debug(f"Failed to parse wheel {file['filename']}: {e}")
                    continue

    download_url = selected_file['url']
    filename = selected_file['filename']
    logging.info(f"Downloading {package_name}=={version} from {download_url}")

    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, filename)
    with requests.get(download_url, stream=True) as r, open(file_path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)

    return file_path, temp_dir

def extract_archive(archive_path, extract_to):
    if archive_path.endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tar.xz', '.tar')):
        with tarfile.open(archive_path, 'r:*') as tar:
            tar.extractall(path=extract_to)
    elif archive_path.endswith(('.zip', '.whl')):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(path=extract_to)
    else:
        raise Exception(f"Unsupported archive format: {archive_path}")

def create_virtualenv(env_dir):
    logging.info(f"Creating virtual environment at {env_dir}")
    venv.EnvBuilder(with_pip=True).create(env_dir)

def install_packages(env_python, packages, cwd=None, verbose=False, extra_args=None):
    if not packages:
        return
    command = [env_python, '-m', 'pip', 'install', '--upgrade'] + packages
    if verbose:
        command.append('--verbose')
    if extra_args:
        command += extra_args
    subprocess.check_call(command, cwd=cwd)

def verify_installation(package_name, env_python):
    version = subprocess.check_output(
        [env_python, '-c', f'import {package_name}; print({package_name}.__version__)'],
        universal_newlines=True
    ).strip()
    logging.info(f"Package {package_name} successfully installed. Version: {version}")

def run_tests_with_coverage(config, package_dir, coverage_dir, env_python):
    logging.info(f"Installing test dependencies: {config.get('test_dependencies')}")
    install_packages(env_python, config['test_dependencies'], cwd=package_dir, verbose=True)
    env = os.environ.copy()
    env.update(config.get('additional_env', {}))

    logging.info("Running tests with coverage...")
    subprocess.check_call(config['test_command'], cwd=package_dir, env=env)

    xml_src = os.path.join(package_dir, 'coverage.xml')
    xml_dest = os.path.join(coverage_dir, 'coverage.xml')
    
    shutil.move(xml_src, xml_dest)
    logging.info(f"Moved coverage.xml to {xml_dest}")
    
    html_src = os.path.join(package_dir, 'coverage_html')
    html_dest = os.path.join(coverage_dir, 'coverage_html')
    if os.path.exists(html_dest):
        shutil.rmtree(html_dest)
        logging.info(f"Removed existing coverage_html at {html_dest}")
    shutil.move(html_src, html_dest)
    logging.info(f"Moved coverage_html to {html_dest}")

def process_package(package_name, version=None, coverage_reports_base_dir='coverage_reports'):

    config = PACKAGE_CONFIG.get(package_name)

    temp_dir = None
    try:
        file_path, temp_dir = download_package_file(package_name, version, use_sdist=config['use_sdist'])

        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        extract_archive(file_path, extract_dir)

        venv_dir = os.path.join(temp_dir, 'venv')
        create_virtualenv(venv_dir)
        env_python = os.path.join(venv_dir, 'bin', 'python') # os.path.join(venv_dir, 'Scripts', 'python') if os.name == 'nt' else os.path.join(venv_dir, 'bin', 'python')

        # if config['build_system'] == 'setuptools':
        #     logging.info("Using setuptools. No additional system dependencies required.")
        # else:
        #     raise Exception(f"Unsupported build system: {config['build_system']}")

        logging.info("Upgrading pip...")
        install_packages(env_python, ['pip'], cwd=None, verbose=True)

        if config['dependencies']:
            logging.info(f"Installing package dependencies: {config['dependencies']}")
            install_packages(env_python, config['dependencies'], cwd=None, verbose=True)

        if config['use_sdist']:
            extracted_subdirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
            if not extracted_subdirs:
                raise Exception("No directory found after extraction.")
            package_dir = os.path.join(extract_dir, extracted_subdirs[0])
            logging.info(f"Installing package from source directory: {package_dir}")

            try:
                subprocess.check_call(
                    [env_python, '-c', 'import setuptools'],
                    cwd=package_dir
                )
                logging.info("'setuptools' module is available.")
            except subprocess.CalledProcessError:
                logging.error("'setuptools' module is not available. Build dependencies may be missing.")
                raise

            install_packages(
                env_python,
                ['.'],
                cwd=package_dir,
                verbose=True
            )
        else:
            logging.info(f"Installing package from wheel: {file_path}")
            install_packages(
                env_python,
                [file_path],
                cwd=extract_dir,
                verbose=True
            )
            package_dir = extract_dir

        verify_installation(package_name, env_python)

        coverage_dir = os.path.abspath(os.path.join(os.getcwd(), coverage_reports_base_dir, package_name))
        os.makedirs(coverage_dir, exist_ok=True)

        run_tests_with_coverage(config, package_dir, coverage_dir, env_python)

        logging.info(f"Package {package_name} processed successfully. Coverage report available at {coverage_dir}/coverage_html/index.html")
    except Exception as e:
        logging.error(f"Error processing package {package_name}: {e}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info(f"Cleaned up temporary directory: {temp_dir}")

def main():
    coverage_reports_base_dir = 'coverage_reports'
    os.makedirs(coverage_reports_base_dir, exist_ok=True)

    packages = [
        'requests',
        # 'numpy',
        # 'pandas'
    ]

    for pkg in packages:
        logging.info(f"\n=== Processing package: {pkg} ===")
        process_package(pkg)

if __name__ == "__main__":
    main()
