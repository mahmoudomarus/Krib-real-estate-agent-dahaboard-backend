-- Enable RLS on storage.objects table
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy to allow authenticated users to upload to property-images bucket
CREATE POLICY "Allow authenticated users to upload property images"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id IN ('make-3c640fc2-property-images', 'krib_host') 
  AND (storage.foldername(name))[1] = 'properties'
);

-- Policy to allow authenticated users to view property images
CREATE POLICY "Allow authenticated users to view property images"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id IN ('make-3c640fc2-property-images', 'krib_host') 
  AND (storage.foldername(name))[1] = 'properties'
);

-- Policy to allow public access to view property images (for display)
CREATE POLICY "Allow public access to view property images"
ON storage.objects
FOR SELECT
TO public
USING (
  bucket_id IN ('make-3c640fc2-property-images', 'krib_host') 
  AND (storage.foldername(name))[1] = 'properties'
);

-- Policy to allow authenticated users to update/delete their property images
CREATE POLICY "Allow authenticated users to update property images"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id IN ('make-3c640fc2-property-images', 'krib_host') 
  AND (storage.foldername(name))[1] = 'properties'
);

CREATE POLICY "Allow authenticated users to delete property images"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id IN ('make-3c640fc2-property-images', 'krib_host') 
  AND (storage.foldername(name))[1] = 'properties'
);
