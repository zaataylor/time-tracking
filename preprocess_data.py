import json
import csv

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60

def calculate_duration(duration: str) -> int:
    '''Parses a string of form PT*H*M*S to get number of seconds'''
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
        raise ValueError('Time duration must include at least one of H, M, or S, but none of these were found')

    # Extract numerical components of the time duration string
    duration = duration.replace('H', '|')
    duration = duration.replace('M', '|')
    duration = duration.replace('S', '|')
    duration = duration.split('|')
    duration = list(filter(None, duration))
    duration = [int(v) for v in duration]

    # Calculate total time in seconds
    # There are 7 cases: H only, M only, S only, H&M only, H&S only, M&S only, H&M&S
    total = 0
    if len(duration) == 3:
        total = duration[0]*SECONDS_IN_HOUR + duration[1]*SECONDS_IN_MINUTE + duration[2]
    else:
        # Idea: using boolean values in hms_found list, select rightmost unused value in
        # duration list. Then, based on index in hms_found, add the appropriate multiple of
        # duration[i] (corresponding to hours, minutes, or seconds) to total number of seconds
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

p = open('projects.json', mode='r')
t = open('tasks.json', mode='r')
d = open('data.json', mode='r')
projects, tasks, data = json.load(p), json.load(t), json.load(d)
processed_items = []
for datum in data:
    proc_item = {}
    if datum['taskId'] is None:
        proc_item['task_id'] = None
        proc_item['task_name'] = None
    else:
        proc_item['task_id'] = datum['taskId']
        proc_item['task_name'] = tasks[datum['taskId']]

    proc_item['project_id'] = datum['projectId']
    proc_item['project_name'] = projects[datum['projectId']][0]

    proc_item['description'] = datum['description']

    proc_item['start_time_utc'] =  datum['timeInterval']['start']
    proc_item['end_time_utc'] = datum['timeInterval']['end']
    try:
        proc_item['duration_seconds'] = calculate_duration(datum['timeInterval']['duration'])
    except KeyError:
        raise
    
    processed_items.append(proc_item)

# Make Preprocessed Data CSV
with open('preprocessed_data.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',')
    csvwriter.writerow(['Project Name', 'Project ID', 'Task Name', 'Task ID', 'Description',
        'Start Time (UTC)', 'End Time (UTC)', 'Duration (Seconds)'])
    for pi in processed_items:
        csvwriter.writerow([pi['project_name'], pi['project_id'], pi['task_name'], pi['task_id'],
        pi['description'], pi['start_time_utc'], pi['end_time_utc'], pi['duration_seconds']])

# Make Preprocessed Data JSON
prpd = open('preprocessed_data.json', 'w')
json.dump(processed_items, prpd)              