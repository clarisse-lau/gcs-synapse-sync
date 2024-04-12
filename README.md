# gcs-synapse-sync

Create a Google Storage Bucket and compatible Google Cloud Function to index bucket files to Synapse. 

### Requirements
- Python 3.10+
- Terraform 1.7.0+

You must have access to deploy resources in the HTAN Google Cloud Project, `htan-dcc`. Please contact an owner of `htan-dcc` to request access (Owners in 2024: Clarisse Lau, Vesteinn Thorsson, William Longabaugh, ISB)

### Getting started
- Configure a custom [IAM Role](https://cloud.google.com/iam/docs/roles-overview#custom) with the following permissions:

```
- secretmanager.secrets.get
- secretmanager.versions.access
- secretmanager.versions.get
- storage.buckets.list
- storage.objects.get
- storage.objects.list
```

- Create a [Synapse Auth Token](https://help.synapse.org/docs/Managing-Your-Account.2055405596.html#ManagingYourAccount-PersonalAccessTokens) secret in [Secret Manager](https://cloud.google.com/secret-manager/docs)

## Deployment

```
terraform init
terraform plan
terraform apply
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


