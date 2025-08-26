-- Make krib_host bucket public for image access
-- This allows public URLs to work properly

UPDATE storage.buckets 
SET public = true 
WHERE id = 'krib_host';

-- Verify the bucket is now public
SELECT id, name, public FROM storage.buckets WHERE id = 'krib_host';
