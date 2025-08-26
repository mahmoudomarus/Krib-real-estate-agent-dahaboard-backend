import { supabase } from '../utils/supabase/client'

export interface ImageUploadResult {
  success: boolean
  url?: string
  error?: string
}

export async function uploadImageToSupabase(file: File, folder: string = 'properties'): Promise<ImageUploadResult> {
  try {
    // Create a unique filename
    const fileExt = file.name.split('.').pop()
    const fileName = `${Math.random().toString(36).substring(2)}-${Date.now()}.${fileExt}`
    const filePath = `${folder}/${fileName}`

    console.log('Uploading file:', file.name, 'to path:', filePath)

    // Upload to krib_host bucket
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('krib_host')
      .upload(filePath, file, {
        cacheControl: '3600',
        upsert: false
      })

    if (uploadError) {
      console.error('Upload error:', uploadError)
      return {
        success: false,
        error: uploadError.message
      }
    }

    console.log('Upload successful:', uploadData)

    // Get the public URL from krib_host bucket
    const { data: urlData } = supabase.storage
      .from('krib_host')
      .getPublicUrl(filePath)

    if (!urlData.publicUrl) {
      return {
        success: false,
        error: 'Failed to generate public URL'
      }
    }

    console.log('Generated public URL:', urlData.publicUrl)

    return {
      success: true,
      url: urlData.publicUrl
    }
  } catch (error: any) {
    console.error('Unexpected upload error:', error)
    return {
      success: false,
      error: error.message || 'Upload failed'
    }
  }
}

export async function uploadMultipleImages(files: FileList | File[], folder: string = 'properties'): Promise<ImageUploadResult[]> {
  const fileArray = Array.from(files)
  const uploadPromises = fileArray.map(file => uploadImageToSupabase(file, folder))
  
  try {
    const results = await Promise.all(uploadPromises)
    return results
  } catch (error: any) {
    console.error('Multiple upload error:', error)
    return fileArray.map(() => ({
      success: false,
      error: error.message || 'Upload failed'
    }))
  }
}
