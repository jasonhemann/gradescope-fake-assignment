# gradescope-fake-assignment

Create a dummy pdf template and a combined pdf of submissions from a class roster.
Each student has a submission with their name on it, otherwise identical to the template.
This makes it easy to provide grades within gradescope for assignments that do not otherwise have submissions.

## Entering the virtual environment

The project is developed in a virtual environment managed by pdm.

In order to activate that virtual env, use 

```
eval $(pdm venv activate in-project)
```

## Usage 

```
python3 -m src.gradescope_fake_assignment "Assignment 1" ./tests/resources/test-roster-bad-columns.csv --format standard --output_dir ./output
```

## Generating the executable

```
pyinstaller --onefile src/gradescope_fake_assignment/__main__.py --name gradescope_fake_assignment
```

and the executable is created under `./dist/`
