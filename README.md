# gcs-synapse-sync

Google Cloud Function code to index files in GCS bucket by creating filehandles on Synapse, triggered by file changes to bucket.

### Prerequisites
Configure Service account
htan-dcc: gcs-synapse-sync

#### Minerva Stories
This function will also render images for [Minerva Story](https://www.cycif.org/software/minerva) visualization, generating a directory containing the JPEG image pyramid and exhibit files suitable for hosting with Minerva Stories (See [below](#minerva-story) for usage details).

### Requirements
- Python 3.7+

### Getting started
- Configure Google Cloud Storage bucket and Synapse project as outlined in [Synapse documentation](https://docs.synapse.org/articles/custom_storage_location.html#toc-custom-storage-locations)
- Create two Google Cloud service accounts that will be used by the cloud function and compute instance. We will assume these service accounts are named `compute-execute-batch-job` and `sync-minerva-function` respectively.

`compute-execute-batch-job` requires the following permissions:
```
- compute.disks.delete
- compute.instances.delete
- compute.instances.deleteAccessConfig
- logging.logEntries.create
- storage.buckets.get
- storage.objects.create
- storage.objects.get
- storage.objects.list
```

`sync-minerva-function` requires the following permissions:
```
- compute.disks.create
- compute.instances.addAccessConfig
- compute.instances.attachDisk
- compute.instances.create
- compute.instances.setLabels
- compute.instances.setMetadata
- compute.instances.setServiceAccount
- compute.instances.updateDisplayDevice
- compute.subnetworks.use
- compute.subnetworks.useExternalIp
- secretmanager.secrets.get
- secretmanager.versions.access
- secretmanager.versions.get
- storage.buckets.list
- storage.objects.get
- storage.objects.list
```

## Deployment

### Set up the Docker image for Minerva story processing
1. Install [Docker](https://docs.docker.com/get-docker/)
2. Clone this repository and navigate to `docker` directory within the repository
3. Build Docker image
4. Tag the build and push the image to your repository

### Cloud Functions
1. Install and initialize the [Cloud SDK](https://cloud.google.com/sdk/docs)
2. Enable the [Cloud Functions API](https://console.cloud.google.com/flows/enableapi?apiid=cloudfunctions&redirect=https://cloud.google.com/functions/quickstart&_ga=2.118113162.2081301619.1590113168-88580457.1590113168)
3. Navigate to `gcs-synapse-sync` directory within the repository
4. Edit `env.yaml` to set environment variables
5. Deploy two functions using the gcloud command-line tool:

Object Creation (triggered by file addition to bucket, creates filehandle on Synapse)
```
gcloud functions deploy <function_name> \
--runtime <python38> \
--env-vars-file env.yaml \
--entry-point obj_add \
--trigger-resource <my_bucket> \
--trigger-event google.storage.object.finalize \
--service-account sync-minerva-function@htan-dcc.iam.gserviceaccount.com
```
Object Deletion (triggered by file deletion from bucket, deletes filehandle from Synapse)
```
gcloud functions deploy <function_name> \
--runtime <python38> \
--env-vars-file env.yaml \
--entry-point obj_delete \
--trigger-resource <my_bucket> \
--trigger-event google.storage.object.delete \
--service-account sync-minerva-function@htan-dcc.iam.gserviceaccount.com
```

---
### To Use:
1. Place file in folder of GCS bucket

Example `cp` command:
```
gsutil cp <file> gs://<MyBucket>/<MyFolder>/
```
*Note: For large files, parallel composite uploads may be enabled for faster upload speeds. Please note that if this is done, you must provide a base-64 encoded MD5 as a metadata tag `content-md5` for each file upon upload (see example below). In addition, users who download files uploaded as composite objects must have a compiled crcmod installed.*

```
gsutil -h x-goog-meta-content-md5:<md5> cp <file> gs://<MyBucket>/<MyFolder>/
```
2. Check GC logs to see if the function was triggered and completed successfully
3. Check Synapse project to see if filehandle was created


#### Minerva Story
Add input OME-TIFF and json `<story_name>.story.json` files to the `minerva` folder in the bucket. Ensure that the image name contained in the `in_file` property of the author json file matches that of the OME-TIFF input file. Output image tiles and exhibit files will be added to the <story_name> directory in the `minerva` folder.
