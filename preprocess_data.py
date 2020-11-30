import json
import csv
from typing import List
import argparse

from get_time_data import dump_data

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60

def main():
    """Runs the program."""
    # Parse command-line args
    parser = argparse.ArgumentParser(prog='preprocess_data.py',
                                    description='Preprocess Clockify API data from files in an opinionated fashion.',
                                    epilog='Have fun preprocessing! :)')
    parser.add_argument('-p',
                        '--projects-file',
                        type=str,
                        dest='proj_file',
                        help='The name of the file to get projects information from. Defaults\n' +
                        'to \'projects.json\' if not specified.',
                        required=False)
    parser.add_argument('-t',
                        '--tasks-file',
                        type=str,
                        dest='tasks_file',
                        help='The name of the file to get tasks information from. Defaults\n' +
                        'to \'tasks.json\' if not specified.',
                        required=False)
    parser.add_argument('-e',
                        '--entries-file',
                        type=str,
                        dest='entries_file',
                        help='The name of the file to get time entry data from. Defaults\n' +
                        'to \'entries.json\' if not specified.',
                        required=False)
    parser.add_argument('-d',
                        '--data-file',
                        type=str,
                        dest='proc_data_file',
                        help='The name of the file that will hold the preprocessed data.\n' +
                        'Defaults to \'preprocessed_data.json\'.')
    parser.add_argument('--csv',
                        dest='export_csv',
                        action='store_true',
                        help='Specify this flag to indicate that the data should also be\n' + 
                        'exported to CSV format. The CSV file will have the same name as\n' +
                        'the file specified by the -d/--data-file argument, or be named\n' +
                        '\'preprocessed_data.csv\' if that argument is not given.', 
                        default=False)
    args = parser.parse_args()
    proj_file = 'projects.json' if args.proj_file is None else args.proj_file
    tasks_file = 'tasks.json' if args.tasks_file is None else args.tasks_file
    entries_file = 'entries.json' if args.entries_file is None else args.entries_file

    preproc_data = preprocess_data(proj_file, tasks_file, entries_file)

    preproc_data_file = \
        'preprocessed_data.json' if args.proc_data_file is None else args.proc_data_file
    if args.export_csv:
        preproc_csv_file = preproc_data_file.split('.')[0] + '.csv'
        export_to_csv(preproc_csv_file, preproc_data)

    if not preproc_data_file.endswith('.json'):
        preproc_data_file += '.json'
    dump_data(preproc_data, preproc_data_file)

def calculate_duration(duration: str) -> int:
    """Parse Clockify time entry duration string into total number of seconds.

    This function parses a string of the form 'PT{num}H{num}M{num}S'
    representing a time duration and returns the total time duration
    in seconds. For example, for the string 'PT1H3M6S' representing a time
    duration of 1 hour, 3 minutes, and 6 seconds, the function would
    return 3786, the total number of seconds in that duration.

    The function expects at least one of 'H', 'M', or 'S' to be in the
    duration string, and raises a ValueError if not.

    Parameters
    -----------
    `duration` : `str`\n
    A string representing the time duration.

    Returns
    -------
    `int`\n
    The total time, in seconds, of the time duration.

    Raises
    ------
    `ValueError`\n
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
    # [H,M] only, [H,S] only, [M,S] only, and [H,M,S]
    total = 0
    # Idea: while iterating over boolean values in hms_found list, 
    # select leftmost unused value in duration list. Then, based
    # on index in hms_found, add the appropriate multiple of 
    # duration[i] (corresponding to hours, minutes, or seconds)
    # to the total number of seconds
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

def get_date(isoformattime: str) -> str:
    """Extract {YYYY-MM-DD} from ISO 8601 formatted time string.
    
    Parameters
    ----------
    `isoformattime`: `str`\n
    An ISO 8601 formatted time string.

    Returns
    -------
    `str`\n
    A string containing the date portion of the original time string.

    Raises
    ------
    `ValueError`\n
    If the 'T' prefacing the time part of the string is missing.
    """
    T_index = isoformattime.find('T')
    if T_index == -1:
        raise ValueError('Improperly formatted time string given.')
    date = isoformattime[0: T_index]
    return date

def preprocess_data(projects_file: str, tasks_file: str, entries_file: str) -> List:
    """Preprocess raw Clockify API time entry data and extract relevant fields.

    This function extracts the task ID, task name, project ID, project name,
    start time (UTC), end time (UTC), and task duration (in seconds) for
    each time entry.

    Parameters
    -----------
    `projects_file` : `str`\n
    Name of the file that holds the dictionary with the following mapping:
    project ID to [project name, dictionary of tasks], reflecting the
    hierarchical nature of the Project-Task relationship. The dictionary of
    tasks maps task ID to task name.

    `tasks_file` : `str`\n
    This file contains a dictionary mapping task ID to task name.

    `entries_file` : `str`\n
    The file containing raw time entry data from the Clockify API.

    Returns
    --------
    `List`\n
    A list of dictionaries, each of which contains fields extracted
    from a time entry.

    Raises
    -------
    `KeyError`\n
    If the 'duration' key in the raw time entry dict obtained from `data_file`
    is not present.
    """

    p = open(projects_file, mode='r')
    t = open(tasks_file, mode='r')
    d = open(entries_file, mode='r')
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

        # project ID and project name
        proc_item['project_id'] = datum['projectId']
        proc_item['project_name'] = projects[datum['projectId']][0]

        # lowercase all project descriptions
        proc_item['description'] = str.lower(datum['description'])

        # get UTC start time, and (separately) date
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

def export_to_csv(preproc_data_file: str, preproc_data: List) -> None:
    """Export preprocessed data to CSV.
    
    Parameters
    -----------
    `preproc_data_file`:`str`\n
    Name of the file to write preprocessed data to.

    `preproc_data`: `List`\n
    A list containing dictionaries representing preprocessed time entries.

    Returns:
    --------
    `None`

    Raises
    ------
    `None`
    """
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

if __name__ == '__main__':
    main()

