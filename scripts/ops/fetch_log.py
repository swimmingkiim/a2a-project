
import subprocess

with open('build_fail_log.txt', 'w') as f:
    try:
        subprocess.run(
            ['gcloud', 'builds', 'log', '7e89c13c-845e-4d9c-8342-1e56c09ec9aa', '--project=a2a-project-486504'],
            cwd='/Users/kimsooyoung/Developments/projects/a2a-projects',
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )
    except Exception as e:
        f.write(f"\nException: {e}")
