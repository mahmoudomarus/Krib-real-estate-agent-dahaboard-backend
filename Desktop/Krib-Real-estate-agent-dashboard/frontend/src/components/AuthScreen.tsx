import { useState } from "react"
import { Bot, Eye, EyeOff } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs"

interface AuthScreenProps {
  onAuthSuccess: () => void
}

export function AuthScreen({ onAuthSuccess }: AuthScreenProps) {
  return (
    <div className="min-h-screen flex items-center justify-center krib-auth-real-estate-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Bot className="h-7 w-7" />
            </div>
          </div>
          <CardTitle>This component is deprecated</CardTitle>
          <CardDescription>
            Please use AuthForm instead, which uses the centralized AppContext
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  )
}