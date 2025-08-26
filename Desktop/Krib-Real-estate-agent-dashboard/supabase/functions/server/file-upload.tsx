import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
)

const BUCKET_NAME = 'make-3c640fc2-property-images'

// Initialize storage bucket on startup
export async function initializeStorage() {
  try {
    const { data: buckets } = await supabase.storage.listBuckets()
    const bucketExists = buckets?.some(bucket => bucket.name === BUCKET_NAME)
    
    if (!bucketExists) {
      const { error } = await supabase.storage.createBucket(BUCKET_NAME, {
        public: false,
        fileSizeLimit: 5242880, // 5MB
        allowedMimeTypes: ['image/jpeg', 'image/png', 'image/webp']
      })
      
      if (error) {
        console.error('Failed to create storage bucket:', error)
      } else {
        console.log('Storage bucket created successfully')
      }
    }
  } catch (error) {
    console.error('Storage initialization error:', error)
  }
}

export async function uploadPropertyImage(
  userId: string, 
  propertyId: string, 
  file: File
): Promise<{ url: string; error?: string }> {
  try {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      return { url: '', error: 'Invalid file type. Only images are allowed.' }
    }

    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      return { url: '', error: 'File too large. Maximum size is 5MB.' }
    }

    // Generate unique filename
    const fileExt = file.name.split('.').pop()
    const fileName = `${userId}/${propertyId}/${Date.now()}.${fileExt}`

    // Upload to Supabase Storage
    const { data, error } = await supabase.storage
      .from(BUCKET_NAME)
      .upload(fileName, file, {
        cacheControl: '3600',
        upsert: false
      })

    if (error) {
      console.error('Upload error:', error)
      return { url: '', error: 'Failed to upload image' }
    }

    // Generate signed URL for private access
    const { data: urlData, error: urlError } = await supabase.storage
      .from(BUCKET_NAME)
      .createSignedUrl(data.path, 60 * 60 * 24 * 365) // 1 year expiry

    if (urlError) {
      console.error('URL generation error:', urlError)
      return { url: '', error: 'Failed to generate image URL' }
    }

    return { url: urlData.signedUrl }
  } catch (error) {
    console.error('Image upload error:', error)
    return { url: '', error: 'Unexpected error during upload' }
  }
}

export async function deletePropertyImage(
  userId: string,
  imagePath: string
): Promise<{ success: boolean; error?: string }> {
  try {
    // Verify the image belongs to the user (path should start with userId)
    if (!imagePath.startsWith(userId)) {
      return { success: false, error: 'Unauthorized to delete this image' }
    }

    const { error } = await supabase.storage
      .from(BUCKET_NAME)
      .remove([imagePath])

    if (error) {
      console.error('Delete error:', error)
      return { success: false, error: 'Failed to delete image' }
    }

    return { success: true }
  } catch (error) {
    console.error('Image deletion error:', error)
    return { success: false, error: 'Unexpected error during deletion' }
  }
}

export async function getPropertyImages(
  propertyId: string,
  userId: string
): Promise<{ images: string[]; error?: string }> {
  try {
    const { data, error } = await supabase.storage
      .from(BUCKET_NAME)
      .list(`${userId}/${propertyId}`)

    if (error) {
      console.error('List images error:', error)
      return { images: [], error: 'Failed to fetch images' }
    }

    const imagePromises = data.map(async (file) => {
      const { data: urlData } = await supabase.storage
        .from(BUCKET_NAME)
        .createSignedUrl(`${userId}/${propertyId}/${file.name}`, 60 * 60 * 24 * 365)
      
      return urlData?.signedUrl || ''
    })

    const images = await Promise.all(imagePromises)
    return { images: images.filter(url => url !== '') }
  } catch (error) {
    console.error('Get images error:', error)
    return { images: [], error: 'Unexpected error fetching images' }
  }
}