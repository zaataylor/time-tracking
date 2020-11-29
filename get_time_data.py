import os
import time
import json
import math
from typing import Dict, Tuple, List, Any
import argparse

import requests

BASE_ENDPOINT = 'https://api.clockify.me/api/v1/'
USER_ENDPOINT = BASE_ENDPOINT + 'user'

# Check https://clockify.me/developers-api, in the section
# about time entry request parameters
ENTRIES_PER_PAGE = 50
# Delay between API requests to avoid rate limiting
DEFAULT_DELAY = 0.2

def main():
    """Runs the program."""
    # Parse command-line args
    parser = argparse.ArgumentParser(prog='get_time_data.py',
                                    description='Get Clockify projects, tasks, and time entry data and write it to files.',
                                    epilog='Have fun tracking! :)')
    parser.add_argument('-a',
                        '--api-key',
                        type=str,
                        dest='api_key',
                        help='Your personal Clockify API key. If not specified here, then you must\n' + 
                        'have the CLOCKIFY_API_KEY environment variable set on your system.',
                        required=False)
    # This is cool! 
    # https://stackoverflow.com/questions/11154946/require-either-of-two-arguments-using-argparse
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--num-pages',
                        type=int,
                        dest='num_pages',
                        help='The number of (contiguous) pages to request from the Clockify API.')
    group.add_argument('--num-entries',
                        type=int,
                        dest='num_entries',
                        help='Lower bound on the number of entries to grab from the Clockify API.\n' + 
                        'If specified, this value will be used to calculate how many pages to grab\n' +
                        'from the Clockify API.')
    parser.add_argument('-p',
                        '--projects-file',
                        type=str,
                        dest='proj_file',
                        help='The name of the file to write projects information to. Defaults\n' +
                        'to \'projects.json\' if not specified.',
                        required=False)
    parser.add_argument('-t',
                        '--tasks-file',
                        type=str,
                        dest='tasks_file',
                        help='The name of the file to write tasks information to. Defaults\n' +
                        'to \'tasks.json\' if not specified.',
                        required=False)
    parser.add_argument('-e',
                        '--entries-file',
                        type=str,
                        dest='entries_file',
                        help='The name of the file to write time entry data to. Defaults\n' +
                        'to \'entries.json\' if not specified.',
                        required=False)
    parser.add_argument('-d',
                        '--delay',
                        type=float,
                        dest='delay',
                        help='Delay between subsequent calls to the Clockify API, in seconds.\n' +
                        'Default value is 0.2. Using a value less than this may cause the program\n' +
                        'to fail due to Clockify API rate limiting.',
                        required=False)
    args = parser.parse_args()

    api_key = args.api_key
    # use environment variable instead
    if api_key is None:
        api_key = os.getenv('CLOCKIFY_API_KEY')
        if api_key is None:
            exit('Error: API key is None. Add it to your environment variables\n' +
            'as CLOCKIFY_API_KEY or specify it with the -a / --api-key CLI option.')
    api_key_header = {'X-Api-Key': api_key}

    # Get entry, project, and task info
    req_delay = args.delay
    user_id, workspace_id = get_user_info(api_key_header)
    projects = get_projects(workspace_id, api_key_header, delay=req_delay)
    num_pages = args.num_pages
    num_entries = args.num_entries
    if num_pages is None:
        num_pages = int(math.ceil(num_entries / ENTRIES_PER_PAGE))
    time_entries = get_time_entries(workspace_id, user_id, num_pages,
                    api_key_header, delay=req_delay)

    # Write data to file
    proj_file = 'projects.json' if args.proj_file is None else args.proj_file
    tasks_file = 'tasks.json' if args.tasks_file is None else args.tasks_file
    entries_file = 'entries.json' if args.entries_file is None else args.entries_file
    dump_data(projects, proj_file)
    tasks = {}
    for _, tasks_dict in projects.values():
        for k, v in tasks_dict.items():
            tasks[k] = v
    dump_data(tasks, tasks_file)
    dump_data(time_entries, entries_file)

def get_user_info(api_key_header: Dict) -> Tuple:
    """Get user ID and workspace ID for currently logged in user.
    
    This function returns the user ID and workspace ID for
    the currently logged in Clockify user.

    Parameters
    ----------
    `api_key_header`: `Dict`\n
    Dict containing the special header required by the Clockify API.

    Returns
    -------
    `Tuple`\n
    A tuple `t` such that `t[0]` is the user ID and `t[1]`\n
    is the workspace ID

    Raises
    ------
    `KeyError`\n
    If the response from the Clockify API does not contain\n
    fields for 'id' and 'activeWorkspace', corresponding to the\n
    user ID and workspace ID, respectively.
    """
    r = requests.get(USER_ENDPOINT, headers=api_key_header)
    response = r.json()
    user_id = workspace_id = None
    try:
        user_id = response['id']
        workspace_id = response['activeWorkspace']
        return (user_id, workspace_id)
    except KeyError:
        raise

def get_tasks_by_project_id(workspace_id: str, project_id: str,
    api_key_header: Dict) -> Dict:
    """Get tasks associated with a given project ID and workspace ID.
    
    This function returns a dictionary of tasks corresponding to a given
    project ID and workspace ID.
    
    The dictionary has task IDs as keys and task names as values.
    
    Parameters
    -----------
    `workspace_id`: `str`\n
    The ID of the workspace the project is located in.

    `project_id`: `str`\n
    The ID of the project in the workspace

    `api_key_header`: `Dict`\n
    Dict containing the special header required by the Clockify API.

    Returns
    -------
    `Dict`\n
    A dictionary, `tasks`, as described above.

    Raises
    -------
    `None`
    """
    tasks = {}
    url = BASE_ENDPOINT + '/workspaces/{}/projects/{}/tasks'.format(
        workspace_id, project_id)
    r = requests.get(url, headers=api_key_header)
    response = r.json()
    for task in response:
        tasks[task['id']] = task['name']
    return tasks

def get_projects(workspace_id: str, api_key_header: Dict,
    delay=None) -> Dict:
    """Get project names, IDs, and associated tasks.
    
    The function returns information about the projects associated
    with a particular workspace in the form of a dictionary.

    For a given key `k` in the returned `projects` dictionary,
    `k` is the project ID, and the value at `projects[k]` is a
    list `v` such that `v[0]` is the project name associated
    with `k`, and `v[1]` is a dictionary of tasks for the
    particular project. This dictionary has task IDs as keys
    and task names as values.

    Thus, this dictionary retains the hierarchical structure
    of projects and tasks as they appear in Clockify.

    Parameters
    ----------
    `workspace_id`: `str`\n
    The ID of the workspace to get project information from.

    `api_key_header`: `Dict`\n
    Dict containing the special header required by the Clockify API.

    `delay`: `float`\n
    An optional parameter indicating the delay between requests\n
    made to the Clockify API. The default is 0.2 seconds to respect\n
    Clockify's rate limiting of 10 requests/second\n
    (https://clockify.me/developers-api).

    Returns
    -------
    `Dict`\n
    A dictionary matching the specifications described above.

    Raises
    ------
    `None`
    """
    if delay is None:
        delay = DEFAULT_DELAY
    projects = {}
    url = BASE_ENDPOINT + '/workspaces/{}/projects'.format(workspace_id)
    r = requests.get(url, headers=api_key_header)
    response = r.json()
    for project in response:
        project_id = project['id']
        project_name = project['name']
        tasks = get_tasks_by_project_id(workspace_id, project_id, api_key_header)
        projects[project_id] = [project_name, tasks]
        time.sleep(delay)
    return projects

def get_time_entries(workspace_id: str, user_id: str,
                     num_pages: int, api_key_header: Dict, 
                     delay=None) -> List:
    """Get the time entries for a specific user in a specific workspace.
    
    This function returns a list of some (or all) of the time entries
    corresponding to a specific user ID and a specific workspace ID.

    Currently, Clockify does not have an API for GETting the total number of
    entries created by a particular user, but this information is displayed at
    the bottom of the time tracker UI.

    Parameters
    ----------
    `workspace_id`: `str`\n
    The ID of the workspace to pull time entries from.

    `user_id`: `str`\n
    The ID of the user in the workspace to pull time entries from.

    `num_pages`: `int`\n
    The number of contiguous pages to request from the API, starting
    from the first page.

    `api_key_header`: `Dict`\n
    Dict containing the special header required by the Clockify API.

    `delay`: `float`\n
    An optional parameter indicating the delay between requests\n
    made to the Clockify API. The default is 0.2 seconds to respect\n
    Clockify's rate limiting of 10 requests/second\n
    (https://clockify.me/developers-api).

    Returns
    -------
    `List`\n
    A list of time entries, each of which is a `dict` with fields\n
    matching those described in the API documentation.
    """
    if delay is None:
        delay = DEFAULT_DELAY
    url = BASE_ENDPOINT + \
        '/workspaces/{}/user/{}/time-entries'.format(workspace_id, user_id)
    entries = []
    for page in range(1, num_pages + 1):
        newurl = url + '?page={}'.format(page)
        r = requests.get(newurl, headers=api_key_header)
        response = r.json()
        for entry in response:
            entries.append(entry)
        time.sleep(delay)
    return entries

def dump_data(data: Any, filename: str) -> None:
    """Dump data to a given filename.
    
    This function uses the `json.dump` function to dump
    data to a given filename. In this context, data will
    be either of `Dict` or `List` type.
    
    Parameters
    -----------
    `data`: `Any`\n
    The data to dump.
    
    `filename`: `str`\n
    The name of the file to dump the data to.
    
    Returns
    --------
    `None`
    
    Raises
    ------
    `None`
    """
    d = open(filename, mode='w')
    json.dump(data, d)
    d.close()

if __name__ == '__main__':
    main()
