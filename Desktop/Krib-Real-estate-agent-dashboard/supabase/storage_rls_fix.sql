-- CORRECT Supabase Storage RLS Policies for krib_host bucket
-- This uses the proper Supabase RLS policy syntax

-- First, ensure RLS is enabled on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "krib_host_upload_policy" ON storage.objects;
DROP POLICY IF EXISTS "krib_host_select_policy" ON storage.objects;
DROP POLICY IF EXISTS "krib_host_public_policy" ON storage.objects;
DROP POLICY IF EXISTS "krib_host_update_policy" ON storage.objects;
DROP POLICY IF EXISTS "krib_host_delete_policy" ON storage.objects;

-- Policy to allow authenticated users to upload to krib_host bucket
CREATE POLICY "krib_host_upload_policy" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'krib_host');

-- Policy to allow authenticated users to select from krib_host bucket
CREATE POLICY "krib_host_select_policy" ON storage.objects
FOR SELECT TO authenticated
USING (bucket_id = 'krib_host');

-- Policy to allow public read access to krib_host bucket (for image display)
CREATE POLICY "krib_host_public_policy" ON storage.objects
FOR SELECT TO public
USING (bucket_id = 'krib_host');

-- Policy to allow authenticated users to update in krib_host bucket
CREATE POLICY "krib_host_update_policy" ON storage.objects
FOR UPDATE TO authenticated
USING (bucket_id = 'krib_host')
WITH CHECK (bucket_id = 'krib_host');

-- Policy to allow authenticated users to delete from krib_host bucket
CREATE POLICY "krib_host_delete_policy" ON storage.objects
FOR DELETE TO authenticated
USING (bucket_id = 'krib_host');
