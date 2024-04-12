# gcs-synapse-sync

Creates a Google Storage Bucket configured according to [Synapse Custom Storage Locations](https://help.synapse.org/docs/Custom-Storage-Locations.2048327803.html#CustomStorageLocations-SettingupanExternalGoogleCloudStorageBucket) requirements, and a compatible Google Cloud Function to index bucket files to Synapse. 

### Requirements
- Python 3.10+
- Terraform 1.7.0+

You must have access to deploy resources in the HTAN Google Cloud Project, `htan-dcc`. Please contact an owner of `htan-dcc` to request access (Owners in 2024: Clarisse Lau, Vesteinn Thorsson, William Longabaugh, ISB)

### Getting started
- Create a new Synapse project, and give `synapse-service-HTAN-lambda` edit & delete access to the project
- Configure a custom [IAM Role](https://cloud.google.com/iam/docs/roles-overview#custom) with the following permissions:

```
- secretmanager.secrets.get
- secretmanager.versions.access
- secretmanager.versions.get
- storage.buckets.list
- storage.objects.get
- storage.objects.list
```
- Create secret `synapse_service_pat` in [Secret Manager](https://cloud.google.com/secret-manager/docs) containing a `synapse-service-HTAN-lambda` auth token

## Deploy resources

```
terraform init
terraform plan
terraform apply
```

## Set Google bucket as Synapse Upload Location
Configure the new Google bucket as the upload location for your Synapse project, according to https://help.synapse.org/docs/Custom-Storage-Locations.2048327803.html#CustomStorageLocations-SetGoogleCloudBucketasUploadLocation 

**NOTE**: this step must be performed by the `synapse-service-HTAN-lambda` account

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


