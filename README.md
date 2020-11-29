# Time Tracking Experiment (Fall 2020)

## Description

This is the code for the time tracking experiment that I did during the Fall 2020 semester.

A writeup of my findings will be posted soon, and this README will be updated with its location.

This is really just something I did for fun, so I'm not planning on making any major updates
to the code for the project after this, aside from adding some visualization-related code.

## Getting Started

### Prerequisites
- Python 3.7+.
- [`Pipenv`](https://pipenv.pypa.io/en/latest/) tool. This tool makes installing the
dependencies for this project and handling virtual environments straightforward. So, if you
haven't installed that, do so using the steps detailed [here](https://pipenv.pypa.io/en/latest/install/#installing-pipenv).
- You're currently logged into Clockify and have an active workspace.

### Steps
1. Generate an API key by going to your user [settings](https://clockify.me/user/settings) page and scrolling down to the **API** heading. Then click _Generate_ to generate a personal API key. Store this API key in an environment variable named `CLOCKIFY_API_KEY`. Alternatively, you can add the 
API key as a command-line argument using the `-a` or `--api-key` options.

2. Clone the project repo and enter it:
```bash
git clone https://github.com/zaataylor/time-tracking.git
cd time-tracking
```

3. Install the required project dependencies included in the `Pipfile` using:
```bash
pipenv install
```

4. Get time tracking data by invoking `python get_time_data.py` with the proper command line parameters. Here is the
usage information:
```bash
usage: get_time_data.py [-h] [-a API_KEY]
                        (--num-pages NUM_PAGES | --num-entries NUM_ENTRIES)
                        [-p PROJ_FILE] [-t TASKS_FILE] [-e ENTRIES_FILE]
                        [-d DELAY]

Get Clockify projects, tasks, and time entry data and write it to files.

optional arguments:
  -h, --help            show this help message and exit
  -a API_KEY, --api-key API_KEY
                        Your personal Clockify API key. If not specified here,
                        then you must have the CLOCKIFY_API_KEY environment
                        variable set on your system.
  --num-pages NUM_PAGES
                        The number of (contiguous) pages to request from the
                        Clockify API.
  --num-entries NUM_ENTRIES
                        Lower bound on the number of entries to grab from the
                        Clockify API. If specified, this value will be used to
                        calculate how many pages to grab from the Clockify
                        API.
  -p PROJ_FILE, --projects-file PROJ_FILE
                        The name of the file to write projects information to.
                        Defaults to 'projects.json' if not specified.
  -t TASKS_FILE, --tasks-file TASKS_FILE
                        The name of the file to write tasks information to.
                        Defaults to 'tasks.json' if not specified.
  -e ENTRIES_FILE, --entries-file ENTRIES_FILE
                        The name of the file to write time entry data to.
                        Defaults to 'entries.json' if not specified.
  -d DELAY, --delay DELAY
                        Delay between subsequent calls to the Clockify API, in
                        seconds. Default value is 0.2. Using a value less than
                        this may cause the program to fail due to Clockify API
                        rate limiting.

Have fun tracking! :)
```

5. (Optional) Invoke the `preprocess_data.py` script to process the time entry data
retrieved from the Clockify API in an opinionated fashion. Here's an example of what
the preprocessor script does to a time entry:


Raw Clockify API data:
```JSON
{
        "id": "5fb02c5f94454c3d296af408",
        "description": "Read PRIMES is in P",
        "tagIds": null,
        "userId": "some-user-id-here",
        "billable": true,
        "taskId": "5f30780549070a418a96891b",
        "projectId": "5f306f4649070a418a968435",
        "timeInterval": {
            "start": "2020-11-14T19:13:35Z",
            "end": "2020-11-14T19:20:31Z",
            "duration": "PT6M56S"
        },
        "workspaceId": "some-workspace-id-here",
        "isLocked": false,
        "customFieldValues": null
    }
```
Preprocessed Data:
```JSON
{
        "task_id": "5f30780549070a418a96891b",
        "task_name": "MA 522",
        "project_id": "5f306f4649070a418a968435",
        "project_name": "Classes",
        "description": "read primes is in p",
        "start_time_utc": "2020-11-14T19:13:35Z",
        "start_date_utc": "2020-11-14",
        "end_time_utc": "2020-11-14T19:20:31Z",
        "end_date_utc": "2020-11-14",
        "duration_seconds": 416
    }
```

You can see more detailed usage information here:
```bash
usage: preprocess_data.py [-h] [-p PROJ_FILE] [-t TASKS_FILE]
                          [-e ENTRIES_FILE] [-d PROC_DATA_FILE] [--csv]

Preprocess Clockify API data from files in an opinionated fashion.

optional arguments:
  -h, --help            show this help message and exit
  -p PROJ_FILE, --projects-file PROJ_FILE
                        The name of the file to get projects information from.
                        Defaults to 'projects.json' if not specified.
  -t TASKS_FILE, --tasks-file TASKS_FILE
                        The name of the file to get tasks information from.
                        Defaults to 'tasks.json' if not specified.
  -e ENTRIES_FILE, --entries-file ENTRIES_FILE
                        The name of the file to get time entry data from.
                        Defaults to 'entries.json' if not specified.
  -d PROC_DATA_FILE, --data-file PROC_DATA_FILE
                        The name of the file that will hold the preprocessed
                        data. Defaults to 'preprocessed_data.json'.
  --csv                 Specify this flag to indicate that the data should
                        also be exported to CSV format. The CSV file will have
                        the same name as the file specified by the -d/--data-
                        file argument, or be named 'preprocessed_data.csv' if
                        that argument is not given.

Have fun preprocessing! :)
```
The processing logic in `preprocess_data.py` is fairly extensible, so feel free to add logic that
makes more sense for your use case. :)