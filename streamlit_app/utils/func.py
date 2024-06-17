import os
import re
from urllib.parse import urlparse

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))



### Below for app.py

def list_directories(directory):
    """
    List all directories under the given directory.

    Parameters:
    directory (str): The path to the directory.

    Returns:
    list: A list of directory names under the given directory.
    """
    try:
        # Get a list of all entries in the directory
        entries = os.listdir(directory)
        
        # Filter out the directories
        directories = [entry for entry in entries if os.path.isdir(os.path.join(directory, entry))]
        
        return directories
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


### Below for build_index.py

def make_valid_directory_name(name):
    """
    Sanitize a given name to be a valid Linux directory name.

    Parameters:
    name (str): The name to be sanitized.

    Returns:
    str: A valid Linux directory name.
    """
    # Define a pattern for invalid characters
    invalid_chars = re.compile(r'[<>:"/\\|?*]')
    
    # Replace invalid characters with an underscore
    sanitized_name = invalid_chars.sub('_', name)
    
    # Trim whitespace from the start and end of the name
    sanitized_name = sanitized_name.strip()
    
    # Replace multiple consecutive whitespace characters with a single underscore
    sanitized_name = re.sub(r'\s+', '_', sanitized_name)
    
    # Ensure the name is not empty
    if not sanitized_name:
        sanitized_name = 'default_directory'
    
    # Ensure the name does not start with a hyphen
    if sanitized_name.startswith('-'):
        sanitized_name = '_' + sanitized_name[1:]
    
    return sanitized_name

def is_valid_url(url):
    """
    Check if a given URL is valid.

    Parameters:
    url (str): The URL to check.

    Returns:
    bool: True if the URL is valid, False otherwise.
    """
    # Regular expression for validating a URL
    regex = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'(([a-zA-Z0-9_\-]+\.)+[a-zA-Z]{2,6})'  # domain name
        r'(:[0-9]{1,5})?'  # optional port
        r'(/.*)?$', re.IGNORECASE)  # resource path

    if re.match(regex, url):
        parsed_url = urlparse(url)
        return all([parsed_url.scheme, parsed_url.netloc])
    return False

def check_urls(text):
    """
    Check if all URLs in a given multiline text are valid.

    Parameters:
    text (str): The multiline text containing URLs.

    Returns:
    bool: True if all URLs are valid, False otherwise.
    """
    # Split the text into lines
    lines = text.strip().split('\n')

    # Check each line to see if it is a valid URL
    for line in lines:
        url = line.strip()
        logging.info(f"> url: {url}")
        if not is_valid_url(url):
            logging.warn(f"!!!!!! Invalid URL: {url}")
            return False
    return True

def count_urls(text):
    """
    Count the number of URLs in a given multiline text.

    Parameters:
    text (str): The multiline text containing URLs.

    Returns:
    int: The number of URLs found in the text.
    """
    logging.info(f">>> count_urls('{text}')")

    # Regular expression to matchf URLs
    url_pattern = re.compile(
        r'https?://'  # http:// or https://
        r'(\w+\.)+'  # Domain name prefix
        r'[a-z]{2,6}'  # Domain name suffix
        r'(:[0-9]{1,5})?'  # Optional port
        r'(/[^\s]*)?', re.IGNORECASE)  # Optional path

    # Find all matches in the text
    urls = url_pattern.findall(text)

    # Return the number of URLs found
    return len(urls)

def get_subdirectories(directory):
    subdirs = []
    # Walk through the directory tree
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            # Join the root with the directory name to get the full path
            full_path = os.path.join(root, dir_name)
            subdirs.append(full_path)
            # subdirs.append(full_path.replace(directory, "Documents"))
    return subdirs

def get_files_with_extensions(directory, extensions):
    # Ensure extensions are in lowercase
    extensions = [ext.lower() for ext in extensions]
    
    files_data = []
    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if the file ends with any of the specified extensions
            if any(file.lower().endswith(f'.{ext}') for ext in extensions):
                # Add the full path of the matching file to the list
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path) / 1024 # Get file size in KiB
                files_data.append((file_path.replace(directory,""), file_size))
    return files_data

def get_total_size_mib(directory):
    """
    Calculate the total size of all files in the given directory in MiB.

    Parameters:
    directory (str): The path to the directory.

    Returns:
    float: The total size of all files in MiB.
    """
    total_size_bytes = 0

    # Walk through the directory
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            # Get the full file path
            file_path = os.path.join(dirpath, filename)
            
            # Check if it's a file (not a directory)
            if os.path.isfile(file_path):
                # Add the file size to the total size
                total_size_bytes += os.path.getsize(file_path)
    
    # Convert bytes to MiB
    total_size_mib = total_size_bytes / (1024 ** 2)
    
    return total_size_mib

def extract_urllist(multiline_text):
    """
    Convert a multiline text that contains a URL per line into a list of URLs.

    Parameters:
    multiline_text (str): The input multiline text.

    Returns:
    list: A list of URL strings.
    """
    # Split the multiline text into individual lines
    lines = multiline_text.strip().split('\n')
    
    # Remove any leading/trailing whitespace from each line
    urllist = [line.strip() for line in lines if line.strip()]
    
    return urllist