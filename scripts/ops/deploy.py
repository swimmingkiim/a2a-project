
import subprocess
import sys

with open('deploy_output.txt', 'w') as f:
    try:
        # Run gcloud command
        result = subprocess.run(
            ['gcloud', 'builds', 'submit', '--config', 'cloudbuild.yaml', '.', '--quiet'],
            cwd='/Users/kimsooyoung/Developments/projects/a2a-projects',
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(f"Return code: {result.returncode}")
    except Exception as e:
        f.write(f"\nException: {e}")
        print(f"Exception: {e}")
