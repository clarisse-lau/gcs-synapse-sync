# gcs-synapse-sync

Google Cloud Function code to index files in GCS bucket by creating filehandles on Synapse, triggered by file changes to bucket.

### Requirements
- Python 3.7

### Getting started
- Configure GCS bucket and Synapse project as outlined in [Synapse documentation](https://docs.synapse.org/articles/custom_storage_location.html#toc-custom-storage-locations)

## Deployment
### gcloud CLI tool
1. Enable the [Cloud Functions API](https://console.cloud.google.com/flows/enableapi?apiid=cloudfunctions&redirect=https://cloud.google.com/functions/quickstart&_ga=2.118113162.2081301619.1590113168-88580457.1590113168)
2. Initialize the [Cloud SDK](https://cloud.google.com/sdk/docs)
3. Edit `.env.yaml` to set environment variables:
    - `username`: Synapse account username 
    - `apiKey`: Synapse API Key, can be found under Settings on Synapse
    - `synapseProjectId`: Synapse ID of project, a unique identifier with the format `syn12345678`
    - `foldersToSync`: Comma separated list of folders in bucket to be synchronized to Synapse
4. Using the gcloud command-line tool, deploy two functions from the directory containing the function code and dependencies:

```
gcloud functions deploy syn_create --runtime python37 --env-vars-file .env.yaml --trigger-resource <TRIGGER_BUCKET_NAME> --trigger-event google.storage.object.finalize
```

```
gcloud functions deploy syn_delete --runtime python37 --env-vars-file .env.yaml --trigger-resource <TRIGGER_BUCKET_NAME> --trigger-event google.storage.object.delete
```


### GCP Console
Deploy two functions (one for each event type trigger)

#### Create 'Object Create' Function
1. From your GCP project dashboard, navigate to the `Cloud Functions` resource
2. Click `Create function` and provide function name
3. Under  **Trigger** 
    - Select `Cloud Storage`  
    - `Event Type`: 'Finalize/Create'
    - `Bucket`: \<your-bucket\>
4. Upload zip containing `main.py` and `requirements.txt` files
    - `Runtime`: Python 3.7
    - `Function to Execute`: ‘syn_create’
    - `Stage Bucket`: \<your-bucket\>
5. Under **Advanced Options**, set up environment variables. 
The function source code requires four input variables: 
    - `username`: Synapse account username 
    - `apiKey`: Synapse API Key, can be found under Settings on Synapse
    - `synapseProjectId`: Synapse ID of project, a unique identifier with the format `syn12345678`
    - `foldersToSync`: Comma separated list of folders in bucket to be synchronized to Synapse
    
#### Create 'Object Delete' Function
6. Click `Create function` and provide function name
7. Under  **Trigger** 
    - Select `Cloud Storage`  
    - `Event Type`: 'Delete'
    - `Bucket`: \<your-bucket\>
8. Upload zip containing `main.py` and `requirements.txt` files
    - `Runtime`: Python 3.7
    - `Function to Execute`: ‘syn_delete’
    - `Stage Bucket`: \<your-bucket\>
9. Under **Advanced Options**, set up your four environment variables


## To Test: 
1. Place a file in one of the folders specified in `foldersToSync` environment variable
2. Check GC logs to see if the function was triggered and completed successfully
3. Check Synapse project to see if filehandle was created
