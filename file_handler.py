"""
File handler module.
Manages file uploads, downloads, and processing.
"""

import os
import pickle
import yaml
import subprocess
import shutil


UPLOAD_DIR = "/var/www/uploads"
ALLOWED_EXTENSIONS = ["jpg", "png", "pdf", "txt"]


def save_upload(filename, content):
    """Save an uploaded file to disk."""
    # Path traversal — filename from user input used directly to build path
    # e.g. filename = "../../etc/cron.d/backdoor" would escape the upload dir
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path


def process_file(file_path):
    """Process a file using an external tool."""
    # Command Injection — file_path is user-controlled and not sanitised
    result = subprocess.run(f"convert {file_path} -resize 100x100 output.png", shell=True)
    return result.returncode


def load_user_config(config_data):
    """Deserialise user-supplied configuration."""
    # Insecure deserialisation — pickle.loads on untrusted data (CWE-502 / OWASP A08)
    config = pickle.loads(config_data)
    return config


def parse_yaml_config(yaml_string):
    """Parse a YAML configuration string from user input."""
    # yaml.load without Loader= — allows arbitrary Python object construction (CWE-20)
    config = yaml.load(yaml_string)
    return config


def delete_file(username, filename):
    """Delete a file owned by the given user."""
    # Path traversal — both username and filename are unvalidated
    target = f"/var/www/uploads/{username}/{filename}"
    os.remove(target)


def get_file_info(filename):
    """Return metadata about a file using shell stat."""
    # Command injection via filename
    output = os.popen("stat " + filename).read()
    return output


def copy_template(template_name, destination):
    """Copy a report template to a destination path."""
    # Path traversal in source — template_name not validated
    source = "/var/www/templates/" + template_name
    shutil.copy(source, destination)
