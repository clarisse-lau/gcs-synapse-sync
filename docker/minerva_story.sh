#!/bin/bash

echo "Beginning minerva_story.sh execution"

# retrieve instance metadata
INPUT_JSON=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/INPUT_JSON" -H "Metadata-Flavor: Google")
INPUT_TIFF=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/INPUT_TIFF" -H "Metadata-Flavor: Google")
DIR_NAME=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/DIR_NAME" -H "Metadata-Flavor: Google")

IMAGE_GCS_URL="gs://${DIR_NAME}/${INPUT_TIFF}"
STORY_GCS_URL="gs://${DIR_NAME}/${INPUT_JSON}"
SUFFIX=".story.json"
OUTPUT_DIR="${INPUT_JSON%%$SUFFIX}"

error_exit () {
  echo "${BASENAME} - ${1}" >&2
  exit 1
}

# copy image and story to container
gsutil cp "${IMAGE_GCS_URL}" "/data/${INPUT_TIFF}" || error_exit "Failed to download input ome-tiff file."
gsutil cp "${STORY_GCS_URL}" "/data/${INPUT_JSON}" || error_exit "Failed to download author json file."

cd /data

echo "Running rendering script save_exhibit_pyramid.py"
python3 /usr/local/bin/save_exhibit_pyramid.py "${INPUT_TIFF}" "${INPUT_JSON}" "${OUTPUT_DIR}" || error_exit "Failed to run save_exhibit_pyramid.py."

echo "Uploading jpeg pyramid and exhibit file to GCS"
gsutil cp -r "${OUTPUT_DIR}/" "gs://${DIR_NAME}/${OUTPUT_DIR}" || error_exit "Failed to upload output folder to GCS."

echo "Uploading index.html to GCS"
gsutil cp /usr/local/bin/index.html "gs://${DIR_NAME}/${OUTPUT_DIR}/index.html" || error_exit "Failed to upload index.html to GCS."

# clean up TIFF image and output directory
rm "${INPUT_TIFF}"
rm -r "${OUTPUT_DIR}/"

# Delete VM
echo "Deleting VM"
gcp_zone=$(curl -H Metadata-Flavor:Google http://metadata.google.internal/computeMetadata/v1/instance/zone -s | cut -d/ -f4)
gcloud compute instances delete $(hostname) --zone ${gcp_zone}
