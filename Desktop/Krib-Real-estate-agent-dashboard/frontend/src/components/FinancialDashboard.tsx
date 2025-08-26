import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { Alert, AlertDescription } from "./ui/alert"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { 
  DollarSign, 
  TrendingUp, 
  Calendar, 
  CreditCard, 
  Download,
  Plus,
  AlertCircle,
  CheckCircle,
  Clock,
  Banknote
} from "lucide-react"
import { useApp } from "../contexts/AppContext"

interface FinancialSummary {
  total_balance: number
  pending_earnings: number
  total_earnings: number
  total_payouts: number
  platform_fees: number
  recent_transactions: any[]
  payout_frequency: string
  next_payout_date?: string
}

interface BankAccount {
  id: string
  account_holder_name: string
  bank_name: string
  account_number_last4: string
  account_type: string
  is_primary: boolean
  is_verified: boolean
  verification_status: string
}

interface Payout {
  id: string
  amount: number
  status: string
  bank_account_id: string
  bank_info?: any
  requested_at: string
  completed_at?: string
  estimated_arrival?: string
  failure_reason?: string
}

export function FinancialDashboard() {
  const { 
    getFinancialSummary, 
    getBankAccounts, 
    addBankAccount, 
    requestPayout, 
    getTransactions, 
    updatePayoutSettings 
  } = useApp()
  const [summary, setSummary] = useState<FinancialSummary | null>(null)
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([])
  const [payouts, setPayouts] = useState<Payout[]>([])
  const [loading, setLoading] = useState(true)
  const [payoutAmount, setPayoutAmount] = useState("")
  const [selectedBankAccount, setSelectedBankAccount] = useState("")
  const [showAddBankModal, setShowAddBankModal] = useState(false)
  const [addingBank, setAddingBank] = useState(false)
  const [bankForm, setBankForm] = useState({
    account_holder_name: "",
    bank_name: "",
    account_number: "",
    routing_number: "",
    account_type: "checking",
    is_primary: false
  })

  useEffect(() => {
    loadFinancialData()
  }, [])

  async function loadFinancialData() {
    try {
      setLoading(true)
      
      const [summaryData, bankAccountsData, transactionsData] = await Promise.all([
        getFinancialSummary(),
        getBankAccounts(),
        getTransactions(20)
      ])
      
      setSummary(summaryData)
      setBankAccounts(bankAccountsData)
      setPayouts(transactionsData || [])
      
      // Set default bank account
      const primaryAccount = bankAccountsData.find((account: BankAccount) => account.is_primary)
      if (primaryAccount) {
        setSelectedBankAccount(primaryAccount.id)
      }
      
    } catch (error) {
      console.error('Failed to load financial data:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleRequestPayout() {
    if (!payoutAmount || !selectedBankAccount) return
    
    try {
      const payout = await requestPayout(parseFloat(payoutAmount))
      
      setPayouts(prev => [payout, ...prev])
      setPayoutAmount("")
      
      // Reload summary to update available balance
      const updatedSummary = await getFinancialSummary()
      setSummary(updatedSummary)
      
    } catch (error) {
      console.error('Failed to request payout:', error)
      alert('Failed to request payout. Please try again.')
    }
  }

  async function handleAddBankAccount() {
    if (!bankForm.account_holder_name || !bankForm.bank_name || !bankForm.account_number || !bankForm.routing_number) {
      alert('Please fill in all required fields')
      return
    }

    try {
      setAddingBank(true)
      
      // Add last 4 digits of account number
      const accountData = {
        ...bankForm,
        account_number_last4: bankForm.account_number.slice(-4)
      }
      
      const newAccount = await addBankAccount(accountData)
      setBankAccounts(prev => [...prev, newAccount])
      
      // Reset form and close modal
      setBankForm({
        account_holder_name: "",
        bank_name: "",
        account_number: "",
        routing_number: "",
        account_type: "checking",
        is_primary: false
      })
      setShowAddBankModal(false)
      
      alert('Bank account added successfully!')
      
    } catch (error) {
      console.error('Failed to add bank account:', error)
      alert('Failed to add bank account. Please try again.')
    } finally {
      setAddingBank(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'processing': return 'bg-blue-100 text-blue-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />
      case 'processing': return <Clock className="h-4 w-4" />
      case 'pending': return <AlertCircle className="h-4 w-4" />
      case 'failed': return <AlertCircle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Financial Dashboard</h1>
        <p className="text-muted-foreground">
          Manage your earnings, payouts, and financial settings
        </p>
      </div>

      {/* Financial Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="krib-card krib-glow-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Balance</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary?.pending_earnings.toFixed(2) || '0.00'}</div>
            <p className="text-xs text-muted-foreground">Ready for payout</p>
          </CardContent>
        </Card>

        <Card className="krib-card krib-glow-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Earnings</CardTitle>
            <TrendingUp className="h-4 w-4 text-krib-lime" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary?.total_earnings.toFixed(2) || '0.00'}</div>
            <p className="text-xs text-muted-foreground">All time earnings</p>
          </CardContent>
        </Card>

        <Card className="krib-card krib-glow-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Payouts</CardTitle>
            <Banknote className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary?.total_payouts.toFixed(2) || '0.00'}</div>
            <p className="text-xs text-muted-foreground">Money transferred</p>
          </CardContent>
        </Card>

        <Card className="krib-card krib-glow-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Platform Fees</CardTitle>
            <CreditCard className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary?.platform_fees.toFixed(2) || '0.00'}</div>
            <p className="text-xs text-muted-foreground">Fees paid</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="payouts" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="payouts">Payouts</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Payouts Tab */}
        <TabsContent value="payouts" className="space-y-4">
          {/* Request Payout Section */}
          <Card>
            <CardHeader>
              <CardTitle>Request Payout</CardTitle>
              <CardDescription>
                Transfer your available earnings to your bank account
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {summary && summary.pending_earnings > 0 ? (
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="text-sm font-medium">Amount</label>
                    <input
                      type="number"
                      value={payoutAmount}
                      onChange={(e) => setPayoutAmount(e.target.value)}
                      placeholder={`Max: $${summary.pending_earnings.toFixed(2)}`}
                      max={summary.pending_earnings}
                      className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Bank Account</label>
                    <select
                      value={selectedBankAccount}
                      onChange={(e) => setSelectedBankAccount(e.target.value)}
                      className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {bankAccounts.map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.bank_name} ****{account.account_number_last4}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <Button 
                      onClick={handleRequestPayout}
                      disabled={!payoutAmount || parseFloat(payoutAmount) <= 0}
                      className="w-full"
                    >
                      Request Payout
                    </Button>
                  </div>
                </div>
              ) : (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No earnings available for payout. Complete bookings to start earning!
                  </AlertDescription>
                </Alert>
              )}

              {summary?.next_payout_date && (
                <div className="text-sm text-muted-foreground">
                  <Calendar className="inline h-4 w-4 mr-1" />
                  Next automatic payout: {new Date(summary.next_payout_date).toLocaleDateString()}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payout History */}
          <Card>
            <CardHeader>
              <CardTitle>Payout History</CardTitle>
              <CardDescription>Your recent payout requests and transfers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {payouts.length > 0 ? (
                  payouts.map((payout) => (
                    <div key={payout.id} className="flex items-center justify-between border-b pb-3 last:border-0">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(payout.status)}
                          <span className="font-medium">${payout.amount.toFixed(2)}</span>
                          <Badge className={getStatusColor(payout.status)}>
                            {payout.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {new Date(payout.requested_at).toLocaleDateString()}
                          {payout.estimated_arrival && ` • Arrives ${new Date(payout.estimated_arrival).toLocaleDateString()}`}
                        </p>
                        {payout.failure_reason && (
                          <p className="text-sm text-red-600">{payout.failure_reason}</p>
                        )}
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        {payout.bank_info && `${payout.bank_info.bank_name} ****${payout.bank_info.account_number_last4}`}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-4">No payouts yet</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Transactions</CardTitle>
              <CardDescription>Your earning transactions from bookings</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {summary?.recent_transactions.length ? (
                  summary.recent_transactions.map((transaction) => (
                    <div key={transaction.id} className="flex items-center justify-between border-b pb-3 last:border-0">
                      <div className="space-y-1">
                        <p className="font-medium">{transaction.property_title}</p>
                        <p className="text-sm text-muted-foreground">
                          {transaction.guest_name} • {new Date(transaction.date).toLocaleDateString()}
                        </p>
                        <Badge variant={transaction.status === 'completed' ? 'default' : 'secondary'}>
                          {transaction.status}
                        </Badge>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-green-600">+${transaction.amount.toFixed(2)}</p>
                        <p className="text-sm text-muted-foreground">{transaction.type}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-4">No transactions yet</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Bank Accounts</CardTitle>
              <CardDescription>Manage your payout destinations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {bankAccounts.map((account) => (
                  <div key={account.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">{account.bank_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {account.account_type} ****{account.account_number_last4}
                      </p>
                      <div className="flex gap-2 mt-1">
                        {account.is_primary && <Badge>Primary</Badge>}
                        <Badge variant={account.is_verified ? 'default' : 'secondary'}>
                          {account.verification_status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
                <Dialog open={showAddBankModal} onOpenChange={setShowAddBankModal}>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="w-full">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Bank Account
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[500px] bg-white border shadow-lg">
                    <DialogHeader className="pb-4 border-b">
                      <DialogTitle className="text-xl font-semibold text-gray-900">Add Bank Account</DialogTitle>
                      <DialogDescription className="text-gray-600">
                        Add a bank account for receiving payouts. Your account information is encrypted and secure.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-6 bg-gray-50 rounded-lg">
                      <div className="space-y-4 bg-white p-4 rounded-md border">
                      <div className="space-y-2">
                        <Label htmlFor="account_holder_name" className="text-sm font-medium text-gray-700">Account Holder Name</Label>
                        <Input
                          id="account_holder_name"
                          value={bankForm.account_holder_name}
                          onChange={(e) => setBankForm(prev => ({...prev, account_holder_name: e.target.value}))}
                          placeholder="Full name on account"
                          className="bg-white border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="bank_name" className="text-sm font-medium text-gray-700">Bank Name</Label>
                        <Input
                          id="bank_name"
                          value={bankForm.bank_name}
                          onChange={(e) => setBankForm(prev => ({...prev, bank_name: e.target.value}))}
                          placeholder="e.g., Emirates NBD, ADCB, FAB"
                          className="bg-white border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="account_number" className="text-sm font-medium text-gray-700">Account Number</Label>
                          <Input
                            id="account_number"
                            type="password"
                            value={bankForm.account_number}
                            onChange={(e) => setBankForm(prev => ({...prev, account_number: e.target.value}))}
                            placeholder="Full account number"
                            className="bg-white border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="routing_number" className="text-sm font-medium text-gray-700">Routing Number / IBAN</Label>
                          <Input
                            id="routing_number"
                            value={bankForm.routing_number}
                            onChange={(e) => setBankForm(prev => ({...prev, routing_number: e.target.value}))}
                            placeholder="IBAN or routing number"
                            className="bg-white border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="account_type" className="text-sm font-medium text-gray-700">Account Type</Label>
                        <Select 
                          value={bankForm.account_type} 
                          onValueChange={(value) => setBankForm(prev => ({...prev, account_type: value}))}
                        >
                          <SelectTrigger className="bg-white border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200">
                            <SelectValue placeholder="Select account type" />
                          </SelectTrigger>
                          <SelectContent className="bg-white border shadow-lg">
                            <SelectItem value="checking">Checking</SelectItem>
                            <SelectItem value="savings">Savings</SelectItem>
                            <SelectItem value="current">Current</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="is_primary"
                          checked={bankForm.is_primary}
                          onChange={(e) => setBankForm(prev => ({...prev, is_primary: e.target.checked}))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <Label htmlFor="is_primary" className="text-sm text-gray-700">Set as primary account</Label>
                      </div>
                      </div>
                    </div>
                    <div className="flex justify-end space-x-2 pt-4 border-t bg-white p-4 rounded-b-lg">
                      <Button variant="outline" onClick={() => setShowAddBankModal(false)}>
                        Cancel
                      </Button>
                      <Button onClick={handleAddBankAccount} disabled={addingBank}>
                        {addingBank ? 'Adding...' : 'Add Account'}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Payout Settings</CardTitle>
              <CardDescription>Configure automatic payouts and preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Payout Frequency</label>
                <select className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md">
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Bi-weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Minimum Payout Amount</label>
                <input
                  type="number"
                  defaultValue="25"
                  className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="auto-payout" defaultChecked />
                <label htmlFor="auto-payout" className="text-sm">Enable automatic payouts</label>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
