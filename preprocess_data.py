import json
import csv
from typing import List

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60

def calculate_duration(duration: str) -> int:
    """Parse Clockify time entry duration string into total number of seconds.

    This function parses a string of the form 'PT{num}H{num}M{num}S'
    representing a time duration and returns the total time duration
    in seconds. For example, for the string 'PT1H3M6S' representing a time
    duration of 1 hour, 3 minutes, and 6 seconds, the function would
    return 3786, the total number of seconds in that duration.

    The function expects at least of 'H', 'M', or 'S' to be in the
    duration string, and will throw a ValueError if not.

    Parameters
    -----------
    `duration` : str
        A string representing the time duration.

    Returns
    -------
    `int`
        The total time, in seconds, of the time duration.

    Raises
    ------
    `ValueError`
        If none of 'H', 'M', or 'S' were found in `duration` string.
    """
    # remove 'PT' from duration string
    duration = duration[2:]

    # get indices of 'H', 'M', and 'S' in the duration string
    H_idx = duration.find('H')
    M_idx = duration.find('M')
    S_idx = duration.find('S')

    H_idx_found = True if H_idx >= 0 else False
    M_idx_found = True if M_idx >= 0 else False
    S_idx_found = True if S_idx >= 0 else False

    hms_found = [H_idx_found, M_idx_found, S_idx_found]
    # none of 'H', 'M', or 'S' were found
    if (H_idx == -1) and (M_idx == -1) and (S_idx == -1):
        raise ValueError(
            'Time duration must include at least one of H, M, or S, but none of these were found')

    # extract numerical components of time duration string
    duration = duration.replace('H', '|')
    duration = duration.replace('M', '|')
    duration = duration.replace('S', '|')
    duration = duration.split('|')
    duration = list(filter(None, duration))
    duration = [int(v) for v in duration]

    # calculate total time in seconds
    # there are 7 cases: [H] only, [M] only, [S] only,
    # [H,M] only, [H,S] only, [M,S] only, [H,M,S]
    total = 0
    # [H,M,S] case
    if len(duration) == 3:
        total = duration[0]*SECONDS_IN_HOUR + \
            duration[1]*SECONDS_IN_MINUTE + duration[2]
    # the other 6 cases
    else:
        # idea: while iterating over boolean values in hms_found list, 
        # select rightmost unused value in duration list. Then, based
        # on index in hms_found, add the appropriate multiple of 
        # duration[i] (corresponding to hours, minutes, or seconds)
        # to total number of seconds
        i = 0
        for idx, found in enumerate(hms_found):
            if not found:
                continue
            elif idx == 0:
                total += duration[i]*SECONDS_IN_HOUR
            elif idx == 1:
                total += duration[i]*SECONDS_IN_MINUTE
            else:
                total += duration[i]
            i += 1
    return total

def get_date(isoformattime: str):
    """Extract {YYYY-MM-DD} from ISO 8601 formatted time string."""
    T_index = isoformattime.find('T')
    if T_index == -1:
        raise ValueError('Improperly formatted time string given.')
    date = isoformattime[0: T_index]
    return date

def preprocess_data(projects_file: str, tasks_file: str, data_file: str) -> List:
    """Preprocess raw Clockify API time entry data and extract relevant fields.

    This function extracts the task ID, task name, project ID, project name,
    start time (UTC), end time (UTC), and task duration (in seconds) for
    each time entry.

    Parameters
    -----------
    `projects_file` : str
        Name of the file that holds the dictionary with the following mapping:
        project ID to [project name, dictionary of tasks], reflecting the
        hierarchical nature of the Project-Task relationship. The dictionary of
        tasks maps task ID to task name.
    `tasks_file` : str
        This file contains a dictionary mapping task ID to task name.
    `data_file` : str
        The raw data of time entries from the Clockify API.

    Returns
    --------
    `List`
        A list of dictionaries, each of which contains the fields extracted
        from a time entry.

    Raises
    -------
    `KeyError`
        If the 'duration' key in the raw time entry dict obtained from `data_file`
        is not present.
    """

    p = open(projects_file, mode='r')
    t = open(tasks_file, mode='r')
    d = open(data_file, mode='r')
    projects, tasks, data = json.load(p), json.load(t), json.load(d)
    processed_items = []
    for datum in data:
        proc_item = {}
        # some time entries are only labeled with a project, but not a specific task
        if datum['taskId'] is None:
            proc_item['task_id'] = None
            proc_item['task_name'] = None
        else:
            proc_item['task_id'] = datum['taskId']
            proc_item['task_name'] = tasks[datum['taskId']]

        proc_item['project_id'] = datum['projectId']
        proc_item['project_name'] = projects[datum['projectId']][0]

        proc_item['description'] = str.lower(datum['description'])

        start_time_utc = datum['timeInterval']['start']
        proc_item['start_time_utc'] = start_time_utc
        proc_item['start_date_utc'] = get_date(start_time_utc)

        end_time_utc = datum['timeInterval']['end']
        proc_item['end_time_utc'] = end_time_utc
        proc_item['end_date_utc'] = get_date(end_time_utc)
        try:
            proc_item['duration_seconds'] = calculate_duration(
                datum['timeInterval']['duration'])
        except KeyError:
            raise

        processed_items.append(proc_item)
    return processed_items

def export_to_csv(preproc_data_file: str, preproc_data: List):
    """Export preprocessed data to CSV."""
    with open(preproc_data_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow(['Project Name', 'Project ID', 'Task Name',
                            'Task ID', 'Description', 'Start Time (UTC)',
                            'Start Date (UTC)', 'End Time (UTC)',
                            'End Date (UTC)','Duration (Seconds)'])
        for pi in preproc_data:
            csvwriter.writerow([pi['project_name'], pi['project_id'], pi['task_name'],
                                pi['task_id'], pi['description'], pi['start_time_utc'],
                                pi['start_date_utc'],  pi['end_time_utc'], pi['end_date_utc'],
                                pi['duration_seconds']])

def export_to_json(preproc_data_file: str, preproc_data: List):
    """Export preprocessed data to JSON."""
    prpd = open(preproc_data_file, 'w')
    json.dump(preproc_data, prpd)

if __name__ == '__main__':
    projects_file = 'projects.json'
    tasks_file = 'tasks.json'
    data_file = 'data.json'
    preproc_data_file = 'preprocessed_data'

    preproc_data = preprocess_data(projects_file, tasks_file, data_file)
    export_to_csv(preproc_data_file + '.csv', preproc_data)
    export_to_json(preproc_data_file + '.json', preproc_data)

