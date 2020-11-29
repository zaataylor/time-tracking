import os
import time
import json
import math
from typing import Dict, Tuple, List, Any

import requests

BASE_ENDPOINT = 'https://api.clockify.me/api/v1/'
USER_ENDPOINT = BASE_ENDPOINT + 'user'

API_KEY = os.getenv('CLOCKIFY_API_KEY')
if API_KEY is None:
    exit('Error: API key is None')
# required header for all API requests
X_API_HEADER = {'X-Api-Key': API_KEY}

# Check https://clockify.me/developers-api, in the section
# about time entry request parameters
ENTRIES_PER_PAGE = 50

def get_user_info() -> Tuple:
    """Get user ID and workspace ID for currently logged in user.
    
    This function returns the user ID and workspace ID for
    the currently logged in Clockify user.

    Parameters
    ----------
    `None`

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
    r = requests.get(USER_ENDPOINT, headers=X_API_HEADER)
    response = r.json()
    user_id = workspace_id = None
    try:
        user_id = response['id']
        workspace_id = response['activeWorkspace']
        return (user_id, workspace_id)
    except KeyError:
        raise

def get_tasks_by_project_id(workspace_id: str, project_id: str) -> Dict:
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
    r = requests.get(url, headers=X_API_HEADER)
    response = r.json()
    for task in response:
        tasks[task['id']] = task['name']
    return tasks

def get_projects(workspace_id: str, delay: float = 0.2) -> Dict:
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
    projects = {}
    url = BASE_ENDPOINT + '/workspaces/{}/projects'.format(workspace_id)
    r = requests.get(url, headers=X_API_HEADER)
    response = r.json()
    for project in response:
        project_id = project['id']
        project_name = project['name']
        tasks = get_tasks_by_project_id(workspace_id, project_id)
        projects[project_id] = [project_name, tasks]
        time.sleep(delay)
    return projects

def get_time_entries(workspace_id: str, user_id: str,
                     maxpages: int, num_entries: int = 0, delay: float = 0.2) -> List:
    """Get the time entries for a specific user in a specific workspace.
    
    This function returns a list of some (or all) of the time entries
    corresponding to a specific user ID and a specific workspace ID.

    Currently, Clockify does not have an API for GETting the total number of
    entries created by a particular user, but this information is displayed at
    the bottom of the time tracker UI. If you want to get all of the entries
    corresponding to a given user, you can pass in an arbitrarily high
    value for `maxpages` (not recommended) or get the number of entries from
    looking at the UI and pass this in as `num_entries`, then use a dummy value
    for `maxpages`. Another alternative is to get the number of entries, `x`,
    from the UI, then let `maxpages` equal `int(math.ceil(x / ENTRIES_PER_PAGE))`,
    where `ENTRIES_PER_PAGE` is the default number of entries per page returned
    by the Clockify API (currently 50).

    Parameters
    ----------
    `workspace_id`: `str`\n
    The ID of the workspace to pull time entries from.

    `user_id`: `str`\n
    The ID of the user in the workspace to pull time entries from.

    `maxpages`: `int`\n
    The maximum number of contiguous pages to request from the API.

    `num_entries`: `int`
    An optional parameter indicating the number of entries, and thus, the\n
    number of pages, to request from the API. Explanation: Since the\n
    default number of entries per page is 50, per \n
    (https://clockify.me/developers-api), the value\n
    that `num_entries` takes on is really a proxy for how many pages to\n
    request. If `num_entries` is specified, the number of pages is\n
    calculated by taking `math.ceil(num_entries / 50)`.

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
    if num_entries != 0:
        maxpages = int(math.ceil(num_entries / ENTRIES_PER_PAGE))

    url = BASE_ENDPOINT + \
        '/workspaces/{}/user/{}/time-entries'.format(workspace_id, user_id)
    entries = []
    for page in range(1, maxpages + 1):
        newurl = url + '?page={}'.format(page)
        r = requests.get(newurl, headers=X_API_HEADER)
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
    user_id, workspace_id = get_user_info()
    projects = get_projects(workspace_id)
    time_entries = get_time_entries(workspace_id, user_id, 58)

    dump_data(projects, 'projects.json')
    tasks = {}
    for _, tasks_dict in projects.values():
        for k, v in tasks_dict.items():
            tasks[k] = v
    dump_data(tasks, 'tasks.json')
    dump_data(time_entries, 'data.json')
