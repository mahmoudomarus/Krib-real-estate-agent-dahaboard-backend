-- Supabase Storage Policies for krib_host bucket
-- Run this in Supabase Dashboard -> Storage -> krib_host bucket -> Policies

-- Policy 1: Allow authenticated users to INSERT (upload) images
INSERT INTO storage.policies (name, bucket_id, policy, check_expression)
VALUES (
  'Allow authenticated uploads',
  'krib_host',
  'INSERT',
  'auth.role() = ''authenticated'''
);

-- Policy 2: Allow authenticated users to SELECT (view) images  
INSERT INTO storage.policies (name, bucket_id, policy, check_expression)
VALUES (
  'Allow authenticated select',
  'krib_host', 
  'SELECT',
  'auth.role() = ''authenticated'''
);

-- Policy 3: Allow public SELECT (for displaying images)
INSERT INTO storage.policies (name, bucket_id, policy, check_expression)
VALUES (
  'Allow public select',
  'krib_host',
  'SELECT', 
  'true'
);

-- Policy 4: Allow authenticated users to UPDATE images
INSERT INTO storage.policies (name, bucket_id, policy, check_expression)
VALUES (
  'Allow authenticated update',
  'krib_host',
  'UPDATE',
  'auth.role() = ''authenticated'''
);

-- Policy 5: Allow authenticated users to DELETE images
INSERT INTO storage.policies (name, bucket_id, policy, check_expression)
VALUES (
  'Allow authenticated delete', 
  'krib_host',
  'DELETE',
  'auth.role() = ''authenticated'''
);
