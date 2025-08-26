import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Alert, AlertDescription } from './ui/alert'
import { ExternalLink, Info } from 'lucide-react'

export function GoogleAuthSetup() {
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Info className="h-5 w-5" />
          Google Authentication Setup Required
        </CardTitle>
        <CardDescription>
          To enable Google sign-in, you need to configure OAuth in your Supabase project
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Google OAuth requires additional setup in your Supabase dashboard. Without this setup, you'll see a "provider is not enabled" error.
          </AlertDescription>
        </Alert>

        <div className="space-y-3">
          <h4 className="font-medium">Setup Instructions:</h4>
          
          <ol className="list-decimal list-inside space-y-2 text-sm">
            <li>Go to your Supabase project dashboard</li>
            <li>Navigate to Authentication → Settings → Auth Providers</li>
            <li>Enable Google provider</li>
            <li>Add your Google OAuth Client ID and Secret</li>
            <li>Configure authorized redirect URLs</li>
          </ol>

          <div className="flex items-center gap-2 mt-4">
            <ExternalLink className="h-4 w-4" />
            <a 
              href="https://supabase.com/docs/guides/auth/social-login/auth-google"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline text-sm"
            >
              Follow the complete setup guide →
            </a>
          </div>
        </div>

        <div className="mt-4 p-3 bg-muted rounded-lg">
          <h5 className="font-medium mb-2">Quick Setup Steps:</h5>
          <div className="text-sm space-y-1">
            <p><strong>1. Google Console:</strong> Create OAuth 2.0 credentials</p>
            <p><strong>2. Supabase:</strong> Add Client ID and Secret to Auth settings</p>
            <p><strong>3. Redirect URL:</strong> Add your site URL + /auth/callback</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}