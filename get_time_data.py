import os
import time
import json
import math
from typing import Dict, Tuple, List

import requests

BASE_ENDPOINT = 'https://api.clockify.me/api/v1/'
USER_ENDPOINT = BASE_ENDPOINT + 'user'
API_KEY = os.getenv('CLOCKIFY_API_KEY')
if API_KEY is None:
    exit('Error: API key is None')
X_API_HEADER = {'X-Api-Key': API_KEY}
DEFAULT_ENTRIES_PER_PAGE = 50

# Get information for currently logged in user GET /user


def get_user_info() -> Tuple:
    r = requests.get(USER_ENDPOINT, headers=X_API_HEADER)
    response = r.json()
    user_id = workspace_id = None
    try:
        user_id = response['id']
        workspace_id = response['activeWorkspace']
        return (user_id, workspace_id)
    except KeyError:
        raise

# Get task IDs and names
# GET /workspaces/{workspaceId}/projects/{projectId}/tasks


def get_tasks_by_project_id(workspace_id: str, project_id: str) -> Dict:
    tasks = {}
    url = BASE_ENDPOINT + '/workspaces/{}/projects/{}/tasks'.format(
        workspace_id, project_id)
    r = requests.get(url, headers=X_API_HEADER)
    response = r.json()
    for task in response:
        tasks[task['id']] = task['name']
    return tasks

# Get project IDs with names and associated tasks
# GET /workspaces/{workspaceId}/projects


def get_projects(workspace_id: str, delay: float = 0.2) -> Dict:
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

# Get time entries
# GET /workspaces/{workspaceId}/user/{userId}/time-entries


def get_time_entries(workspace_id: str, user_id: str,
                     maxpages: int, num_entries: int = 0, delay: float = 0.2) -> List:
    if num_entries != 0:
        # set maxpages based on the default number of results returned per page,
        # which is currently 50 (https://clockify.me/developers-api)
        maxpages = int(math.ceil(num_entries / DEFAULT_ENTRIES_PER_PAGE))

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


def dump_data(data, filename: str) -> None:
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
