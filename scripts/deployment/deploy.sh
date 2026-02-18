#!/bin/bash
gcloud builds submit --config cloudbuild.yaml . --quiet > build.log 2>&1
