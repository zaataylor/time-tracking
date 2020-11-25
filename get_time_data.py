import os
import time
import json

import requests

BASE_ENDPOINT = 'https://api.clockify.me/api/v1/'
USER_ENDPOINT = BASE_ENDPOINT + 'user'
API_KEY = os.getenv('CLOCKIFY_API_KEY')
if API_KEY is None:
    exit('Error: API key is None')
X_API_HEADER = {'X-Api-Key': API_KEY}

# Get information for currently logged in user GET /user
r = requests.get(USER_ENDPOINT, headers=X_API_HEADER)
response = r.json()
user_id = active_workspace = None
try:
    user_id = response['id']
    workspace_id = response['activeWorkspace']
except KeyError:
    raise

# Get project IDs and names
# GET /workspaces/{workspaceId}/projects
projects = {}
url = BASE_ENDPOINT + '/workspaces/{}/projects'.format(workspace_id)
r = requests.get(url, headers=X_API_HEADER)
response = r.json()
for project in response:
  projects[project['id']] = project['name']

# Get task IDs and names
# GET /workspaces/{workspaceId}/projects/{projectId}/tasks
tasks = {}
for project_id in projects.keys():
    url = BASE_ENDPOINT + '/workspaces/{}/projects/{}/tasks'.format(workspace_id, project_id)
    r = requests.get(url, headers=X_API_HEADER)
    response = r.json()
    project_tasks = {}
    for task in response:
        project_tasks[task['id']] = task['name']
    tasks.update(project_tasks)
    project_name = projects[project_id]
    # projects[proj_id] -> [str: project_name, dict(key: task_id, value: task_name)]
    projects[project_id] = [project_name, project_tasks]
    time.sleep(0.2)
# Write the project + task information to file
p = open('projects.json', mode='w')
json.dump(projects, p)
p.close()
tf = open('tasks.json', mode='w')
json.dump(tasks, tf)

# Get JSON data containing the time entries
# GET /workspaces/{workspaceId}/user/{user_id}/time-entries
url = BASE_ENDPOINT + '/workspaces/{}/user/{}/time-entries'.format(workspace_id, user_id)
# I have 2853 time entries. At 50 entries a page, that's 58 pages total
# Iterate over these page numbers, passing them in as query parameters
# What format would be easiest to visualize? What parts of the data do I actually need?
data = []
for pagenum in range(1, 59):
    newurl = url + '?page={}'.format(pagenum)
    r = requests.get(newurl, headers=X_API_HEADER)
    response = r.json()
    for entry in response:
        data.append(entry)
    time.sleep(0.5)
d = open('data.json', mode='w')
json.dump(data, d)
d.close()