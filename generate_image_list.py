import os
import json

# Get all image files from static/images/
images_dir = 'static/images'
image_extensions = ('.jpg', '.jpeg', '.png', '.gif')

images = []
for filename in os.listdir(images_dir):
    if filename.lower().endswith(image_extensions):
        images.append(f'static/images/{filename}')

# Write to JSON file
with open('static/images.json', 'w') as f:
    json.dump(images, f, indent=2)

print(f'Generated images.json with {len(images)} images')
