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
3. Clone this repository, and edit `env.yaml` to set the environment variable `synapseProjectId`: the Synapse ID of the center's project, a unique identifier with the format `syn12345678`

    *`gcProjectName` variable should remain `htan-dcc`*

4. Change directory to within the repository, and deploy two functions using the gcloud command-line tool:
```
gcloud functions deploy <center_name>_create \
--runtime python37 \
--env-vars-file env.yaml \
--entry-point syn_create \
--trigger-resource <my_bucket> \
--trigger-event google.storage.object.finalize
```

```
gcloud functions deploy <center_name>_delete \
--runtime python37 \
--env-vars-file env.yaml \
--entry-point syn_delete \
--trigger-resource <my_bucket> \
--trigger-event google.storage.object.delete
```

---
For large files, parallel composite uploads may be enabled for faster upload speeds. Please note that if this is done, you must provide a base-64 encoded MD5 as a metadata tag `content-md5` for each file upon upload (see example below). In addition, users who download files uploaded as composite objects must have a compiled crcmod installed.

```
gsutil -h x-goog-meta-content-md5:<md5> cp <file> gs://<MyBucket>/<MyFolder>/
```

---
### Sync Existing Files
To sync files already in a bucket, complete the setup and deployment steps above, then run the following command with your bucket and folder name. This will effectively "touch" all files within that folder and trigger the cloud function to sync the files to Synapse:

```
gsutil cp -r gs://<your-bucket>/<folder-to-sync> gs://<your-bucket>/<folder-to-sync>
```

---
### To Test: 
1. Place a file in a folder within the bucket (folder names may not begin with a number)
2. Check GC logs to see if the function was triggered and completed successfully
3. Check Synapse project to see if filehandle was created
